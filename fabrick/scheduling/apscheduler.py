"""Fabrikk APScheduler adapter — local cron, interval, and date scheduling."""

from __future__ import annotations

from typing import Any, Callable

import structlog
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger

from .base import SchedulerAdapter

logger = structlog.get_logger("fabrick.scheduling")


class APSchedulerAdapter(SchedulerAdapter):
    """Local scheduler backed by APScheduler.

    Supports cron expressions, fixed intervals, and one-time date triggers.
    Runs jobs in a background thread.
    """

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler()
        self._started = False

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
        trigger = self._resolve_trigger(cron, interval_seconds, run_date)
        self._scheduler.add_job(
            run_fn,
            trigger=trigger,
            id=job_id,
            replace_existing=True,
            kwargs=kwargs or {},
        )
        logger.info("scheduler.job_added", job_id=job_id, trigger_type=type(trigger).__name__)

    def cancel(self, job_id: str) -> bool:
        try:
            self._scheduler.remove_job(job_id)
            logger.info("scheduler.job_cancelled", job_id=job_id)
            return True
        except Exception:
            return False

    def list_jobs(self) -> list[dict[str, Any]]:
        jobs = self._scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name,
                "trigger": str(job.trigger),
                "next_run": str(job.next_run_time) if job.next_run_time else None,
            }
            for job in jobs
        ]

    def start(self) -> None:
        if not self._started:
            self._scheduler.start()
            self._started = True
            logger.info("scheduler.started")

    def shutdown(self) -> None:
        if self._started:
            self._scheduler.shutdown(wait=True)
            self._started = False
            logger.info("scheduler.shutdown")

    @staticmethod
    def _resolve_trigger(
        cron: str | None,
        interval_seconds: int | None,
        run_date: str | None,
    ) -> CronTrigger | IntervalTrigger | DateTrigger:
        """Resolve scheduling parameters into an APScheduler trigger."""
        if cron:
            return CronTrigger.from_crontab(cron)
        if interval_seconds:
            return IntervalTrigger(seconds=interval_seconds)
        if run_date:
            return DateTrigger(run_date=run_date)
        raise ValueError("One of cron, interval_seconds, or run_date must be provided")
