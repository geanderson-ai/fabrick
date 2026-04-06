"""Fabrikk Providers — pluggable LLM provider adapters."""

from __future__ import annotations

import os

from .base import ProviderAdapter, ProviderConfig
from .claude import ClaudeProvider
from .gemini import GeminiProvider
from .ollama import OllamaProvider
from .openrouter import OpenRouterProvider

# Registry of all available providers
_PROVIDERS: dict[str, ProviderAdapter] = {
    "CLAUDE": ClaudeProvider(),
    "OPENROUTER": OpenRouterProvider(),
    "GEMINI": GeminiProvider(),
    "OLLAMA": OllamaProvider(),
}


def resolve_provider(provider: str = "") -> ProviderAdapter:
    """Resolve a provider by name (case-insensitive).

    Resolution chain:
        explicit arg > AUTO_BUILD_PROVIDER env > "OLLAMA" default
    """
    provider_id = (
        provider.upper()
        or os.environ.get("AUTO_BUILD_PROVIDER", "OLLAMA").upper()
    )

    adapter = _PROVIDERS.get(provider_id)
    if adapter is None:
        available = ", ".join(sorted(_PROVIDERS.keys()))
        raise ValueError(
            f"Unknown provider '{provider_id}'. Available: {available}"
        )
    return adapter


def get_provider_config(provider: str = "", model: str = "") -> ProviderConfig:
    """Convenience: resolve provider and build its config in one call."""
    adapter = resolve_provider(provider)
    return adapter.resolve_config(model)


__all__ = [
    "ProviderAdapter",
    "ProviderConfig",
    "ClaudeProvider",
    "OpenRouterProvider",
    "GeminiProvider",
    "OllamaProvider",
    "resolve_provider",
    "get_provider_config",
]
