from __future__ import annotations

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any

import httpx

from app.ai_agents.config import AISettings, ai_settings
from app.ai_agents.llm.errors import LLMBadResponse, LLMDisabled, LLMError, LLMTimeout

logger = logging.getLogger("app.ai.llm")


@dataclass(slots=True, frozen=True)
class LLMResult:
    data: dict[str, Any]
    raw: str
    model: str
    latency_ms: int
    prompt_tokens: int | None = None
    completion_tokens: int | None = None


class LLMClient:
    """Thin OpenAI-compatible JSON-mode client with retries + strict parsing.

    Works with OpenAI, Groq, Together, OpenRouter, local Ollama, etc.
    Never raises on transport/protocol errors from the caller's perspective —
    agents catch LLMError and fall back to deterministic logic.
    """

    def __init__(self, settings: AISettings | None = None) -> None:
        self.settings = settings or ai_settings

    def _headers(self) -> dict[str, str]:
        return {
            "authorization": f"Bearer {self.settings.api_key}",
            "content-type": "application/json",
        }

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        text = text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise LLMBadResponse(f"no JSON object in response: {text[:200]!r}")
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMBadResponse(f"malformed JSON: {exc}") from exc

    async def complete_json(
        self,
        *,
        system: str,
        user: str,
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> LLMResult:
        if not self.settings.is_ready:
            raise LLMDisabled("AI is disabled or API key missing")

        payload = {
            "model": self.settings.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": self.settings.temperature if temperature is None else temperature,
            "max_tokens": self.settings.max_tokens if max_tokens is None else max_tokens,
            "response_format": {"type": "json_object"},
            "stream": False,
        }

        url = f"{self.settings.base_url.rstrip('/')}/chat/completions"
        last_error: Exception | None = None
        start = time.monotonic()

        for attempt in range(self.settings.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.settings.timeout_s) as http:
                    res = await http.post(url, headers=self._headers(), json=payload)

                if res.status_code >= 500 or res.status_code == 429:
                    last_error = LLMError(f"upstream {res.status_code}: {res.text[:160]}")
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                if res.status_code >= 400:
                    raise LLMError(f"client error {res.status_code}: {res.text[:200]}")

                body = res.json()
                choices = body.get("choices") or []
                if not choices:
                    raise LLMBadResponse("no choices in response")
                content = (choices[0].get("message") or {}).get("content") or ""
                data = self._extract_json(content)
                usage = body.get("usage") or {}
                latency_ms = int((time.monotonic() - start) * 1000)
                return LLMResult(
                    data=data,
                    raw=content,
                    model=body.get("model") or self.settings.model,
                    latency_ms=latency_ms,
                    prompt_tokens=usage.get("prompt_tokens"),
                    completion_tokens=usage.get("completion_tokens"),
                )
            except httpx.TimeoutException as exc:
                last_error = LLMTimeout(str(exc))
                await asyncio.sleep(0.3 * (attempt + 1))
            except (httpx.HTTPError, LLMBadResponse) as exc:
                last_error = exc
                await asyncio.sleep(0.3 * (attempt + 1))

        logger.warning("LLM call failed after %s retries: %s", self.settings.max_retries, last_error)
        raise last_error if isinstance(last_error, LLMError) else LLMError(str(last_error))
