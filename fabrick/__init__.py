"""Fabrikk — Declarative AI Pipeline Orchestrator."""

from .constants import OFF, ON
from .context import ExecutionContext
from .contracts import StepResult
from .core import Fabrick
from .decorators import finish, start, step
from .agents import architecture, execute, plan, review, security, spec
from .exceptions import (
    DuplicateStepError,
    FabrikkError,
    InvalidTransitionError,
    PipelineNotReadyError,
    StepFailedError,
    StepNotFoundError,
)

__all__ = [
    # Core
    "Fabrick",
    "ExecutionContext",
    "StepResult",
    # Decorators (base)
    "start",
    "step",
    "finish",
    # Decorators (agent)
    "spec",
    "plan",
    "execute",
    "review",
    "security",
    "architecture",
    # Constants
    "ON",
    "OFF",
    # Exceptions
    "FabrikkError",
    "InvalidTransitionError",
    "StepFailedError",
    "PipelineNotReadyError",
    "StepNotFoundError",
    "DuplicateStepError",
]
