"""@security — Security validation decorator.

Wraps Tear's security scanners:
  scan_secrets -> validate_commands -> risk_classifier -> dependency audit
"""

from .base import agent_decorator

security = agent_decorator(
    agent_type="security",
    default_options={
        "scan_secrets": True,          # scan for exposed secrets
        "validate_commands": True,     # validate bash commands against allowlist
        "check_dependencies": True,    # check dependency vulnerabilities
        "fail_on": "critical",         # critical | high | medium | low
    },
)
