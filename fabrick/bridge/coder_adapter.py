"""Bridge: @execute ↔ Tear run_autonomous_agent().

Translates between the Fabrick StepResult contract and
Tear's coder agent interface.
"""

from __future__ import annotations

import json
from typing import Any

import structlog

from ..context import ExecutionContext
from .tear import get_bridge

logger = structlog.get_logger("fabrick.bridge.coder")


async def run_coder(
    context: ExecutionContext,
    *,
    max_retries: int = 3,
    max_iterations: int | None = None,
    parallel_agents: int = 1,
    auto_commit: bool = True,
) -> dict[str, Any]:
    """Execute Tear's autonomous coder agent and return a Fabrick StepResult dict.

    Args:
        context: The pipeline execution context.
        max_retries: Max retries per subtask.
        max_iterations: Max total iterations (None = unlimited).
        parallel_agents: Number of parallel agents (future use).
        auto_commit: Whether to auto-commit after each subtask.

    Returns:
        StepResult-compatible dict with completion stats.
    """
    bridge = get_bridge()
    run_autonomous_agent = bridge.get_coder()

    spec_dir = context.spec_dir or context.data.get("spec_dir")
    if spec_dir is None:
        return {
            "status": "failed",
            "data": {"error": "No spec_dir available. Run @spec and @plan first."},
        }

    try:
        await run_autonomous_agent(
            project_dir=context.project_dir,
            spec_dir=spec_dir,
            model=context.model or "sonnet",
            max_iterations=max_iterations,
        )
    except Exception as exc:
        logger.error("coder.error", error=str(exc))
        return {
            "status": "failed",
            "data": {"error": str(exc)},
        }

    # Read subtask completion status from implementation_plan.json
    completed = 0
    total = 0
    plan_path = spec_dir / "implementation_plan.json" if spec_dir else None

    if plan_path and plan_path.exists():
        try:
            plan_data = json.loads(plan_path.read_text())
            for phase in plan_data.get("phases", []):
                for subtask in phase.get("subtasks", []):
                    total += 1
                    if subtask.get("status") in ("completed", "done"):
                        completed += 1
        except (json.JSONDecodeError, OSError):
            pass

    all_complete = completed == total and total > 0

    return {
        "status": "success" if all_complete else "partial",
        "data": {
            "completed_subtasks": completed,
            "total_subtasks": total,
            "all_complete": all_complete,
        },
    }
