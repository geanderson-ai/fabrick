"""Fabrikk Execution — pluggable pipeline execution modes."""

from .background import run_in_background, run_in_thread, shutdown_executor
from .local import run_async, run_sync

__all__ = [
    "run_sync",
    "run_async",
    "run_in_background",
    "run_in_thread",
    "shutdown_executor",
]
