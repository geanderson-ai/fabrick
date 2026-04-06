"""@plan — Implementation planning decorator.

Wraps Tear's run_followup_planner():
  Reads spec -> creates implementation_plan.json with phases and subtasks.
"""

from .base import agent_decorator

plan = agent_decorator(
    agent_type="plan",
    default_options={
        "max_phases": 10,            # maximum phases in the plan
        "parallel_subtasks": True,   # allow parallel subtask execution
    },
)
