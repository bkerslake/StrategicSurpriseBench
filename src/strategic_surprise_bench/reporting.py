"""Pilot aggregation and hierarchical uncertainty estimates."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

import numpy as np
from pydantic import Field

from strategic_surprise_bench.models import StrictModel


class RunRecord(StrictModel):
    case_id: str
    model: str
    condition: str
    run: int = Field(ge=1)
    total: float = Field(ge=0, le=100)
    automation_coverage: float = Field(ge=0, le=1)
    human_escalation_rate: float = Field(ge=0, le=1)
    latency_seconds: float | None = Field(default=None, ge=0)
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    tool_calls: int = Field(default=0, ge=0)
    schema_repairs: int = Field(default=0, ge=0)
    schema_failure: bool = False
    refusal: bool = False


@dataclass(frozen=True)
class BootstrapInterval:
    mean: float
    lower: float
    upper: float
    samples: int


def hierarchical_bootstrap(
    records: list[RunRecord],
    *,
    samples: int = 5000,
    seed: int = 203,
) -> BootstrapInterval:
    """Resample cases, then within-case runs, preserving case as the top-level unit."""
    if not records:
        raise ValueError("records cannot be empty")
    by_case: dict[str, list[float]] = defaultdict(list)
    for record in records:
        by_case[record.case_id].append(record.total)
    case_ids = sorted(by_case)
    rng = np.random.default_rng(seed)
    estimates = np.empty(samples)
    for index in range(samples):
        sampled_cases = rng.choice(case_ids, size=len(case_ids), replace=True)
        case_means: list[float] = []
        for case_id in sampled_cases:
            values = np.asarray(by_case[str(case_id)], dtype=float)
            sampled_runs = rng.choice(values, size=len(values), replace=True)
            case_means.append(float(np.mean(sampled_runs)))
        estimates[index] = float(np.mean(case_means))
    return BootstrapInterval(
        mean=float(np.mean([item.total for item in records])),
        lower=float(np.quantile(estimates, 0.025)),
        upper=float(np.quantile(estimates, 0.975)),
        samples=samples,
    )


def summarize_runs(records: list[RunRecord], *, bootstrap_samples: int = 5000) -> dict:
    if not records:
        raise ValueError("records cannot be empty")
    groups: dict[tuple[str, str, str], list[RunRecord]] = defaultdict(list)
    for record in records:
        groups[(record.model, record.condition, record.case_id)].append(record)
    per_case = []
    for (model, condition, case_id), items in sorted(groups.items()):
        values = np.asarray([item.total for item in items], dtype=float)
        per_case.append(
            {
                "model": model,
                "condition": condition,
                "case_id": case_id,
                "runs": len(items),
                "mean": float(values.mean()),
                "median": float(np.median(values)),
                "minimum": float(values.min()),
                "maximum": float(values.max()),
                "automation_coverage": float(np.mean([item.automation_coverage for item in items])),
                "human_escalation_rate": float(
                    np.mean([item.human_escalation_rate for item in items])
                ),
                "mean_tool_calls": float(np.mean([item.tool_calls for item in items])),
                "schema_failure_rate": float(np.mean([item.schema_failure for item in items])),
                "refusal_rate": float(np.mean([item.refusal for item in items])),
            }
        )

    by_model_condition: dict[tuple[str, str], list[RunRecord]] = defaultdict(list)
    for record in records:
        by_model_condition[(record.model, record.condition)].append(record)
    aggregate = []
    for (model, condition), items in sorted(by_model_condition.items()):
        interval = hierarchical_bootstrap(items, samples=bootstrap_samples)
        aggregate.append(
            {
                "model": model,
                "condition": condition,
                "mean": interval.mean,
                "ci95": [interval.lower, interval.upper],
                "bootstrap_samples": interval.samples,
                "automation_coverage": float(np.mean([item.automation_coverage for item in items])),
                "human_escalation_rate": float(
                    np.mean([item.human_escalation_rate for item in items])
                ),
                "mean_tool_calls": float(np.mean([item.tool_calls for item in items])),
                "schema_failure_rate": float(np.mean([item.schema_failure for item in items])),
                "refusal_rate": float(np.mean([item.refusal for item in items])),
            }
        )

    uplift: list[dict] = []
    models = sorted({item.model for item in records})
    for model in models:
        plain = [item for item in records if item.model == model and item.condition == "plain"]
        agent = [item for item in records if item.model == model and item.condition == "agent"]
        plain_by_case: dict[str, list[float]] = defaultdict(list)
        agent_by_case: dict[str, list[float]] = defaultdict(list)
        for item in plain:
            plain_by_case[item.case_id].append(item.total)
        for item in agent:
            agent_by_case[item.case_id].append(item.total)
        shared = sorted(set(plain_by_case) & set(agent_by_case))
        if shared:
            differences = [
                float(np.mean(agent_by_case[case_id]) - np.mean(plain_by_case[case_id]))
                for case_id in shared
            ]
            uplift.append(
                {
                    "model": model,
                    "agent_uplift": float(np.mean(differences)),
                    "cases": len(shared),
                }
            )
    return {
        "exploratory": True,
        "per_case": per_case,
        "aggregate": aggregate,
        "agent_uplift": uplift,
    }
