"""Fabrikk Celery execution — distributed pipeline runs.

Requires celery and a message broker (Redis or RabbitMQ).
"""

from __future__ import annotations

import os
from typing import Any

import structlog

logger = structlog.get_logger("fabrick.execution.celery")

DEFAULT_BROKER = "redis://localhost:6379/0"
DEFAULT_BACKEND = "redis://localhost:6379/1"

# Celery app instance (created lazily)
_celery_app = None


def get_celery_app() -> Any:
    """Get or create the Celery application instance."""
    global _celery_app
    if _celery_app is None:
        from celery import Celery

        broker = os.environ.get("CELERY_BROKER_URL", DEFAULT_BROKER)
        backend = os.environ.get("CELERY_RESULT_BACKEND", DEFAULT_BACKEND)

        _celery_app = Celery(
            "fabrick",
            broker=broker,
            backend=backend,
        )
        _celery_app.conf.update(
            task_serializer="json",
            accept_content=["json"],
            result_serializer="json",
            timezone="UTC",
            task_track_started=True,
            task_time_limit=3600,  # 1 hour max
        )
    return _celery_app


def create_pipeline_task(
    pipeline_module: str,
    pipeline_attr: str,
) -> Any:
    """Create a Celery task for a pipeline.

    Args:
        pipeline_module: Dotted module path (e.g. "app").
        pipeline_attr: Attribute name of the Fabrick instance.

    Returns:
        A Celery task that can be called with .delay() or .apply_async().
    """
    app = get_celery_app()

    @app.task(name=f"fabrick.run.{pipeline_module}.{pipeline_attr}", bind=True)
    def run_pipeline_task(self: Any, input: Any = None) -> dict[str, Any]:
        import importlib

        mod = importlib.import_module(pipeline_module)
        pipeline = getattr(mod, pipeline_attr)

        logger.info("celery.task.start", pipeline=pipeline.name, task_id=self.request.id)
        context = pipeline.run(input=input)
        logger.info("celery.task.complete", pipeline=pipeline.name, state=context.state)

        return {
            "run_id": context.run_id,
            "state": context.state,
            "data": context.data,
        }

    return run_pipeline_task


def send_pipeline(
    pipeline_module: str,
    pipeline_attr: str,
    input: Any = None,
    queue: str = "default",
) -> Any:
    """Send a pipeline run to Celery as an async task.

    Returns an AsyncResult for tracking the task.
    """
    task = create_pipeline_task(pipeline_module, pipeline_attr)
    result = task.apply_async(args=[input], queue=queue)
    logger.info("celery.sent", task_id=result.id, queue=queue)
    return result
