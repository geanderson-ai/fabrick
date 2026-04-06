"""Fabrikk persistence — abstract checkpoint interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class CheckpointStore(ABC):
    """Abstract interface for pipeline checkpoint persistence.

    Stores execution state so pipelines can be resumed after failures,
    and provides an audit trail of all runs.
    """

    @abstractmethod
    def save_checkpoint(
        self,
        run_id: str,
        pipeline_name: str,
        state: str,
        data: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        """Save a checkpoint at the current pipeline state."""

    @abstractmethod
    def load_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        """Load the latest checkpoint for a run. Returns None if not found."""

    @abstractmethod
    def list_runs(
        self,
        pipeline_name: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List recent pipeline runs, optionally filtered by pipeline name."""

    @abstractmethod
    def save_step_result(
        self,
        run_id: str,
        step_name: str,
        status: str,
        data: dict[str, Any],
        elapsed_seconds: float,
    ) -> None:
        """Save the result of a single step execution."""

    @abstractmethod
    def get_step_results(self, run_id: str) -> list[dict[str, Any]]:
        """Get all step results for a run, in execution order."""

    def close(self) -> None:
        """Clean up resources. Override if needed."""
