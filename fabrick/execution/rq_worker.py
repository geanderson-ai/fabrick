"""Fabrikk RQ execution — pipeline runs via Redis Queue.

Requires rq and redis packages, plus a running Redis instance.
"""

from __future__ import annotations

import os
from typing import Any

import structlog

logger = structlog.get_logger("fabrick.execution.rq")

DEFAULT_QUEUE = "fabrick"
DEFAULT_REDIS_URL = "redis://localhost:6379/0"


def enqueue_pipeline(
    pipeline_module: str,
    pipeline_attr: str,
    input: Any = None,
    queue_name: str = DEFAULT_QUEUE,
    redis_url: str | None = None,
) -> Any:
    """Enqueue a pipeline run as an RQ job.

    Since RQ serializes jobs, the pipeline must be importable by module path.

    Args:
        pipeline_module: Dotted module path (e.g. "app").
        pipeline_attr: Attribute name of the Fabrick instance (e.g. "workflow").
        input: Input data for the pipeline.
        queue_name: RQ queue name.
        redis_url: Redis connection URL.

    Returns:
        The RQ Job object.
    """
    from redis import Redis
    from rq import Queue

    url = redis_url or os.environ.get("FABRICK_REDIS_URL", DEFAULT_REDIS_URL)
    conn = Redis.from_url(url)
    queue = Queue(queue_name, connection=conn)

    job = queue.enqueue(
        _run_pipeline_job,
        pipeline_module,
        pipeline_attr,
        input,
        job_timeout="1h",
    )

    logger.info("rq.enqueued", job_id=job.id, queue=queue_name)
    return job


def _run_pipeline_job(
    pipeline_module: str,
    pipeline_attr: str,
    input: Any = None,
) -> dict[str, Any]:
    """RQ worker entry point — imports and runs the pipeline."""
    import importlib

    mod = importlib.import_module(pipeline_module)
    pipeline = getattr(mod, pipeline_attr)

    logger.info("rq.job.start", pipeline=pipeline.name)
    context = pipeline.run(input=input)
    logger.info("rq.job.complete", pipeline=pipeline.name, state=context.state)

    return {
        "run_id": context.run_id,
        "state": context.state,
        "data": context.data,
    }
