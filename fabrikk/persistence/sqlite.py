"""Fabrikk SQLite persistence — lightweight checkpoint store for development."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .base import CheckpointStore

DEFAULT_DB_PATH = "fabrikk.db"


class SQLiteCheckpointStore(CheckpointStore):
    """SQLite-backed checkpoint store.

    Creates a local database file for storing pipeline run state,
    step results, and checkpoints. Ideal for development and
    single-machine deployments.
    """

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = str(db_path)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                pipeline_name TEXT NOT NULL,
                state TEXT NOT NULL,
                data TEXT NOT NULL,
                metadata TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS step_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id TEXT NOT NULL,
                step_name TEXT NOT NULL,
                status TEXT NOT NULL,
                data TEXT NOT NULL,
                elapsed_seconds REAL NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_checkpoints_run_id ON checkpoints(run_id);
            CREATE INDEX IF NOT EXISTS idx_step_results_run_id ON step_results(run_id);
        """)
        self._conn.commit()

    def save_checkpoint(
        self,
        run_id: str,
        pipeline_name: str,
        state: str,
        data: dict[str, Any],
        metadata: dict[str, Any],
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO checkpoints (run_id, pipeline_name, state, data, metadata, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, pipeline_name, state, json.dumps(data), json.dumps(metadata), now),
        )
        self._conn.commit()

    def load_checkpoint(self, run_id: str) -> dict[str, Any] | None:
        row = self._conn.execute(
            "SELECT * FROM checkpoints WHERE run_id = ? ORDER BY id DESC LIMIT 1",
            (run_id,),
        ).fetchone()

        if row is None:
            return None

        return {
            "run_id": row["run_id"],
            "pipeline_name": row["pipeline_name"],
            "state": row["state"],
            "data": json.loads(row["data"]),
            "metadata": json.loads(row["metadata"]),
            "created_at": row["created_at"],
        }

    def list_runs(
        self,
        pipeline_name: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        if pipeline_name:
            rows = self._conn.execute(
                "SELECT DISTINCT run_id, pipeline_name, state, created_at "
                "FROM checkpoints WHERE pipeline_name = ? "
                "ORDER BY id DESC LIMIT ?",
                (pipeline_name, limit),
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT DISTINCT run_id, pipeline_name, state, created_at "
                "FROM checkpoints ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def save_step_result(
        self,
        run_id: str,
        step_name: str,
        status: str,
        data: dict[str, Any],
        elapsed_seconds: float,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        self._conn.execute(
            "INSERT INTO step_results (run_id, step_name, status, data, elapsed_seconds, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (run_id, step_name, status, json.dumps(data), elapsed_seconds, now),
        )
        self._conn.commit()

    def get_step_results(self, run_id: str) -> list[dict[str, Any]]:
        rows = self._conn.execute(
            "SELECT * FROM step_results WHERE run_id = ? ORDER BY id ASC",
            (run_id,),
        ).fetchall()

        return [
            {
                "step_name": row["step_name"],
                "status": row["status"],
                "data": json.loads(row["data"]),
                "elapsed_seconds": row["elapsed_seconds"],
                "created_at": row["created_at"],
            }
            for row in rows
        ]

    def close(self) -> None:
        self._conn.close()
