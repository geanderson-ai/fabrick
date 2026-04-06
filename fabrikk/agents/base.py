"""Fabrikk AgentDecorator — base class for all agent-phase decorators."""

from __future__ import annotations

from typing import Any, Callable

from ..constants import STEP_MIDDLE
from ..decorators import StepInfo, _FABRIKK_ATTR


class AgentConfig:
    """Configuration attached to an agent decorator, resolved at runtime."""

    def __init__(
        self,
        agent_type: str,
        transitions_to: list[str] | None = None,
        **options: Any,
    ):
        self.agent_type = agent_type
        self.transitions_to = transitions_to
        self.options = options

    def get(self, key: str, default: Any = None) -> Any:
        return self.options.get(key, default)


# Attribute name for agent-specific config
_FABRIKK_AGENT_ATTR = "_fabrikk_agent"


def agent_decorator(
    agent_type: str,
    default_options: dict[str, Any] | None = None,
) -> Callable:
    """Factory that creates an agent-phase decorator.

    Each agent decorator (@spec, @plan, @execute, @review, @security) is built
    from this factory. It attaches both the standard StepInfo (so the Fabrick
    engine treats it as a @step) and an AgentConfig with agent-specific settings.

    Usage inside agent modules:

        spec = agent_decorator("spec", default_options={"mode": "interactive", "complexity": "auto"})

    Then users write:

        @spec(mode="task", transitions_to=["plan"])
        async def create_spec(context): ...
    """
    defaults = default_options or {}

    def wrapper(fn: Callable | None = None, /, **kwargs: Any) -> Callable:
        # Merge defaults with user-provided kwargs
        merged = {**defaults, **kwargs}
        transitions_to = merged.pop("transitions_to", None)

        def decorator(fn: Callable) -> Callable:
            # Attach standard StepInfo so Fabrick engine recognizes it as a step
            step_info = StepInfo(
                step_type=STEP_MIDDLE,
                name=fn.__name__,
                transitions_to=transitions_to,
                options=merged,
            )
            setattr(fn, _FABRIKK_ATTR, step_info)

            # Attach agent-specific config
            agent_config = AgentConfig(
                agent_type=agent_type,
                transitions_to=transitions_to,
                **merged,
            )
            setattr(fn, _FABRIKK_AGENT_ATTR, agent_config)

            return fn

        if fn is not None:
            # Used as @spec (no parentheses)
            return decorator(fn)
        # Used as @spec(...) with keyword args
        return decorator

    return wrapper


def get_agent_config(fn: Callable) -> AgentConfig | None:
    """Retrieve the AgentConfig attached to a decorated function, or None."""
    return getattr(fn, _FABRIKK_AGENT_ATTR, None)
