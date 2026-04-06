"""Fabrikk metrics — token counting, cost estimation, and timing."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

# Approximate cost per 1M tokens (USD) for common models
_COST_TABLE: dict[str, dict[str, float]] = {
    "claude-3-5-sonnet-20241022": {"input": 3.0, "output": 15.0},
    "claude-3-5-haiku-20241022": {"input": 0.25, "output": 1.25},
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    # OpenRouter / Gemini models — approximate
    "moonshotai/kimi-k2.5": {"input": 1.0, "output": 3.0},
    "google/gemini-2.0-flash-001": {"input": 0.1, "output": 0.4},
    # Ollama — free (local)
    "_local_default": {"input": 0.0, "output": 0.0},
}


@dataclass
class StepMetrics:
    """Metrics collected for a single step execution."""

    step_name: str
    elapsed_seconds: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineMetrics:
    """Aggregated metrics across all steps in a pipeline run."""

    pipeline_name: str
    run_id: str
    steps: list[StepMetrics] = field(default_factory=list)

    @property
    def total_elapsed(self) -> float:
        return sum(s.elapsed_seconds for s in self.steps)

    @property
    def total_tokens(self) -> int:
        return sum(s.total_tokens for s in self.steps)

    @property
    def total_cost_usd(self) -> float:
        return sum(s.estimated_cost_usd for s in self.steps)

    def add_step(self, metrics: StepMetrics) -> None:
        self.steps.append(metrics)

    def summary(self) -> dict[str, Any]:
        return {
            "pipeline": self.pipeline_name,
            "run_id": self.run_id,
            "total_steps": len(self.steps),
            "total_elapsed_seconds": round(self.total_elapsed, 3),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "steps": [
                {
                    "name": s.step_name,
                    "elapsed": round(s.elapsed_seconds, 3),
                    "tokens": s.total_tokens,
                    "cost": round(s.estimated_cost_usd, 6),
                }
                for s in self.steps
            ],
        }


def estimate_cost(
    model: str,
    input_tokens: int = 0,
    output_tokens: int = 0,
) -> float:
    """Estimate cost in USD based on model and token counts."""
    costs = _COST_TABLE.get(model, _COST_TABLE["_local_default"])
    input_cost = (input_tokens / 1_000_000) * costs["input"]
    output_cost = (output_tokens / 1_000_000) * costs["output"]
    return input_cost + output_cost


def create_step_metrics(
    step_name: str,
    elapsed: float,
    model: str = "",
    input_tokens: int = 0,
    output_tokens: int = 0,
    metadata: dict[str, Any] | None = None,
) -> StepMetrics:
    """Create a StepMetrics instance with cost estimation."""
    total = input_tokens + output_tokens
    cost = estimate_cost(model, input_tokens, output_tokens) if model else 0.0

    return StepMetrics(
        step_name=step_name,
        elapsed_seconds=elapsed,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=total,
        estimated_cost_usd=cost,
        metadata=metadata or {},
    )
