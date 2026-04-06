"""@review — QA review decorator.

Wraps Tear's run_qa_validation_loop():
  QA Reviewer validates -> if rejected, QA Fixer corrects -> re-review -> loop
"""

from .base import agent_decorator

review = agent_decorator(
    agent_type="review",
    default_options={
        "max_iterations": 50,        # max review->fix cycles
        "auto_fix": True,            # auto-run fixer if rejected
        "escalate_after": 3,         # escalate to human after N recurring issues
    },
)
