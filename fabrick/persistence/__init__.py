"""Fabrikk Persistence — pluggable checkpoint stores."""

from __future__ import annotations

from typing import Any

from .base import CheckpointStore

# Lazy imports to avoid requiring all backends
_STORES: dict[str, str] = {
    "sqlite": "fabrick.persistence.sqlite:SQLiteCheckpointStore",
    "postgres": "fabrick.persistence.postgres:PostgresCheckpointStore",
    "redis": "fabrick.persistence.redis:RedisCheckpointStore",
}


def create_store(backend: str = "sqlite", **kwargs: Any) -> CheckpointStore:
    """Create a checkpoint store by backend name.

    Args:
        backend: "sqlite" | "postgres" | "redis"
        **kwargs: Backend-specific options (db_path, db_url, redis_url).
    """
    if backend not in _STORES:
        available = ", ".join(sorted(_STORES.keys()))
        raise ValueError(f"Unknown persistence backend '{backend}'. Available: {available}")

    module_path, class_name = _STORES[backend].rsplit(":", 1)
    import importlib
    mod = importlib.import_module(module_path)
    cls = getattr(mod, class_name)
    return cls(**kwargs)


__all__ = [
    "CheckpointStore",
    "create_store",
]
