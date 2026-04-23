from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AISettings(BaseSettings):
    """LLM + agent runtime configuration.

    Reads `AI_*` env vars. Any provider that exposes an OpenAI-compatible
    `/chat/completions` endpoint works (OpenAI, Groq, Together, Ollama, ...).
    """
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    enabled: bool = Field(default=False, alias="AI_ENABLED")
    provider: str = Field(default="groq", alias="AI_PROVIDER")
    base_url: str = Field(default="https://api.groq.com/openai/v1", alias="AI_BASE_URL")
    api_key: str = Field(default="", alias="AI_API_KEY")
    model: str = Field(default="llama-3.1-70b-versatile", alias="AI_MODEL")

    timeout_s: float = Field(default=25.0, alias="AI_TIMEOUT_S", ge=1.0, le=120.0)
    max_retries: int = Field(default=2, alias="AI_MAX_RETRIES", ge=0, le=5)
    temperature: float = Field(default=0.3, alias="AI_TEMPERATURE", ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, alias="AI_MAX_TOKENS", ge=128, le=16384)

    @property
    def is_ready(self) -> bool:
        return bool(self.enabled and self.api_key and self.model)


@lru_cache
def get_ai_settings() -> AISettings:
    return AISettings()


ai_settings = get_ai_settings()
