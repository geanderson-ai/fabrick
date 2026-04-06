"""Fabrikk ExecutionContext — shared state across all pipeline steps."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class ExecutionContext:
    """Shared context passed to every step in a pipeline execution.

    Each step can read/write to `data` and `metadata`. The pipeline engine
    manages `state`, `state_history`, and checkpoint fields.
    """

    def __init__(
        self,
        pipeline_name: str,
        input: Any = None,
        *,
        provider: str = "ollama",
        model: str = "",
        project_dir: Path | None = None,
    ):
        # Identity
        self.pipeline_name = pipeline_name
        self.run_id = str(uuid.uuid4())

        # Input
        self.input = input

        # State (managed by PipelineMachine)
        self.state: str = "idle"
        self.state_history: list[str] = ["idle"]

        # Shared payload
        self.data: dict[str, Any] = {}
        self.metadata: dict[str, Any] = {}

        # Provider config
        self.provider = provider
        self.model = model

        # Paths
        self.project_dir = project_dir or Path.cwd()
        self.spec_dir: Path | None = None

        # Observability
        self.start_time = datetime.now(timezone.utc)
        self.step_timings: dict[str, float] = {}
        self.total_tokens: int = 0
        self.total_cost: float = 0.0

        # Checkpoints
        self.last_checkpoint: str | None = None
        self.checkpoint_data: dict[str, Any] = {}

    def transition_to(self, new_state: str) -> None:
        """Record a state transition."""
        self.state = new_state
        self.state_history.append(new_state)

    def record_step_timing(self, step_name: str, elapsed: float) -> None:
        """Record how long a step took in seconds."""
        self.step_timings[step_name] = elapsed

    def merge_data(self, new_data: dict[str, Any]) -> None:
        """Merge step output data into the shared context."""
        self.data.update(new_data)

    def merge_metadata(self, new_metadata: dict[str, Any]) -> None:
        """Merge step metadata into the shared context."""
        self.metadata.update(new_metadata)
