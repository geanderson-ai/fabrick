"""Fabrikk core — the Fabrick pipeline engine."""

from __future__ import annotations

import time
from typing import Any, Callable

import structlog

from .constants import (
    EXECUTION_LOCAL,
    MACHINE_FLEXIBLE,
    OBSERVABILITY_LANGSMITH,
    OBSERVABILITY_NONE,
    PERSISTENCE_SQLITE,
    STATE_COMPLETED,
    STATE_FAILED,
    STEP_FINISH,
    STEP_START,
)
from .context import ExecutionContext
from .contracts import StepResult
from .decorators import StepInfo, get_step_info
from .exceptions import (
    DuplicateStepError,
    PipelineNotReadyError,
    StepFailedError,
    StepNotFoundError,
)
from .machine import PipelineMachine
from .observability import langsmith_configured, trace_pipeline, trace_step, record_step_result
from .observability.metrics import PipelineMetrics, create_step_metrics
from .persistence import CheckpointStore, create_store
from .providers import get_provider_config, resolve_provider
from .scheduling import SchedulerAdapter

logger = structlog.get_logger("fabrick")


class Fabrick:
    """Declarative AI pipeline orchestrator.

    Usage:
        pipeline = Fabrick(name="My Pipeline", retry=ON)
        pipeline.register(step_a, step_b, step_c)
        pipeline.run(input="some data")
    """

    def __init__(
        self,
        name: str = "Fabrick Pipeline",
        *,
        execution_mode: str = EXECUTION_LOCAL,
        persistence: str = PERSISTENCE_SQLITE,
        observability: str = OBSERVABILITY_NONE,
        retry: bool = False,
        max_retries: int = 3,
        scheduler: str | None = None,
        start_at: str | None = None,
        machine_mode: str = MACHINE_FLEXIBLE,
        provider: str = "ollama",
        model: str = "",
    ):
        self.name = name
        self.execution_mode = execution_mode
        self.persistence = persistence
        self.observability = observability
        self.retry = retry
        self.max_retries = max_retries
        self.scheduler = scheduler
        self.start_at = start_at
        self.machine_mode = machine_mode
        self.provider = provider
        self.model = model

        # Internal registry: step_name -> (function, StepInfo)
        self._steps: dict[str, tuple[Callable, StepInfo]] = {}
        self._ordered_steps: list[str] = []
        self._start_step: str | None = None
        self._finish_step: str | None = None

        # Persistence store (created lazily on run)
        self._store: CheckpointStore | None = None

        # Scheduler (created on start())
        self._scheduler: SchedulerAdapter | None = None

    def register(self, *functions: Callable) -> None:
        """Register one or more decorated step functions."""
        for fn in functions:
            info = get_step_info(fn)
            if info is None:
                raise PipelineNotReadyError(
                    f"Function '{fn.__name__}' is not decorated with @start, @step, or @finish"
                )

            if info.name in self._steps:
                raise DuplicateStepError(info.name)

            self._steps[info.name] = (fn, info)
            self._ordered_steps.append(info.name)

            if info.step_type == STEP_START:
                if self._start_step is not None:
                    raise PipelineNotReadyError("Only one @start step is allowed")
                self._start_step = info.name

            if info.step_type == STEP_FINISH:
                if self._finish_step is not None:
                    raise PipelineNotReadyError("Only one @finish step is allowed")
                self._finish_step = info.name

    def run(self, input: Any = None) -> ExecutionContext:
        """Execute the pipeline synchronously."""
        self._validate()

        # Resolve and configure provider
        provider_adapter = resolve_provider(self.provider)
        provider_config = provider_adapter.resolve_config(self.model)
        provider_adapter.setup_env(provider_config)

        resolved_model = provider_config.model

        logger.info(
            "provider.resolved",
            provider=provider_config.provider_id,
            model=resolved_model,
        )

        context = ExecutionContext(
            pipeline_name=self.name,
            input=input,
            provider=provider_config.provider_id,
            model=resolved_model,
        )

        machine = self._build_machine()
        metrics = PipelineMetrics(pipeline_name=self.name, run_id=context.run_id)

        # Initialize persistence store
        self._get_store()

        # Determine if LangSmith tracing is active
        use_langsmith = (
            self.observability == OBSERVABILITY_LANGSMITH
            and langsmith_configured()
        )

        logger.info("pipeline.start", name=self.name, run_id=context.run_id)

        # Transition from idle to the @start step
        current_step = self._start_step
        assert current_step is not None

        # Wrap execution in optional LangSmith trace
        with trace_pipeline(self.name, context.run_id, input) as pipeline_run:
            try:
                machine.transition(current_step)
                context.transition_to(current_step)

                while current_step is not None:
                    fn, info = self._steps[current_step]

                    logger.info("step.start", step=current_step, state=machine.current_state)
                    step_start = time.monotonic()

                    # Wrap step in optional LangSmith trace
                    with trace_step(current_step, pipeline_run, {"state": current_step}) as step_run:
                        raw_result = self._execute_step(fn, context)
                        result = StepResult.model_validate(raw_result)

                        elapsed = time.monotonic() - step_start
                        context.record_step_timing(current_step, elapsed)
                        context.merge_data(result.data)
                        context.merge_metadata(result.metadata)

                        # Record LangSmith step result
                        if step_run is not None:
                            record_step_result(step_run, raw_result, elapsed)

                    # Collect metrics
                    step_metrics = create_step_metrics(
                        step_name=current_step,
                        elapsed=elapsed,
                        model=resolved_model,
                        metadata=result.metadata,
                    )
                    metrics.add_step(step_metrics)

                    # Persist step result
                    self._persist(
                        self._store, "save_step_result",
                        run_id=context.run_id,
                        step_name=current_step,
                        status=result.status,
                        data=result.data,
                        elapsed_seconds=elapsed,
                    )

                    logger.info(
                        "step.complete",
                        step=current_step,
                        status=result.status,
                        elapsed=f"{elapsed:.3f}s",
                    )

                    if result.status == "failed":
                        if self.retry:
                            current_step = self._retry_step(fn, context, machine, current_step)
                            if current_step is None:
                                machine.fail()
                                context.transition_to(STATE_FAILED)
                                raise StepFailedError(info.name, "Max retries exceeded")
                            continue
                        else:
                            machine.fail()
                            context.transition_to(STATE_FAILED)
                            raise StepFailedError(info.name)

                    # Checkpoint after each successful step
                    self._persist(
                        self._store, "save_checkpoint",
                        run_id=context.run_id,
                        pipeline_name=self.name,
                        state=current_step,
                        data=context.data,
                        metadata=context.metadata,
                    )

                    # Determine next step
                    next_state = result.next_state
                    is_finish = info.step_type == STEP_FINISH or current_step == self._finish_step
                    if is_finish or next_state is None:
                        # Pipeline complete
                        machine.transition(STATE_COMPLETED)
                        context.transition_to(STATE_COMPLETED)
                        current_step = None
                    else:
                        if next_state not in self._steps:
                            raise StepNotFoundError(next_state)
                        machine.transition(next_state)
                        context.transition_to(next_state)
                        current_step = next_state

            except (StepFailedError, StepNotFoundError):
                raise
            except Exception as exc:
                logger.error("pipeline.error", error=str(exc), step=current_step)
                try:
                    machine.fail()
                except Exception:
                    pass
                context.transition_to(STATE_FAILED)
                raise

        # Store final checkpoint
        self._persist(
            self._store, "save_checkpoint",
            run_id=context.run_id,
            pipeline_name=self.name,
            state=context.state,
            data=context.data,
            metadata=context.metadata,
        )

        # Attach metrics summary to context
        context.metadata["metrics"] = metrics.summary()
        context.total_tokens = metrics.total_tokens
        context.total_cost = metrics.total_cost_usd

        logger.info(
            "pipeline.complete",
            name=self.name,
            run_id=context.run_id,
            final_state=context.state,
            steps=len(context.step_timings),
            total_elapsed=f"{metrics.total_elapsed:.3f}s",
        )

        return context

    def _execute_step(self, fn: Callable, context: ExecutionContext) -> dict:
        """Run a step function and return its raw dict result."""
        result = fn(context)
        if not isinstance(result, dict):
            raise TypeError(
                f"Step '{fn.__name__}' must return a dict, got {type(result).__name__}"
            )
        return result

    def _retry_step(
        self,
        fn: Callable,
        context: ExecutionContext,
        machine: PipelineMachine,
        step_name: str,
    ) -> str | None:
        """Retry a failed step up to max_retries times. Returns step name if successful, None if exhausted."""
        for attempt in range(1, self.max_retries + 1):
            logger.warning("step.retry", step=step_name, attempt=attempt)
            try:
                raw_result = fn(context)
                result = StepResult.model_validate(raw_result)
                if result.status != "failed":
                    context.merge_data(result.data)
                    context.merge_metadata(result.metadata)
                    return step_name
            except Exception as exc:
                logger.error("step.retry.error", step=step_name, attempt=attempt, error=str(exc))
        return None

    def _build_machine(self) -> PipelineMachine:
        """Build and return the state machine from registered steps."""
        machine = PipelineMachine(mode=self.machine_mode)
        for name, (_, info) in self._steps.items():
            machine.add_state(name, transitions_to=info.transitions_to)
        machine.build()
        return machine

    def _get_store(self) -> CheckpointStore | None:
        """Get or create the persistence store. Returns None if persistence is 'none'."""
        if self.persistence == "none":
            return None
        if self._store is None:
            try:
                self._store = create_store(self.persistence)
            except Exception as exc:
                logger.warning("persistence.init_failed", backend=self.persistence, error=str(exc))
                return None
        return self._store

    def _persist(self, store: CheckpointStore | None, method: str, **kwargs: Any) -> None:
        """Safely call a persistence method, logging errors without crashing.

        Disables the store after the first failure to avoid repeated slow timeouts.
        """
        if store is None:
            return
        try:
            getattr(store, method)(**kwargs)
        except Exception as exc:
            logger.warning(
                "persistence.error",
                method=method,
                error=str(exc),
                detail="Persistence disabled for this run.",
            )
            self._store = None

    # ── Scheduling & Execution Modes ──

    def start(self) -> None:
        """Start the pipeline with its configured execution mode and scheduler.

        For 'local' mode: equivalent to run().
        For 'background' mode: runs in a background thread.
        If scheduler is set: schedules recurring runs via APScheduler/Cloud.
        """
        from .execution import run_in_background, run_sync

        if self.scheduler:
            self._setup_scheduler()
            return

        if self.execution_mode == "background":
            run_in_background(self)
        else:
            run_sync(self)

    def stop(self) -> None:
        """Stop the scheduler if running."""
        if self._scheduler:
            self._scheduler.shutdown()
            self._scheduler = None

    def _setup_scheduler(self) -> None:
        """Configure and start the scheduler with the pipeline's cron/date config."""
        from .scheduling import create_scheduler

        backend = "apscheduler"  # default; could be extended to detect cloud
        self._scheduler = create_scheduler(backend)

        job_id = f"fabrick-{self.name.replace(' ', '-').lower()}"

        self._scheduler.schedule(
            job_id=job_id,
            run_fn=self.run,
            cron=self.scheduler if self._is_cron(self.scheduler) else None,
            run_date=self.start_at,
        )

        self._scheduler.start()
        logger.info("pipeline.scheduled", job_id=job_id, cron=self.scheduler, start_at=self.start_at)

    @staticmethod
    def _is_cron(value: str | None) -> bool:
        """Simple check if a string looks like a cron expression."""
        if not value:
            return False
        parts = value.strip().split()
        return len(parts) == 5

    def _validate(self) -> None:
        """Validate that the pipeline is properly configured before running.

        If no explicit @start/@finish is declared, the first and last
        registered steps are used (allows agent-only pipelines).
        """
        if not self._steps:
            raise PipelineNotReadyError("No steps registered")
        if self._start_step is None:
            self._start_step = self._ordered_steps[0]
            logger.debug("pipeline.auto_start", step=self._start_step)
        if self._finish_step is None:
            self._finish_step = self._ordered_steps[-1]
            logger.debug("pipeline.auto_finish", step=self._finish_step)
