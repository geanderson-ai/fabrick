"""@spec — Specification creation decorator.

Wraps Tear's SpecOrchestrator pipeline:
  discovery -> research -> writing -> critique

Generates: spec.md, requirements.json, context.json
"""

from .base import agent_decorator

spec = agent_decorator(
    agent_type="spec",
    default_options={
        "mode": "interactive",       # interactive | task | auto
        "complexity": "auto",        # auto | simple | moderate | complex
    },
)
