"""Fabrikk decorators — @start, @step, @finish."""

from __future__ import annotations

from typing import Any, Callable

from .constants import STEP_FINISH, STEP_MIDDLE, STEP_START

# Attribute name used to tag decorated functions
_FABRIKK_ATTR = "_fabrikk_step"


class StepInfo:
    """Metadata attached to a decorated function."""

    def __init__(
        self,
        step_type: str,
        name: str,
        transitions_to: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ):
        self.step_type = step_type
        self.name = name
        self.transitions_to = transitions_to
        self.options = options or {}


def _make_decorator(
    step_type: str,
    transitions_to: list[str] | None = None,
    **options: Any,
) -> Callable:
    """Internal factory that creates a decorator for the given step type."""

    def decorator(fn: Callable) -> Callable:
        info = StepInfo(
            step_type=step_type,
            name=fn.__name__,
            transitions_to=transitions_to,
            options=options,
        )
        setattr(fn, _FABRIKK_ATTR, info)
        return fn

    return decorator


def start(fn: Callable | None = None, /, **kwargs: Any) -> Callable:
    """Mark a function as the first step of the pipeline.

    Can be used bare (@start) or with arguments (@start(transitions_to=[...])).
    """
    if fn is not None:
        # Used as @start (no parentheses)
        info = StepInfo(step_type=STEP_START, name=fn.__name__)
        setattr(fn, _FABRIKK_ATTR, info)
        return fn
    # Used as @start(...) with keyword args
    return _make_decorator(STEP_START, **kwargs)


def step(fn: Callable | None = None, /, **kwargs: Any) -> Callable:
    """Mark a function as an intermediate step.

    Can be used bare (@step) or with arguments (@step(transitions_to=[...])).
    """
    if fn is not None:
        info = StepInfo(step_type=STEP_MIDDLE, name=fn.__name__)
        setattr(fn, _FABRIKK_ATTR, info)
        return fn
    return _make_decorator(STEP_MIDDLE, **kwargs)


def finish(fn: Callable | None = None, /, **kwargs: Any) -> Callable:
    """Mark a function as the final step (no next_state).

    Can be used bare (@finish) or with arguments (@finish(...)).
    """
    if fn is not None:
        info = StepInfo(step_type=STEP_FINISH, name=fn.__name__)
        setattr(fn, _FABRIKK_ATTR, info)
        return fn
    return _make_decorator(STEP_FINISH, **kwargs)


def get_step_info(fn: Callable) -> StepInfo | None:
    """Retrieve the StepInfo attached to a decorated function, or None."""
    return getattr(fn, _FABRIKK_ATTR, None)
