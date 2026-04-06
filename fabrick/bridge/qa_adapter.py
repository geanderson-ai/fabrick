"""Bridge: @review ↔ Tear run_qa_validation_loop().

Translates between the Fabrick StepResult contract and
Tear's QA loop interface.
"""

from __future__ import annotations

from typing import Any

import structlog

from ..context import ExecutionContext
from .tear import get_bridge

logger = structlog.get_logger("fabrick.bridge.qa")


async def run_qa_loop(
    context: ExecutionContext,
    *,
    max_iterations: int = 50,
    auto_fix: bool = True,
    escalate_after: int = 3,
) -> dict[str, Any]:
    """Execute Tear's QA validation loop and return a Fabrick StepResult dict.

    Args:
        context: The pipeline execution context.
        max_iterations: Maximum review-fix cycles.
        auto_fix: Whether to automatically run fixer on rejection.
        escalate_after: Number of recurring issues before escalation.

    Returns:
        StepResult-compatible dict with QA results.
    """
    bridge = get_bridge()
    run_qa_validation_loop = bridge.get_qa_loop()

    spec_dir = context.spec_dir or context.data.get("spec_dir")
    if spec_dir is None:
        return {
            "status": "failed",
            "data": {"error": "No spec_dir available."},
        }

    try:
        approved = await run_qa_validation_loop(
            project_dir=context.project_dir,
            spec_dir=spec_dir,
            model=context.model or "sonnet",
        )
    except Exception as exc:
        logger.error("qa.error", error=str(exc))
        return {
            "status": "failed",
            "data": {"error": str(exc)},
        }

    # Determine final status
    if approved:
        status = "approved"
    else:
        status = "rejected"

    return {
        "status": status,
        "data": {
            "approved": approved,
            "qa_report_path": str(spec_dir / "qa_report.md") if spec_dir else None,
        },
    }
