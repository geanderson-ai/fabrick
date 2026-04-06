"""Claude provider — Anthropic API via Claude Agent SDK."""

from __future__ import annotations

import os

from .base import ProviderAdapter, ProviderConfig

CLAUDE_MODELS = {
    "sonnet": "claude-3-5-sonnet-20241022",
    "haiku": "claude-3-5-haiku-20241022",
    "opus": "claude-3-opus-20240229",
}

DEFAULT_MODEL = "claude-3-5-sonnet-20241022"


class ClaudeProvider(ProviderAdapter):
    provider_id = "CLAUDE"
    name = "Anthropic Claude"

    def resolve_config(self, model: str = "") -> ProviderConfig:
        resolved_model = self.resolve_model(model)
        return ProviderConfig(
            name=self.name,
            provider_id=self.provider_id,
            base_url=None,  # SDK default
            api_key=self._env("CLAUDE_CODE_OAUTH_TOKEN") or self._env("ANTHROPIC_API_KEY"),
            model=resolved_model,
            default_model=DEFAULT_MODEL,
            models=CLAUDE_MODELS,
            thinking_enabled=True,
        )

    def resolve_model(self, model: str) -> str:
        if not model:
            return DEFAULT_MODEL
        return CLAUDE_MODELS.get(model, model)

    def setup_env(self, config: ProviderConfig) -> None:
        os.environ["AUTO_BUILD_PROVIDER"] = "CLAUDE"
        if config.api_key:
            os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = config.api_key
