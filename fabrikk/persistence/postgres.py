"""Fabrikk PostgreSQL persistence — production checkpoint store.

Requires psycopg2 and a running PostgreSQL instance.
Connection string is read from FABRICK_DB_URL env var.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Any

from .base import CheckpointStore

DEFAULT_DB_URL = "postgresql://localhost:5432/fabrikk"


class PostgresCheckpointStore(CheckpointStore):
    """PostgreSQL-backed checkpoint store for production deployments.

    Uses psycopg2 for direct database access. Connection is established
    lazily on first operation.
    """

    def __init__(self, db_url: str | None = None):
        self.db_url = db_url or os.environ.get("FABRICK_DB_URL", DEFAULT_DB_URL)
        self._conn = None

    def _get_conn(self) -> Any:
        if self._conn is None or self._conn.closed:
            import psycopg2
            import psycopg2.extras

            self._conn = psycopg2.connect(self.db_url)
            self._conn.autocommit = False
            self._create_tables()
        return self._conn

    def _create_tables(self) -> None:
        conn = self._conn
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS checkpoints (
                    id SERIAL PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    pipeline_name TEXT NOT NULL,
                    state TEXT NOT NULL,
                    data JSONB NOT NULL DEFAULT '{}',
                    metadata JSONB NOT NULL DEFAULT '{}',
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE TABLE IF NOT EXISTS step_results (
                    id SERIAL PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    step_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    data JSONB NOT NULL DEFAULT '{}',
                    elapsed_seconds DOUBLE PRECISION NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                );

                CREATE INDEX IF NOT EXISTS idx_pg_checkpoints_run_id ON checkpoints(run_id);
                CREATE INDEX IF NOT EXISTS idx_pg_step_results_run_id ON step_results(run_id);
            """)
        conn.commit()

    def save_checkpoint(
        self,
        run_id: str,
        pipeline_name: str,
        state: str,
        data: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO checkpoints (run_id, pipeline_name, state, data, metadata) "
                "VALUES (%s, %s, %s, %s, %s)",
                (run_id, pipeline_name, state, json.dumps(data), json.dumps(metadata)),
            )
        conn.commit()

    def load_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT run_id, pipeline_name, state, data, metadata, created_at "
                "FROM checkpoints WHERE run_id = %s ORDER BY id DESC LIMIT 1",
                (run_id,),
            )
            row = cur.fetchone()

        if row is None:
            return None

        return {
            "run_id": row[0],
            "pipeline_name": row[1],
            "state": row[2],
            "data": row[3] if isinstance(row[3], dict) else json.loads(row[3]),
            "metadata": row[4] if isinstance(row[4], dict) else json.loads(row[4]),
            "created_at": str(row[5]),
        }

    def list_runs(
        self,
        pipeline_name: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        conn = self._get_conn()
        with conn.cursor() as cur:
            if pipeline_name:
                cur.execute(
                    "SELECT DISTINCT ON (run_id) run_id, pipeline_name, state, created_at "
                    "FROM checkpoints WHERE pipeline_name = %s "
                    "ORDER BY run_id, id DESC LIMIT %s",
                    (pipeline_name, limit),
                )
            else:
                cur.execute(
                    "SELECT DISTINCT ON (run_id) run_id, pipeline_name, state, created_at "
                    "FROM checkpoints ORDER BY run_id, id DESC LIMIT %s",
                    (limit,),
                )
            rows = cur.fetchall()

        return [
            {"run_id": r[0], "pipeline_name": r[1], "state": r[2], "created_at": str(r[3])}
            for r in rows
        ]

    def save_step_result(
        self,
        run_id: str,
        step_name: str,
        status: str,
        data: dict[str, Any],
        elapsed_seconds: float,
    ) -> None:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO step_results (run_id, step_name, status, data, elapsed_seconds) "
                "VALUES (%s, %s, %s, %s, %s)",
                (run_id, step_name, status, json.dumps(data), elapsed_seconds),
            )
        conn.commit()

    def get_step_results(self, run_id: str) -> list[dict[str, Any]]:
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT step_name, status, data, elapsed_seconds, created_at "
                "FROM step_results WHERE run_id = %s ORDER BY id ASC",
                (run_id,),
            )
            rows = cur.fetchall()

        return [
            {
                "step_name": r[0],
                "status": r[1],
                "data": r[2] if isinstance(r[2], dict) else json.loads(r[2]),
                "elapsed_seconds": r[3],
                "created_at": str(r[4]),
            }
            for r in rows
        ]

    def close(self) -> None:
        if self._conn and not self._conn.closed:
            self._conn.close()
