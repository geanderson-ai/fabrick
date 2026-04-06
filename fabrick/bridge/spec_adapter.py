"""Bridge: @spec ↔ Tear SpecOrchestrator.

Translates between the Fabrick StepResult contract and
Tear's SpecOrchestrator.run() interface.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from ..context import ExecutionContext
from .tear import get_bridge


async def run_spec_pipeline(
    context: ExecutionContext,
    *,
    mode: str = "interactive",
    complexity: str = "auto",
) -> dict[str, Any]:
    """Execute Tear's spec pipeline and return a Fabrick StepResult dict.

    Args:
        context: The pipeline execution context.
        mode: "interactive" | "task" | "auto"
        complexity: "auto" | "simple" | "moderate" | "complex"

    Returns:
        StepResult-compatible dict with spec_dir, complexity, requirements.
    """
    bridge = get_bridge()
    SpecOrchestrator = bridge.get_spec_orchestrator()

    interactive = mode == "interactive"
    auto_approve = mode == "auto"
    complexity_override = complexity if complexity != "auto" else None

    orchestrator = SpecOrchestrator(
        project_dir=context.project_dir,
        task_description=context.input if isinstance(context.input, str) else None,
        model=context.model or "sonnet",
        complexity_override=complexity_override,
    )

    success = await orchestrator.run(
        interactive=interactive,
        auto_approve=auto_approve,
    )

    # Extract results from the orchestrator
    spec_dir = getattr(orchestrator, "spec_dir", None)
    detected_complexity = getattr(orchestrator, "complexity", complexity)

    if success and spec_dir:
        context.spec_dir = Path(spec_dir)

    return {
        "status": "success" if success else "failed",
        "data": {
            "spec_dir": str(spec_dir) if spec_dir else None,
            "complexity": detected_complexity,
        },
    }
