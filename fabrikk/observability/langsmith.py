"""Fabrikk LangSmith integration — pipeline and step tracing."""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Any, Generator

import structlog

logger = structlog.get_logger("fabrikk.observability.langsmith")

_langsmith_available = False
_langsmith_client = None

try:
    from langsmith import Client as LangSmithClient
    from langsmith.run_trees import RunTree
    _langsmith_available = True
except ImportError:
    LangSmithClient = None  # type: ignore
    RunTree = None  # type: ignore


def is_configured() -> bool:
    """Check if LangSmith is configured and available."""
    return (
        _langsmith_available
        and bool(os.environ.get("LANGSMITH_API_KEY"))
    )


def get_client() -> Any | None:
    """Get or create the LangSmith client singleton."""
    global _langsmith_client
    if not is_configured():
        return None
    if _langsmith_client is None:
        _langsmith_client = LangSmithClient()
    return _langsmith_client


@contextmanager
def trace_pipeline(
    pipeline_name: str,
    run_id: str,
    input_data: Any = None,
) -> Generator[Any | None, None, None]:
    """Context manager that traces an entire pipeline run in LangSmith.

    Yields a RunTree (or None if LangSmith isn't configured).
    """
    if not is_configured():
        yield None
        return

    project = os.environ.get("LANGSMITH_PROJECT", "fabrikk")

    run = RunTree(
        name=pipeline_name,
        run_type="chain",
        inputs={"input": str(input_data)} if input_data else {},
        project_name=project,
        id=run_id,
    )

    try:
        yield run
        run.end(outputs={"status": "completed"})
    except Exception as exc:
        run.end(error=str(exc))
        raise
    finally:
        run.post()


@contextmanager
def trace_step(
    step_name: str,
    parent_run: Any | None = None,
    inputs: dict[str, Any] | None = None,
) -> Generator[Any | None, None, None]:
    """Context manager that traces a single step within a pipeline.

    Yields a child RunTree (or None if LangSmith isn't configured).
    """
    if not is_configured() or parent_run is None:
        yield None
        return

    child = parent_run.create_child(
        name=step_name,
        run_type="chain",
        inputs=inputs or {},
    )

    try:
        yield child
    except Exception as exc:
        child.end(error=str(exc))
        child.post()
        raise


def record_step_result(
    run: Any | None,
    result: dict[str, Any],
    timing: float,
) -> None:
    """Record the output of a step trace."""
    if run is None:
        return
    run.end(
        outputs={
            "status": result.get("status"),
            "data": result.get("data"),
            "timing_seconds": timing,
        }
    )
    run.post()
