"""Fabrikk exceptions."""


class FabrikkError(Exception):
    """Base exception for all Fabrikk errors."""


class InvalidTransitionError(FabrikkError):
    """Raised when a state transition is not allowed."""

    def __init__(self, current_state: str, target_state: str, allowed: list[str] | None = None):
        self.current_state = current_state
        self.target_state = target_state
        self.allowed = allowed
        msg = f"Invalid transition: '{current_state}' -> '{target_state}'"
        if allowed:
            msg += f". Allowed transitions: {allowed}"
        super().__init__(msg)


class StepFailedError(FabrikkError):
    """Raised when a step returns a failed status."""

    def __init__(self, step_name: str, reason: str = ""):
        self.step_name = step_name
        self.reason = reason
        msg = f"Step '{step_name}' failed"
        if reason:
            msg += f": {reason}"
        super().__init__(msg)


class PipelineNotReadyError(FabrikkError):
    """Raised when trying to run a pipeline that isn't properly configured."""


class StepNotFoundError(FabrikkError):
    """Raised when a referenced step/state doesn't exist."""

    def __init__(self, state_name: str):
        self.state_name = state_name
        super().__init__(f"No step registered for state '{state_name}'")


class DuplicateStepError(FabrikkError):
    """Raised when registering a step with a name that already exists."""

    def __init__(self, step_name: str):
        self.step_name = step_name
        super().__init__(f"Step '{step_name}' is already registered")
