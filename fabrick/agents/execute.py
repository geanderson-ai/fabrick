"""@execute — Code execution decorator.

Wraps Tear's run_autonomous_agent():
  Pick subtask -> generate prompt -> run agent -> validate -> commit -> repeat
"""

from .base import agent_decorator

execute = agent_decorator(
    agent_type="execute",
    default_options={
        "max_retries": 3,                # retries per subtask
        "retry_delay": "exponential",    # exponential | fixed | linear
        "parallel_agents": 1,            # parallel agents (worktrees)
        "auto_commit": True,             # auto-commit per subtask
    },
)
