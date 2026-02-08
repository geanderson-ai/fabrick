"""
Centralized Provider Configuration Registry
==========================================

Defines metadata for supported LLM providers including API endpoints,
default models, and environment variable mappings.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ProviderInfo:
    """Metadata for an LLM provider."""
    name: str
    base_url: Optional[str]
    auth_env_var: str
    default_model: str
    models: Dict[str, str] = field(default_factory=dict)


PROVIDERS = {
    "CLAUDE": ProviderInfo(
        name="Anthropic Claude",
        base_url=None,  # Uses SDK default
        auth_env_var="CLAUDE_CODE_OAUTH_TOKEN",
        default_model="claude-3-5-sonnet-20241022",
        models={
            "sonnet": "claude-3-5-sonnet-20241022",
            "haiku": "claude-3-5-haiku-20241022",
            "opus": "claude-3-opus-20240229",
        }
    ),
    "OPENROUTER": ProviderInfo(
        name="OpenRouter",
        base_url="https://openrouter.ai/api/v1",
        auth_env_var="OPENROUTER_API_KEY",
        default_model="moonshotai/kimi-k2.5",
        models={
            "sonnet": "anthropic/claude-3.5-sonnet",
            "haiku": "anthropic/claude-3.5-haiku",
            "gemini-flash": "google/gemini-2.0-flash-001",
            "gemini-pro": "google/gemini-pro-1.5",
            "kimi": "moonshotai/kimi-k2.5",
        }
    ),
    "GEMINI": ProviderInfo(
        name="Google Gemini",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        auth_env_var="GEMINI_API_KEY",
        default_model="google/gemini-2.0-flash-001",
        models={
            "flash": "google/gemini-2.0-flash-001",
            "pro": "google/gemini-pro-1.5",
        }
    )
}


def get_provider(provider_id: str) -> Optional[ProviderInfo]:
    """Get provider info by ID (case-insensitive)."""
    return PROVIDERS.get(provider_id.upper())
