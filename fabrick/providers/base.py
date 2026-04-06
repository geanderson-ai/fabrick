"""Fabrikk ProviderAdapter — abstract interface for LLM providers."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ProviderConfig:
    """Resolved configuration for a specific provider."""

    name: str
    provider_id: str
    base_url: str | None = None
    api_key: str | None = None
    model: str = ""
    default_model: str = ""
    models: dict[str, str] = field(default_factory=dict)
    thinking_enabled: bool = True
    max_thinking_tokens: int | None = None
    extra: dict[str, Any] = field(default_factory=dict)


class ProviderAdapter(ABC):
    """Abstract base for all LLM provider adapters.

    Each provider implements:
    - resolve_config(): reads env vars and returns a ProviderConfig
    - resolve_model(): maps shorthand names to full model IDs
    - setup_env(): sets any environment variables needed before calling Tear
    """

    provider_id: str
    name: str

    @abstractmethod
    def resolve_config(self, model: str = "") -> ProviderConfig:
        """Build a fully resolved ProviderConfig from env vars and defaults."""

    @abstractmethod
    def resolve_model(self, model: str) -> str:
        """Map a model shorthand (e.g. 'sonnet') to a full model ID."""

    @abstractmethod
    def setup_env(self, config: ProviderConfig) -> None:
        """Set environment variables needed by Tear's client layer."""

    def _env(self, key: str, default: str = "") -> str:
        """Read an environment variable."""
        return os.environ.get(key, default)
