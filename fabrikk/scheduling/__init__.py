"""Fabrikk Scheduling — pluggable scheduler adapters."""

from __future__ import annotations

from typing import Any

from .base import SchedulerAdapter

_SCHEDULERS: dict[str, str] = {
    "apscheduler": "fabrikk.scheduling.apscheduler:APSchedulerAdapter",
    "cloud": "fabrikk.scheduling.cloud:CloudSchedulerAdapter",
}


def create_scheduler(backend: str = "apscheduler", **kwargs: Any) -> SchedulerAdapter:
    """Create a scheduler by backend name.

    Args:
        backend: "apscheduler" | "cloud"
        **kwargs: Backend-specific options.
    """
    if backend not in _SCHEDULERS:
        available = ", ".join(sorted(_SCHEDULERS.keys()))
        raise ValueError(f"Unknown scheduler backend '{backend}'. Available: {available}")

    module_path, class_name = _SCHEDULERS[backend].rsplit(":", 1)
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls(**kwargs)


__all__ = [
    "SchedulerAdapter",
    "create_scheduler",
]
