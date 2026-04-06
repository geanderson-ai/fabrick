"""Fabrikk local execution — synchronous and async pipeline runners."""

from __future__ import annotations

import asyncio
from typing import Any

import structlog

logger = structlog.get_logger("fabrikk.execution.local")


def run_sync(pipeline: Any, input: Any = None) -> Any:
    """Run a pipeline synchronously (blocking). This is the default."""
    return pipeline.run(input=input)


def run_async(pipeline: Any, input: Any = None) -> Any:
    """Run a pipeline in an asyncio event loop.

    If an event loop is already running, uses run_coroutine_threadsafe.
    Otherwise, creates a new loop with asyncio.run().
    """
    async def _run() -> Any:
        return pipeline.run(input=input)

    try:
        loop = asyncio.get_running_loop()
        # Already in an async context — schedule in the loop
        future = asyncio.run_coroutine_threadsafe(_run(), loop)
        return future.result()
    except RuntimeError:
        # No running loop — create one
        return asyncio.run(_run())
