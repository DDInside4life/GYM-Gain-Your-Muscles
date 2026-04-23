from __future__ import annotations


class LLMError(Exception):
    """Base class for all LLM failures. Callers always treat it as 'fallback please'."""


class LLMDisabled(LLMError):
    """AI is not configured (no key / disabled flag)."""


class LLMTimeout(LLMError):
    pass


class LLMBadResponse(LLMError):
    """Response is not valid JSON or doesn't match expected schema."""
