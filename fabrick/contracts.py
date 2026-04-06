"""Fabrikk contracts — standardized step return models."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class StepResult(BaseModel):
    """Standardized return contract for every pipeline step.

    Every decorated function must return a dict matching this schema.
    """

    status: str = Field(
        ...,
        description="Step outcome: 'success', 'failed', 'approved', 'rejected', etc.",
    )
    data: dict[str, Any] = Field(
        default_factory=dict,
        description="Payload produced by this step, merged into context.data.",
    )
    next_state: str | None = Field(
        default=None,
        description="Target state for the next transition. None for @finish steps.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional metadata (timing, tokens, cost, etc.).",
    )
