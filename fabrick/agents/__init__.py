"""Fabrick agent decorators."""

from .base import AgentConfig, get_agent_config
from .architecture import (
    architecture,
    ALL_SECTIONS,
    SECTION_META,
)
from .execute import execute
from .plan import plan
from .review import review
from .security import security
from .spec import spec

__all__ = [
    "spec",
    "plan",
    "execute",
    "review",
    "security",
    "architecture",
    "ALL_SECTIONS",
    "SECTION_META",
    "AgentConfig",
    "get_agent_config",
]
