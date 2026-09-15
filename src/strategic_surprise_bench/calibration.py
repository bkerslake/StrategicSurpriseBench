"""Expert-label corpus validation and fail-closed release gating."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator

from strategic_surprise_bench.legacy_versions import (
    BENCHMARK_VERSION,
    JUDGE_PROMPT_VERSION,
    RUBRIC_VERSION,
)
from strategic_surprise_bench.loader import load_all_cases
from strategic_surprise_bench.models import StrictModel
from strategic_surprise_bench.reliability import ReliabilityReport, evaluate_reliability

Label = Literal[0.0, 0.5, 1.0]


class CriterionLabel(StrictModel):
    case_id: str
    response_id: str
    split: Literal["calibration", "holdout"]
    rubric_id: str
    expert_a: Label
    expert_b: Label
    adjudicated: Label
    judge_label: Label | None = None
    critical: bool = False


class AggregateLabel(StrictModel):
    case_id: str
    response_id: str
    split: Literal["calibration", "holdout"]
    expert_score: float = Field(ge=0, le=100)
    judge_score: float = Field(ge=0, le=100)


class ScenarioReview(StrictModel):
    case_id: str
    domain_reviewer_count: int = Field(ge=0)
    methods_reviewer: bool
    plausibility_mean: float = Field(ge=1, le=5)
    answerability_mean: float = Field(ge=1, le=5)
    human_human_alpha: float = Field(ge=-1, le=1)
    approved: bool


class CalibrationCorpus(StrictModel):
    benchmark_version: str
    rubric_version: str
    judge_prompt_version: str
    calibration_version: str
    locked_at: datetime | None = None
    criterion_labels: list[CriterionLabel]
    aggregate_labels: list[AggregateLabel]
    scenario_reviews: list[ScenarioReview]
    paraphrase_invariance: float = Field(ge=0, le=1)
    evidence_deletion_sensitivity: float = Field(ge=0, le=1)

    @model_validator(mode="after")
    def unique_rows(self) -> CalibrationCorpus:
        keys = [(item.case_id, item.response_id, item.rubric_id) for item in self.criterion_labels]
        if len(keys) != len(set(keys)):
            raise ValueError("criterion label rows must be unique")
        aggregate_keys = [(item.case_id, item.response_id) for item in self.aggregate_labels]
        if len(aggregate_keys) != len(set(aggregate_keys)):
            raise ValueError("aggregate label rows must be unique")
        return self


@dataclass(frozen=True)
class ReleaseGateReport:
    benchmark_version: str
    rubric_version: str
    judge_prompt_version: str
    calibration_version: str
    locked_holdout: bool
    corpus_complete: bool
    scenario_review_complete: bool
    reliability: ReliabilityReport | None
    subgroup_reliability: dict[str, dict]
    passed: bool
    failures: tuple[str, ...]

    def to_dict(self) -> dict:
        value = asdict(self)
        return value


def _validate_corpus_shape(corpus: CalibrationCorpus) -> list[str]:
    failures: list[str] = []
    cases = {case.manifest.id: case for case in load_all_cases()}
    provided_cases = {item.case_id for item in corpus.criterion_labels}
    if provided_cases != set(cases):
        failures.append("corpus_case_set")

    for case_id, case in cases.items():
        rows = [item for item in corpus.criterion_labels if item.case_id == case_id]
        response_splits: dict[str, str] = {}
        for row in rows:
            previous = response_splits.setdefault(row.response_id, row.split)
            if previous != row.split:
                failures.append(f"{case_id}:response_split_conflict")
        calibration_ids = {item.response_id for item in rows if item.split == "calibration"}
        holdout_ids = {item.response_id for item in rows if item.split == "holdout"}
        if len(calibration_ids) != 16:
            failures.append(f"{case_id}:calibration_response_count")
        if len(holdout_ids) != 8:
            failures.append(f"{case_id}:holdout_response_count")
        expected_rubrics = {item.id for item in case.rubric}
        for response_id in calibration_ids | holdout_ids:
            actual_rubrics = {item.rubric_id for item in rows if item.response_id == response_id}
            if actual_rubrics != expected_rubrics:
                failures.append(f"{case_id}:{response_id}:rubric_coverage")

        aggregates = [item for item in corpus.aggregate_labels if item.case_id == case_id]
        aggregate_holdouts = {item.response_id for item in aggregates if item.split == "holdout"}
        if aggregate_holdouts != holdout_ids:
            failures.append(f"{case_id}:aggregate_holdout_coverage")
    return sorted(set(failures))


def _validate_reviews(corpus: CalibrationCorpus) -> list[str]:
    failures: list[str] = []
    case_ids = {case.manifest.id for case in load_all_cases()}
    reviews = {review.case_id: review for review in corpus.scenario_reviews}
    if set(reviews) != case_ids:
        failures.append("scenario_review_case_set")
    for case_id in case_ids:
        review = reviews.get(case_id)
        if review is None:
            continue
        if review.domain_reviewer_count < 2:
            failures.append(f"{case_id}:reviewer_count")
        if not review.methods_reviewer:
            failures.append(f"{case_id}:methods_review")
        if review.plausibility_mean < 4:
            failures.append(f"{case_id}:plausibility")
        if review.answerability_mean < 4:
            failures.append(f"{case_id}:answerability")
        if review.human_human_alpha < 0.67:
            failures.append(f"{case_id}:human_alpha")
        if not review.approved:
            failures.append(f"{case_id}:approval")
    return sorted(set(failures))


def evaluate_calibration(corpus: CalibrationCorpus) -> ReleaseGateReport:
    corpus_failures = _validate_corpus_shape(corpus)
    review_failures = _validate_reviews(corpus)
    holdout = [item for item in corpus.criterion_labels if item.split == "holdout"]
    aggregates = [item for item in corpus.aggregate_labels if item.split == "holdout"]
    reliability: ReliabilityReport | None = None
    subgroup_reliability: dict[str, dict] = {}
    reliability_failures: list[str] = []
    if corpus_failures or not holdout or not aggregates:
        reliability_failures.append("reliability_not_computable")
    else:
        try:
            reliability = evaluate_reliability(
                expert_labels=[item.adjudicated for item in holdout],
                judge_labels=[item.judge_label for item in holdout],
                second_expert_labels=[item.expert_b for item in holdout],
                expert_aggregate_scores=[item.expert_score for item in aggregates],
                judge_aggregate_scores=[item.judge_score for item in aggregates],
                first_expert_labels=[item.expert_a for item in holdout],
                critical_mask=[item.critical for item in holdout],
                invariance=corpus.paraphrase_invariance,
                deletion_sensitivity=corpus.evidence_deletion_sensitivity,
            )
        except ValueError:
            reliability_failures.append("reliability_not_computable")
        else:
            reliability_failures.extend(f"reliability:{item}" for item in reliability.failures)
            subgroup_keys = sorted(
                {f"case:{item.case_id}" for item in holdout}
                | {f"rubric:{item.rubric_id}" for item in holdout}
            )
            for key in subgroup_keys:
                prefix, identifier = key.split(":", 1)
                rows = [
                    item
                    for item in holdout
                    if (item.case_id if prefix == "case" else item.rubric_id) == identifier
                ]
                case_ids = {item.case_id for item in rows}
                subgroup_aggregates = [item for item in aggregates if item.case_id in case_ids]
                try:
                    subgroup = evaluate_reliability(
                        expert_labels=[item.adjudicated for item in rows],
                        judge_labels=[item.judge_label for item in rows],
                        second_expert_labels=[item.expert_b for item in rows],
                        first_expert_labels=[item.expert_a for item in rows],
                        expert_aggregate_scores=[item.expert_score for item in subgroup_aggregates],
                        judge_aggregate_scores=[item.judge_score for item in subgroup_aggregates],
                        critical_mask=[item.critical for item in rows],
                        invariance=corpus.paraphrase_invariance,
                        deletion_sensitivity=corpus.evidence_deletion_sensitivity,
                    )
                except ValueError:
                    subgroup_reliability[key] = {"computable": False}
                else:
                    subgroup_reliability[key] = {
                        "computable": True,
                        **asdict(subgroup),
                    }

    failures = tuple(
        [*(f"corpus:{item}" for item in corpus_failures)]
        + [*(f"review:{item}" for item in review_failures)]
        + reliability_failures
        + ([] if corpus.locked_at else ["holdout_not_locked"])
    )
    return ReleaseGateReport(
        benchmark_version=corpus.benchmark_version,
        rubric_version=corpus.rubric_version,
        judge_prompt_version=corpus.judge_prompt_version,
        calibration_version=corpus.calibration_version,
        locked_holdout=corpus.locked_at is not None,
        corpus_complete=not corpus_failures,
        scenario_review_complete=not review_failures,
        reliability=reliability,
        subgroup_reliability=subgroup_reliability,
        passed=not failures,
        failures=failures,
    )


def load_corpus(path: str | Path) -> CalibrationCorpus:
    return CalibrationCorpus.model_validate_json(Path(path).read_text())


def load_gate_report(path: str | Path) -> ReleaseGateReport:
    raw = json.loads(Path(path).read_text())
    reliability_raw = raw.get("reliability")
    reliability = ReliabilityReport(**reliability_raw) if reliability_raw else None
    return ReleaseGateReport(
        benchmark_version=raw["benchmark_version"],
        rubric_version=raw["rubric_version"],
        judge_prompt_version=raw["judge_prompt_version"],
        calibration_version=raw["calibration_version"],
        locked_holdout=raw["locked_holdout"],
        corpus_complete=raw["corpus_complete"],
        scenario_review_complete=raw["scenario_review_complete"],
        reliability=reliability,
        subgroup_reliability=raw.get("subgroup_reliability", {}),
        passed=raw["passed"],
        failures=tuple(raw.get("failures", [])),
    )


def gate_allows_automated_scoring(
    path: str | Path | None,
    *,
    benchmark_version: str = BENCHMARK_VERSION,
    rubric_version: str = RUBRIC_VERSION,
    judge_prompt_version: str = JUDGE_PROMPT_VERSION,
) -> bool:
    if path is None or not Path(path).is_file():
        return False
    try:
        report = load_gate_report(path)
    except (KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False
    return (
        report.passed
        and report.locked_holdout
        and report.corpus_complete
        and report.scenario_review_complete
        and report.benchmark_version == benchmark_version
        and report.rubric_version == rubric_version
        and report.judge_prompt_version == judge_prompt_version
    )
