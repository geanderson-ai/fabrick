"""Fabrikk Redis persistence — fast checkpoint store with cache and locks.

Requires redis-py and a running Redis instance.
Connection URL is read from FABRICK_REDIS_URL env var.
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

from .base import CheckpointStore

DEFAULT_REDIS_URL = "redis://localhost:6379/0"
KEY_PREFIX = "fabrikk:"
CHECKPOINT_TTL = 86400 * 7  # 7 days


class RedisCheckpointStore(CheckpointStore):
    """Redis-backed checkpoint store.

    Uses Redis hashes and sorted sets for fast checkpoint lookup
    and run listing. Ideal for distributed deployments where
    multiple workers share state.
    """

    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or os.environ.get("FABRICK_REDIS_URL", DEFAULT_REDIS_URL)
        self._client = None

    def _get_client(self) -> Any:
        if self._client is None:
            import redis

            self._client = redis.from_url(self.redis_url, decode_responses=True)
        return self._client

    def _key(self, *parts: str) -> str:
        return KEY_PREFIX + ":".join(parts)

    def save_checkpoint(
        self,
        run_id: str,
        pipeline_name: str,
        state: str,
        data: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        client = self._get_client()
        checkpoint = {
            "run_id": run_id,
            "pipeline_name": pipeline_name,
            "state": state,
            "data": json.dumps(data),
            "metadata": json.dumps(metadata),
            "created_at": time.time(),
        }

        # Store checkpoint as hash
        key = self._key("checkpoint", run_id)
        client.hset(key, mapping=checkpoint)
        client.expire(key, CHECKPOINT_TTL)

        # Add to run index (sorted set by timestamp)
        index_key = self._key("runs", pipeline_name) if pipeline_name else self._key("runs", "_all")
        client.zadd(index_key, {run_id: time.time()})
        client.zadd(self._key("runs", "_all"), {run_id: time.time()})

    def load_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        client = self._get_client()
        key = self._key("checkpoint", run_id)
        raw = client.hgetall(key)

        if not raw:
            return None

        return {
            "run_id": raw["run_id"],
            "pipeline_name": raw["pipeline_name"],
            "state": raw["state"],
            "data": json.loads(raw["data"]),
            "metadata": json.loads(raw["metadata"]),
            "created_at": raw["created_at"],
        }

    def list_runs(
        self,
        pipeline_name: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        client = self._get_client()
        index_key = (
            self._key("runs", pipeline_name) if pipeline_name
            else self._key("runs", "_all")
        )

        # Get most recent run_ids
        run_ids = client.zrevrange(index_key, 0, limit - 1)

        results = []
        for run_id in run_ids:
            checkpoint = self.load_checkpoint(run_id)
            if checkpoint:
                results.append(checkpoint)

        return results

    def save_step_result(
        self,
        run_id: str,
        step_name: str,
        status: str,
        data: dict[str, Any],
        elapsed_seconds: float,
    ) -> None:
        client = self._get_client()
        result = {
            "step_name": step_name,
            "status": status,
            "data": json.dumps(data),
            "elapsed_seconds": elapsed_seconds,
            "created_at": time.time(),
        }

        key = self._key("steps", run_id)
        client.rpush(key, json.dumps(result))
        client.expire(key, CHECKPOINT_TTL)

    def get_step_results(self, run_id: str) -> list[dict[str, Any]]:
        client = self._get_client()
        key = self._key("steps", run_id)
        raw_list = client.lrange(key, 0, -1)

        results = []
        for raw in raw_list:
            item = json.loads(raw)
            item["data"] = json.loads(item["data"]) if isinstance(item["data"], str) else item["data"]
            results.append(item)

        return results

    def close(self) -> None:
        if self._client:
            self._client.close()
