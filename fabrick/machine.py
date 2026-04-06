"""Fabrikk PipelineMachine — state machine wrapper around `transitions`."""

from __future__ import annotations

from transitions import Machine

from .constants import MACHINE_FLEXIBLE, MACHINE_STRICT, STATE_COMPLETED, STATE_FAILED, STATE_IDLE
from .exceptions import InvalidTransitionError


class PipelineMachine:
    """Wraps the `transitions` library to manage pipeline state lifecycle.

    Supports two modes:
    - flexible (default): any registered state can transition to any other.
    - strict: only transitions declared via `transitions_to` are allowed.
    """

    def __init__(self, mode: str = MACHINE_FLEXIBLE):
        self.mode = mode
        self._states: list[str] = [STATE_IDLE, STATE_FAILED, STATE_COMPLETED]
        self._transitions: list[dict] = []
        self._step_allowed_targets: dict[str, list[str]] = {}
        self._machine: Machine | None = None
        self._model = _MachineModel()

    def add_state(self, name: str, transitions_to: list[str] | None = None) -> None:
        """Register a state (step name) in the machine."""
        if name not in self._states:
            self._states.append(name)
        if transitions_to:
            self._step_allowed_targets[name] = transitions_to

    def build(self) -> None:
        """Build the internal transitions.Machine after all states are registered."""
        if self.mode == MACHINE_FLEXIBLE:
            self._transitions = self._build_flexible_transitions()
        else:
            self._transitions = self._build_strict_transitions()

        # Always allow transition to failed from any state
        for state in self._states:
            if state != STATE_FAILED:
                self._transitions.append({
                    "trigger": "fail",
                    "source": state,
                    "dest": STATE_FAILED,
                })

        self._machine = Machine(
            model=self._model,
            states=self._states,
            transitions=self._transitions,
            initial=STATE_IDLE,
            auto_transitions=False,
            send_event=False,
        )

    def _build_flexible_transitions(self) -> list[dict]:
        """In flexible mode, every state can go to every other state."""
        transitions = []
        non_terminal = [s for s in self._states if s not in (STATE_FAILED, STATE_COMPLETED)]
        all_targets = [s for s in self._states if s != STATE_IDLE]

        for source in non_terminal:
            for dest in all_targets:
                if source != dest:
                    transitions.append({
                        "trigger": f"to_{dest}",
                        "source": source,
                        "dest": dest,
                    })
        return transitions

    def _build_strict_transitions(self) -> list[dict]:
        """In strict mode, only declared transitions are allowed."""
        transitions = []
        for source, targets in self._step_allowed_targets.items():
            for dest in targets:
                transitions.append({
                    "trigger": f"to_{dest}",
                    "source": source,
                    "dest": dest,
                })
        # idle -> first registered non-special state
        first_step = self._get_first_step()
        if first_step:
            transitions.append({
                "trigger": f"to_{first_step}",
                "source": STATE_IDLE,
                "dest": first_step,
            })
        return transitions

    def _get_first_step(self) -> str | None:
        """Return the first user-registered state (not idle/failed/completed)."""
        special = {STATE_IDLE, STATE_FAILED, STATE_COMPLETED}
        for s in self._states:
            if s not in special:
                return s
        return None

    def transition(self, target_state: str) -> None:
        """Execute a state transition."""
        trigger_name = f"to_{target_state}"
        current = self._model.state

        if not hasattr(self._model, trigger_name):
            allowed = self.get_allowed_transitions()
            raise InvalidTransitionError(current, target_state, allowed)

        trigger_fn = getattr(self._model, trigger_name)
        if not trigger_fn():
            allowed = self.get_allowed_transitions()
            raise InvalidTransitionError(current, target_state, allowed)

    def fail(self) -> None:
        """Transition to the failed state from any state."""
        self._model.fail()

    @property
    def current_state(self) -> str:
        return self._model.state

    def get_allowed_transitions(self) -> list[str]:
        """Return states reachable from the current state."""
        current = self._model.state
        allowed = []
        for t in self._transitions:
            if t["source"] == current:
                allowed.append(t["dest"])
        return sorted(set(allowed))


class _MachineModel:
    """Internal model object for the transitions library."""
    pass
