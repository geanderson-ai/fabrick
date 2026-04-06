"""Fabrikk Bridge — main Tear adapter.

Resolves Tear's backend path and provides a unified interface for
importing and calling Tear modules from the Fabrick pipeline.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger("fabrikk.bridge")

# Default relative path from fabrikk package to Tear backend
_DEFAULT_TEAR_BACKEND = Path(__file__).resolve().parents[2] / "Tear" / "apps" / "backend"


class TearBridge:
    """Central adapter that manages the connection to the Tear backend.

    Handles sys.path injection, module importing, and provides
    typed accessors for each Tear subsystem.
    """

    def __init__(self, backend_path: Path | None = None):
        self.backend_path = (backend_path or _DEFAULT_TEAR_BACKEND).resolve()
        self._initialized = False

    def initialize(self) -> None:
        """Add Tear backend to sys.path so its modules are importable."""
        if self._initialized:
            return

        if not self.backend_path.exists():
            raise FileNotFoundError(
                f"Tear backend not found at {self.backend_path}. "
                "Set TEAR_BACKEND_PATH or pass backend_path to TearBridge()."
            )

        backend_str = str(self.backend_path)
        if backend_str not in sys.path:
            sys.path.insert(0, backend_str)
            logger.debug("tear.path_injected", path=backend_str)

        self._initialized = True

    def import_module(self, module_path: str) -> Any:
        """Import a module from the Tear backend.

        Args:
            module_path: Dotted module path relative to the backend root.
                         e.g. "spec.pipeline.orchestrator"
        """
        self.initialize()
        return importlib.import_module(module_path)

    def get_spec_orchestrator(self) -> type:
        """Return the SpecOrchestrator class from Tear."""
        mod = self.import_module("spec.pipeline.orchestrator")
        return mod.SpecOrchestrator

    def get_planner(self) -> Any:
        """Return the run_followup_planner function from Tear."""
        mod = self.import_module("agents.planner")
        return mod.run_followup_planner

    def get_coder(self) -> Any:
        """Return the run_autonomous_agent function from Tear."""
        mod = self.import_module("agents.coder")
        return mod.run_autonomous_agent

    def get_qa_loop(self) -> Any:
        """Return the run_qa_validation_loop function from Tear."""
        mod = self.import_module("qa.loop")
        return mod.run_qa_validation_loop

    def get_security_hook(self) -> Any:
        """Return the bash_security_hook function from Tear."""
        mod = self.import_module("security.hooks")
        return mod.bash_security_hook

    def get_command_validator(self) -> Any:
        """Return the validate_command function from Tear."""
        mod = self.import_module("security.hooks")
        return mod.validate_command

    def get_secret_scanner(self) -> Any:
        """Return the scan_files function from Tear."""
        mod = self.import_module("security.scan_secrets")
        return mod.scan_files


# Singleton instance — initialized lazily
_bridge: TearBridge | None = None


def get_bridge(backend_path: Path | None = None) -> TearBridge:
    """Get or create the global TearBridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = TearBridge(backend_path=backend_path)
    return _bridge
