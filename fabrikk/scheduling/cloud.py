"""Fabrikk Cloud Scheduler adapter — Google Cloud Scheduler integration.

Requires google-cloud-scheduler package and GCP credentials.
Creates HTTP-triggered Cloud Scheduler jobs that call a pipeline endpoint.
"""

from __future__ import annotations

import os
from typing import Any, Callable

import structlog

from .base import SchedulerAdapter

logger = structlog.get_logger("fabrikk.scheduling.cloud")


class CloudSchedulerAdapter(SchedulerAdapter):
    """Google Cloud Scheduler adapter.

    Creates Cloud Scheduler jobs that trigger pipeline runs via HTTP.
    The target URL should be a Cloud Run or Cloud Function endpoint
    that invokes Fabrick.run().
    """

    def __init__(
        self,
        project_id: str | None = None,
        location: str = "us-central1",
        target_url: str | None = None,
    ):
        self.project_id = project_id or os.environ.get("GCP_PROJECT_ID", "")
        self.location = location
        self.target_url = target_url or os.environ.get("FABRICK_TRIGGER_URL", "")
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            from google.cloud import scheduler_v1
            self._client = scheduler_v1.CloudSchedulerClient()
        return self._client

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
        if not cron:
            raise ValueError("Cloud Scheduler only supports cron expressions")

        if not self.target_url:
            raise ValueError("FABRICK_TRIGGER_URL must be set for Cloud Scheduler")

        import json
        from google.cloud import scheduler_v1

        client = self._get_client()
        parent = f"projects/{self.project_id}/locations/{self.location}"

        job = scheduler_v1.Job(
            name=f"{parent}/jobs/{job_id}",
            schedule=cron,
            time_zone="UTC",
            http_target=scheduler_v1.HttpTarget(
                uri=self.target_url,
                http_method=scheduler_v1.HttpMethod.POST,
                body=json.dumps(kwargs or {}).encode(),
                headers={"Content-Type": "application/json"},
            ),
        )

        try:
            client.create_job(parent=parent, job=job)
            logger.info("cloud_scheduler.created", job_id=job_id, cron=cron)
        except Exception as exc:
            if "already exists" in str(exc).lower():
                client.update_job(job=job)
                logger.info("cloud_scheduler.updated", job_id=job_id, cron=cron)
            else:
                raise

    def cancel(self, job_id: str) -> bool:
        client = self._get_client()
        name = f"projects/{self.project_id}/locations/{self.location}/jobs/{job_id}"
        try:
            client.delete_job(name=name)
            logger.info("cloud_scheduler.deleted", job_id=job_id)
            return True
        except Exception:
            return False

    def list_jobs(self) -> list[dict[str, Any]]:
        client = self._get_client()
        parent = f"projects/{self.project_id}/locations/{self.location}"
        jobs = client.list_jobs(parent=parent)
        return [
            {
                "id": job.name.split("/")[-1],
                "schedule": job.schedule,
                "state": job.state.name,
                "target": job.http_target.uri if job.http_target else None,
            }
            for job in jobs
        ]

    def start(self) -> None:
        # Cloud Scheduler is always running — no-op
        logger.info("cloud_scheduler.ready")

    def shutdown(self) -> None:
        # Cloud Scheduler is managed by GCP — no-op
        pass
