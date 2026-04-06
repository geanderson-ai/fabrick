"""Fabrikk SchedulerAdapter — abstract interface for pipeline scheduling."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Callable


class SchedulerAdapter(ABC):
    """Abstract interface for scheduling pipeline runs.

    Implementations handle the when — cron expressions, intervals, dates,
    or external triggers. The Fabrick engine handles the what (execution).
    """

    @abstractmethod
    def schedule(
        self,
        job_id: str,
        run_fn: Callable[..., Any],
        *,
        cron: str | None = None,
        interval_seconds: int | None = None,
        run_date: str | None = None,
        kwargs: dict[str, Any] | None = None,
    ) -> None:
        """Schedule a pipeline run.

        Exactly one of cron, interval_seconds, or run_date must be provided.

        Args:
            job_id: Unique identifier for this scheduled job.
            run_fn: The callable to execute (typically Fabrick.run).
            cron: Cron expression (e.g. "0 12 * * *").
            interval_seconds: Run every N seconds.
            run_date: ISO date string for a one-time run.
            kwargs: Keyword arguments to pass to run_fn.
        """

    @abstractmethod
    def cancel(self, job_id: str) -> bool:
        """Cancel a scheduled job. Returns True if found and cancelled."""

    @abstractmethod
    def list_jobs(self) -> list[dict[str, Any]]:
        """List all scheduled jobs with their metadata."""

    @abstractmethod
    def start(self) -> None:
        """Start the scheduler (begin processing jobs)."""

    @abstractmethod
    def shutdown(self) -> None:
        """Shutdown the scheduler gracefully."""
