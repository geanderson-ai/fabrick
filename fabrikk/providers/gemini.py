"""Gemini provider — Google Generative AI via OpenAI-compatible endpoint."""

from __future__ import annotations

import os

from .base import ProviderAdapter, ProviderConfig

GEMINI_MODELS = {
    "flash": "google/gemini-2.0-flash-001",
    "pro": "google/gemini-pro-1.5",
}

DEFAULT_MODEL = "google/gemini-2.0-flash-001"
BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"


class GeminiProvider(ProviderAdapter):
    provider_id = "GEMINI"
    name = "Google Gemini"

    def resolve_config(self, model: str = "") -> ProviderConfig:
        resolved_model = self.resolve_model(model)
        return ProviderConfig(
            name=self.name,
            provider_id=self.provider_id,
            base_url=BASE_URL,
            api_key=self._env("GEMINI_API_KEY"),
            model=resolved_model,
            default_model=DEFAULT_MODEL,
            models=GEMINI_MODELS,
            thinking_enabled=True,
        )

    def resolve_model(self, model: str) -> str:
        if not model:
            return DEFAULT_MODEL
        return GEMINI_MODELS.get(model, model)

    def setup_env(self, config: ProviderConfig) -> None:
        os.environ["AUTO_BUILD_PROVIDER"] = "GEMINI"
        os.environ["ANTHROPIC_BASE_URL"] = BASE_URL
        if config.api_key:
            os.environ["GEMINI_API_KEY"] = config.api_key
