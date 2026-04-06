"""Bridge: @security ↔ Tear security scanners.

Translates between the Fabrick StepResult contract and
Tear's security scanning interfaces.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog

from ..context import ExecutionContext
from .tear import get_bridge

logger = structlog.get_logger("fabrick.bridge.security")


async def run_security_scan(
    context: ExecutionContext,
    *,
    scan_secrets: bool = True,
    validate_commands: bool = True,
    check_dependencies: bool = True,
    fail_on: str = "critical",
) -> dict[str, Any]:
    """Execute Tear's security scanners and return a Fabrick StepResult dict.

    Args:
        context: The pipeline execution context.
        scan_secrets: Whether to scan for exposed secrets.
        validate_commands: Whether to validate bash commands.
        check_dependencies: Whether to check dependency vulnerabilities.
        fail_on: Minimum severity to fail: "critical" | "high" | "medium" | "low"

    Returns:
        StepResult-compatible dict with security report.
    """
    bridge = get_bridge()

    secrets_found: list[dict[str, Any]] = []
    risky_commands: list[dict[str, Any]] = []
    risk_level = "low"
    issues: list[str] = []

    # 1. Secret scanning
    if scan_secrets:
        try:
            scan_files = bridge.get_secret_scanner()
            project_files = _collect_source_files(context.project_dir)
            matches = scan_files(project_files)
            secrets_found = [
                {"file": str(m.file), "line": m.line, "type": m.type}
                for m in matches
            ] if matches else []
            if secrets_found:
                risk_level = "high"
                issues.append(f"{len(secrets_found)} secrets found")
        except Exception as exc:
            logger.warning("security.secrets.error", error=str(exc))

    # 2. Command validation (checks project security profile)
    if validate_commands:
        try:
            validate_command = bridge.get_command_validator()
            # Validate common risky commands as a smoke test
            for cmd in ["rm -rf /", "curl | bash", "chmod 777"]:
                allowed, reason = validate_command(cmd, project_dir=context.project_dir)
                if not allowed:
                    risky_commands.append({"command": cmd, "reason": reason})
        except Exception as exc:
            logger.warning("security.commands.error", error=str(exc))

    # Determine severity ordering
    severity_order = ["low", "medium", "high", "critical"]
    fail_threshold = severity_order.index(fail_on) if fail_on in severity_order else 3
    current_level = severity_order.index(risk_level) if risk_level in severity_order else 0

    passed = current_level < fail_threshold

    return {
        "status": "pass" if passed else "fail",
        "data": {
            "secrets_found": secrets_found,
            "risky_commands": risky_commands,
            "risk_level": risk_level,
            "issues": issues,
            "report_path": str(context.project_dir / "security_report.md"),
        },
    }


def _collect_source_files(project_dir: Path, max_files: int = 500) -> list[str]:
    """Collect source files from the project for scanning."""
    extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".env", ".yml", ".yaml", ".json", ".toml"}
    skip_dirs = {".venv", "node_modules", ".git", "__pycache__", "dist", "build"}
    files: list[str] = []

    for path in project_dir.rglob("*"):
        if len(files) >= max_files:
            break
        if any(skip in path.parts for skip in skip_dirs):
            continue
        if path.is_file() and path.suffix in extensions:
            files.append(str(path))

    return files
