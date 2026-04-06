"""Bridge: @plan ↔ Tear run_followup_planner().

Translates between the Fabrick StepResult contract and
Tear's planner interface.
"""

from __future__ import annotations

import json
from typing import Any

from ..context import ExecutionContext
from .tear import get_bridge


async def run_planner(
    context: ExecutionContext,
    *,
    max_phases: int = 10,
    parallel_subtasks: bool = True,
) -> dict[str, Any]:
    """Execute Tear's planner and return a Fabrick StepResult dict.

    Args:
        context: The pipeline execution context.
        max_phases: Maximum number of phases to generate.
        parallel_subtasks: Whether to allow parallel subtask execution.

    Returns:
        StepResult-compatible dict with plan metadata.
    """
    bridge = get_bridge()
    run_followup_planner = bridge.get_planner()

    spec_dir = context.spec_dir or context.data.get("spec_dir")
    if spec_dir is None:
        return {
            "status": "failed",
            "data": {"error": "No spec_dir available. Run @spec first."},
        }

    success = await run_followup_planner(
        project_dir=context.project_dir,
        spec_dir=spec_dir,
        model=context.model or "sonnet",
    )

    # Try to read plan stats from implementation_plan.json
    total_phases = 0
    total_subtasks = 0
    plan_path = spec_dir / "implementation_plan.json" if spec_dir else None

    if plan_path and plan_path.exists():
        try:
            plan_data = json.loads(plan_path.read_text())
            phases = plan_data.get("phases", [])
            total_phases = min(len(phases), max_phases)
            total_subtasks = sum(
                len(p.get("subtasks", [])) for p in phases[:max_phases]
            )
        except (json.JSONDecodeError, OSError):
            pass

    return {
        "status": "success" if success else "failed",
        "data": {
            "plan_path": str(plan_path) if plan_path else None,
            "total_phases": total_phases,
            "total_subtasks": total_subtasks,
            "plan_ready": success,
        },
    }
