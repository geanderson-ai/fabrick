from transitions import Machine

from fabrikk.logging_config import get_logger

logger = get_logger()

RESERVED_STATES = {"idle", "completed", "failed"}


class InvalidTransitionError(RuntimeError):
    """Raised when a state transition is not allowed in strict mode."""
    pass


class PipelineMachine:
    """Wraps transitions.Machine to manage pipeline lifecycle.

    Two modes of operation:
    - Flexible (default): auto_transitions=True, any step can go to any other.
    - Strict (opt-in): auto_transitions=False, only declared transitions are allowed.
      Activated when any step declares transitions_to.
    """

    state = None  # managed by transitions.Machine

    def __init__(self, steps_meta, start_step_name, finish_step_name):
        """Build the state machine from registered step metadata.

        Args:
            steps_meta: list of dicts with keys 'name', 'kind', 'transitions_to'.
            start_step_name: name of the @start step.
            finish_step_name: name of the @finish step.
        """
        self._start_step_name = start_step_name
        self._finish_step_name = finish_step_name

        # Validate reserved names
        for meta in steps_meta:
            if meta["name"] in RESERVED_STATES:
                raise ValueError(
                    f"Step name '{meta['name']}' is reserved. "
                    f"Cannot use: {', '.join(sorted(RESERVED_STATES))}"
                )

        # Determine mode: strict if any step declares transitions_to
        self._strict = any(
            meta.get("transitions_to") is not None for meta in steps_meta
        )

        # Build states
        step_names = [meta["name"] for meta in steps_meta]
        states = ["idle"] + step_names + ["completed", "failed"]

        # Build transitions
        transitions = self._build_transitions(steps_meta, step_names)

        # Create the machine
        self._machine = Machine(
            model=self,
            states=states,
            initial="idle",
            transitions=transitions,
            send_event=True,
            before_state_change=self._before_state_change,
            after_state_change=self._after_state_change,
        )

    def _build_transitions(self, steps_meta, step_names):
        transitions = []

        # begin: idle -> start step
        transitions.append({
            "trigger": "begin",
            "source": "idle",
            "dest": self._start_step_name,
        })

        # fail: any -> failed (wildcard)
        transitions.append({
            "trigger": "fail",
            "source": "*",
            "dest": "failed",
        })

        # complete: finish step -> completed
        transitions.append({
            "trigger": "complete",
            "source": self._finish_step_name,
            "dest": "completed",
        })

        if self._strict:
            # Only declared transitions
            meta_by_name = {m["name"]: m for m in steps_meta}
            for meta in steps_meta:
                targets = meta.get("transitions_to")
                if targets:
                    for target in targets:
                        transitions.append({
                            "trigger": f"to_{target}",
                            "source": meta["name"],
                            "dest": target,
                        })
        else:
            # Flexible: any step can go to any other step
            for source in step_names:
                for dest in step_names:
                    if source != dest:
                        transitions.append({
                            "trigger": f"to_{dest}",
                            "source": source,
                            "dest": dest,
                        })

        return transitions

    def advance_to(self, target_state):
        """Validate and transition to the target state.

        Raises InvalidTransitionError if the transition is not allowed.
        """
        trigger_name = f"to_{target_state}"

        allowed = self.get_allowed_triggers()
        if trigger_name not in allowed:
            raise InvalidTransitionError(
                f"Transition from '{self.current_state}' to '{target_state}' "
                f"is not allowed. Allowed triggers: {allowed}"
            )

        # Fire the trigger
        self.trigger(trigger_name)

    @property
    def current_state(self):
        return self.state

    @property
    def is_strict(self):
        return self._strict

    def get_allowed_triggers(self):
        """Return list of trigger names available from the current state."""
        return [
            event.name
            for event in self._machine.events.values()
            for _ in event.transitions.get(self.state, [])
        ] + [
            event.name
            for event in self._machine.events.values()
            for _ in event.transitions.get("*", [])
        ]

    def reset(self):
        """Reset the machine to idle state for re-execution."""
        self.state = "idle"
        logger.debug("Machine reset to idle")

    def _before_state_change(self, event):
        logger.info(
            "State transition",
            from_state=self.state,
            to_state=event.transition.dest,
            trigger=event.event.name,
        )

    def _after_state_change(self, event):
        logger.debug("State changed", current_state=self.state)
        if self.state in ("completed", "failed"):
            logger.info("Pipeline reached terminal state", state=self.state)
