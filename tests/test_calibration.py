from __future__ import annotations

import json
from datetime import UTC, datetime

from strategic_surprise_bench.calibration import (
    CalibrationCorpus,
    evaluate_calibration,
    gate_allows_automated_scoring,
)
from strategic_surprise_bench.legacy_versions import (
    BENCHMARK_VERSION,
    JUDGE_PROMPT_VERSION,
    RUBRIC_VERSION,
)
from strategic_surprise_bench.loader import load_all_cases
from strategic_surprise_bench.reliability import evaluate_reliability


def complete_synthetic_corpus() -> CalibrationCorpus:
    criterion_labels = []
    aggregate_labels = []
    scenario_reviews = []
    values = [0.0, 0.5, 1.0]
    for case in load_all_cases():
        for index in range(24):
            response_id = f"{case.manifest.id}-R{index:02d}"
            split = "calibration" if index < 16 else "holdout"
            label = values[index % len(values)]
            for rubric in case.rubric:
                criterion_labels.append(
                    {
                        "case_id": case.manifest.id,
                        "response_id": response_id,
                        "split": split,
                        "rubric_id": rubric.id,
                        "expert_a": label,
                        "expert_b": label,
                        "adjudicated": label,
                        "judge_label": label,
                        "critical": rubric.critical,
                    }
                )
            aggregate = 25.0 + 2.5 * index
            aggregate_labels.append(
                {
                    "case_id": case.manifest.id,
                    "response_id": response_id,
                    "split": split,
                    "expert_score": aggregate,
                    "judge_score": aggregate,
                }
            )
        scenario_reviews.append(
            {
                "case_id": case.manifest.id,
                "domain_reviewer_count": 2,
                "methods_reviewer": True,
                "plausibility_mean": 4.5,
                "answerability_mean": 4.5,
                "human_human_alpha": 0.9,
                "approved": True,
            }
        )
    return CalibrationCorpus(
        benchmark_version=BENCHMARK_VERSION,
        rubric_version=RUBRIC_VERSION,
        judge_prompt_version=JUDGE_PROMPT_VERSION,
        calibration_version="synthetic-test-only",
        locked_at=datetime.now(UTC),
        criterion_labels=criterion_labels,
        aggregate_labels=aggregate_labels,
        scenario_reviews=scenario_reviews,
        paraphrase_invariance=1.0,
        evidence_deletion_sensitivity=1.0,
    )


def test_reliability_metrics_pass_for_identical_labels():
    labels = [0.0, 0.5, 1.0] * 20
    aggregates = [20.0, 40.0, 60.0, 80.0, 90.0]
    report = evaluate_reliability(
        expert_labels=labels,
        judge_labels=labels,
        second_expert_labels=labels,
        expert_aggregate_scores=aggregates,
        judge_aggregate_scores=aggregates,
        critical_mask=[True] * len(labels),
    )
    assert report.passed, report.failures
    assert report.coverage == 1
    assert report.accepted_agreement == 1


def test_complete_locked_corpus_passes_and_can_open_gate(tmp_path):
    report = evaluate_calibration(complete_synthetic_corpus())
    assert report.passed, report.failures
    path = tmp_path / "gate.json"
    path.write_text(json.dumps(report.to_dict(), default=str))
    assert gate_allows_automated_scoring(path)
    stale = report.to_dict()
    stale["judge_prompt_version"] = "stale"
    path.write_text(json.dumps(stale, default=str))
    assert not gate_allows_automated_scoring(path)


def test_missing_or_incomplete_expert_corpus_fails_closed(tmp_path):
    assert not gate_allows_automated_scoring(tmp_path / "missing.json")
    corpus = complete_synthetic_corpus()
    corpus.criterion_labels = corpus.criterion_labels[:-1]
    report = evaluate_calibration(corpus)
    assert not report.passed
    assert any("rubric_coverage" in failure for failure in report.failures)


def test_abstention_counts_against_coverage():
    labels = [0.0, 0.5, 1.0] * 10
    judges = [value if index < 15 else None for index, value in enumerate(labels)]
    report = evaluate_reliability(
        expert_labels=labels,
        judge_labels=judges,
        second_expert_labels=labels,
        expert_aggregate_scores=[30, 50, 70, 90],
        judge_aggregate_scores=[30, 50, 70, 90],
    )
    assert report.coverage == 0.5
    assert not report.passed
    assert "coverage" in report.failures
