"""LLM client — unified interface for OpenAI-compatible APIs."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


@dataclass
class LLMConfig:
    api_key: str
    base_url: str
    primary_model: str
    fast_model: str
    temperature: float
    max_tokens: int
    timeout: int

    @classmethod
    def from_env(cls) -> "LLMConfig":
        return cls(
            api_key=os.getenv("LLM_API_KEY", ""),
            base_url=os.getenv("LLM_BASE_URL", "https://api.openai.com/v1"),
            primary_model=os.getenv("LLM_MODEL_PRIMARY", "gpt-4o"),
            fast_model=os.getenv("LLM_MODEL_FAST", "gpt-4o-mini"),
            temperature=float(os.getenv("LLM_TEMPERATURE", "0.7")),
            max_tokens=int(os.getenv("LLM_MAX_TOKENS", "4096")),
            timeout=int(os.getenv("LLM_TIMEOUT", "120")),
        )


class LLMClient:
    """Unified LLM client supporting OpenAI-compatible APIs."""

    def __init__(self, config: LLMConfig | None = None) -> None:
        self.config = config or LLMConfig.from_env()
        if not self.config.api_key:
            raise ValueError(
                "LLM_API_KEY not set. Please configure .env file. "
                "See .env.example for reference."
            )
        self._client = OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            timeout=self.config.timeout,
        )
        self._cache: dict[str, str] = {}

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str | None = None,
        temperature: float | None = None,
        max_tokens: int | None = None,
        use_cache: bool = False,
    ) -> str:
        model = model or self.config.primary_model
        temperature = temperature if temperature is not None else self.config.temperature
        max_tokens = max_tokens or self.config.max_tokens

        cache_key = ""
        if use_cache:
            cache_key = f"{model}:{temperature}:{str(messages)}"
            if cache_key in self._cache:
                return self._cache[cache_key]

        response = self._client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        content = response.choices[0].message.content or ""

        if use_cache:
            self._cache[cache_key] = content

        return content

    def chat_fast(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> str:
        return self.chat(
            messages,
            model=self.config.fast_model,
            temperature=temperature if temperature is not None else 0.5,
            max_tokens=2048,
        )

    def chat_primary(
        self,
        messages: list[dict[str, str]],
        temperature: float | None = None,
    ) -> str:
        return self.chat(
            messages,
            model=self.config.primary_model,
            temperature=temperature,
        )


def get_client() -> LLMClient:
    """Get a singleton LLM client instance."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client


_client: Optional[LLMClient] = None
