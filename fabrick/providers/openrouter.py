"""OpenRouter provider — multi-model API via ANTHROPIC_BASE_URL."""

from __future__ import annotations

import os

from .base import ProviderAdapter, ProviderConfig

OPENROUTER_MODELS = {
    "sonnet": "anthropic/claude-3.5-sonnet",
    "haiku": "anthropic/claude-3.5-haiku",
    "gemini-flash": "google/gemini-2.0-flash-001",
    "gemini-pro": "google/gemini-pro-1.5",
    "kimi": "moonshotai/kimi-k2.5",
}

DEFAULT_MODEL = "moonshotai/kimi-k2.5"
BASE_URL = "https://openrouter.ai/api/v1"


class OpenRouterProvider(ProviderAdapter):
    provider_id = "OPENROUTER"
    name = "OpenRouter"

    def resolve_config(self, model: str = "") -> ProviderConfig:
        resolved_model = self.resolve_model(model)
        return ProviderConfig(
            name=self.name,
            provider_id=self.provider_id,
            base_url=BASE_URL,
            api_key=self._env("OPENROUTER_API_KEY"),
            model=resolved_model,
            default_model=DEFAULT_MODEL,
            models=OPENROUTER_MODELS,
            thinking_enabled=True,
        )

    def resolve_model(self, model: str) -> str:
        if not model:
            return DEFAULT_MODEL
        return OPENROUTER_MODELS.get(model, model)

    def setup_env(self, config: ProviderConfig) -> None:
        os.environ["AUTO_BUILD_PROVIDER"] = "OPENROUTER"
        os.environ["ANTHROPIC_BASE_URL"] = BASE_URL
        if config.api_key:
            os.environ["OPENROUTER_API_KEY"] = config.api_key
