"""Ollama provider — local LLM via Ollama's OpenAI-compatible endpoint.

Automatically configures ANTHROPIC_BASE_URL, dummy API key,
and disables thinking tokens (not supported by local models).
"""

from __future__ import annotations

import os

from .base import ProviderAdapter, ProviderConfig

OLLAMA_MODELS = {
    "qwen2.5-coder": "qwen2.5-coder:7b",
    "qwen2.5-coder:7b": "qwen2.5-coder:7b",
    "qwen3": "qwen3:8b",
    "qwen3:14b": "qwen3:14b",
    "qwen3:32b": "qwen3:32b",
    "llama3.1": "llama3.1:8b",
    "llama3.1:70b": "llama3.1:70b",
    "codellama": "codellama:13b",
    "deepseek-coder-v2": "deepseek-coder-v2:16b",
    "mistral": "mistral:7b",
}

DEFAULT_MODEL = "qwen2.5-coder:7b"
DEFAULT_OLLAMA_URL = "http://localhost:11434"


class OllamaProvider(ProviderAdapter):
    provider_id = "OLLAMA"
    name = "Ollama (Local)"

    def resolve_config(self, model: str = "") -> ProviderConfig:
        resolved_model = self.resolve_model(model)
        ollama_url = self._env("OLLAMA_URL", DEFAULT_OLLAMA_URL).rstrip("/")
        base_url = f"{ollama_url}/v1"

        return ProviderConfig(
            name=self.name,
            provider_id=self.provider_id,
            base_url=base_url,
            api_key="ollama",  # Dummy key — Ollama doesn't need auth
            model=resolved_model,
            default_model=DEFAULT_MODEL,
            models=OLLAMA_MODELS,
            thinking_enabled=False,  # Local models don't support thinking
            max_thinking_tokens=None,
            extra={"ollama_url": ollama_url},
        )

    def resolve_model(self, model: str) -> str:
        # Priority: explicit model > OLLAMA_MODEL env > default
        if not model:
            return self._env("OLLAMA_MODEL", DEFAULT_MODEL)
        return OLLAMA_MODELS.get(model, model)

    def setup_env(self, config: ProviderConfig) -> None:
        os.environ["AUTO_BUILD_PROVIDER"] = "OLLAMA"
        os.environ["ANTHROPIC_BASE_URL"] = config.base_url or f"{DEFAULT_OLLAMA_URL}/v1"
        os.environ["ANTHROPIC_API_KEY"] = "ollama"  # Dummy
        os.environ["OLLAMA_MODEL"] = config.model
        ollama_url = config.extra.get("ollama_url", DEFAULT_OLLAMA_URL)
        os.environ["OLLAMA_URL"] = ollama_url
