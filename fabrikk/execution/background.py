"""Fabrikk background execution — run pipelines in threads or asyncio tasks."""

from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from typing import Any

import structlog

logger = structlog.get_logger("fabrikk.execution.background")

# Shared thread pool for background execution
_executor: ThreadPoolExecutor | None = None


def _get_executor() -> ThreadPoolExecutor:
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="fabrikk-bg")
    return _executor


def run_in_background(pipeline: Any, input: Any = None) -> Future:
    """Submit a pipeline run to a background thread pool.

    Returns a Future that can be used to get the result or check status.

    Usage:
        future = run_in_background(pipeline, input="data")
        # ... do other work ...
        context = future.result()  # blocks until done
    """
    executor = _get_executor()

    def _run() -> Any:
        logger.info("background.start", pipeline=pipeline.name, thread=threading.current_thread().name)
        result = pipeline.run(input=input)
        logger.info("background.complete", pipeline=pipeline.name, state=result.state)
        return result

    return executor.submit(_run)


def run_in_thread(pipeline: Any, input: Any = None) -> threading.Thread:
    """Run a pipeline in a dedicated daemon thread.

    Returns the Thread object. Results must be retrieved through
    persistence or context — the thread return value is not accessible.

    Usage:
        thread = run_in_thread(pipeline, input="data")
        thread.join()  # optional: wait for completion
    """
    def _run() -> None:
        logger.info("thread.start", pipeline=pipeline.name)
        pipeline.run(input=input)
        logger.info("thread.complete", pipeline=pipeline.name)

    thread = threading.Thread(
        target=_run,
        name=f"fabrikk-{pipeline.name}",
        daemon=True,
    )
    thread.start()
    return thread


def shutdown_executor() -> None:
    """Shutdown the background thread pool gracefully."""
    global _executor
    if _executor is not None:
        _executor.shutdown(wait=True)
        _executor = None
