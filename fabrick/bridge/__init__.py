"""Fabrikk Bridge — adapters between Fabrick decorators and Tear backend."""

from .coder_adapter import run_coder
from .planner_adapter import run_planner
from .qa_adapter import run_qa_loop
from .security_adapter import run_security_scan
from .spec_adapter import run_spec_pipeline
from .tear import TearBridge, get_bridge

__all__ = [
    "TearBridge",
    "get_bridge",
    "run_spec_pipeline",
    "run_planner",
    "run_coder",
    "run_qa_loop",
    "run_security_scan",
]
