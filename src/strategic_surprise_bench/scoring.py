"""Deterministic benchmark scoring with optional calibrated rubric decisions."""

from __future__ import annotations

from collections import Counter

from pydantic import BaseModel, ConfigDict, Field

from strategic_surprise_bench.mechanics import (
    optimal_collection_portfolio,
    portfolio_information_gain,
    validate_session,
)
from strategic_surprise_bench.models import (
    RoundResponse,
    ScenarioCase,
    ValidationDecision,
    ValidationStatus,
)
from strategic_surprise_bench.rubric import deterministic_topic_screen

ROUND_WEIGHTS = {1: 0.50, 2: 0.35, 3: 0.15}
UNINFORMED_BRIER_LOSS = 0.30


class ScoreBreakdown(BaseModel):
    model_config = ConfigDict(extra="forbid")
    forecast_accuracy: float = Field(ge=0, le=25)
    evidence_handling: float = Field(ge=0, le=15)
    strategic_reasoning: float = Field(ge=0, le=20)
    collection_value: float = Field(ge=0, le=15)
    collection_coverage: float = Field(ge=0, le=5)
    policy_consequences: float = Field(ge=0, le=8)
    policy_tasks: float = Field(ge=0, le=8)
    memo_quality: float = Field(ge=0, le=4)


class BenchmarkScore(BaseModel):
    model_config = ConfigDict(extra="forbid")
    total: float = Field(ge=0, le=100)
    epistemics: float = Field(ge=0, le=60)
    collection: float = Field(ge=0, le=20)
    policy: float = Field(ge=0, le=20)
    breakdown: ScoreBreakdown
    automation_coverage: float = Field(ge=0, le=1)
    human_review_items: list[str]
    diagnostics: dict[str, object]


def _brier_components(case: ScenarioCase, response: RoundResponse) -> tuple[float, float]:
    truth = case.world_bible.resolved_hypothesis
    multi = (
        sum(
            (assessment.probability - (1.0 if assessment.id == truth else 0.0)) ** 2
            for assessment in response.hypotheses
        )
        / 2.0
    )
    outcomes = {item.id: item.outcome for item in case.forecasts}
    binary = sum(
        (assessment.probability - outcomes[assessment.id]) ** 2 for assessment in response.forecasts
    ) / len(response.forecasts)
    return multi, binary


def _forecast_score(case: ScenarioCase, responses: list[RoundResponse]) -> tuple[float, float]:
    weighted_loss = 0.0
    for response in responses:
        multi, binary = _brier_components(case, response)
        weighted_loss += ROUND_WEIGHTS[response.round] * (0.4 * multi + 0.6 * binary)
    # A uniform four-way hypothesis distribution and 0.5 binary forecasts have a
    # blended loss of .30. Score skill relative to that baseline so an uninformed
    # response no longer receives most of the forecast points.
    skill = max(0.0, min(1.0, 1.0 - weighted_loss / UNINFORMED_BRIER_LOSS))
    return 25.0 * skill, weighted_loss


def _relation_f1(expected: set[tuple[str, str, str]], actual: set[tuple[str, str, str]]) -> float:
    if not expected and not actual:
        return 1.0
    true_positive = len(expected & actual)
    precision = true_positive / len(actual) if actual else 0.0
    recall = true_positive / len(expected) if expected else 0.0
    return 2 * precision * recall / (precision + recall) if precision + recall else 0.0


def _evidence_score(case: ScenarioCase, responses: list[RoundResponse]) -> float:
    evidence = case.evidence_by_id()
    scores: list[float] = []
    selected_ids: set[str] = set()
    for response in responses:
        visible = {item.id for item in case.visible_evidence(response.round, selected_ids)}
        expected_relations = {
            (hypothesis_id, evidence_id, direction)
            for evidence_id in visible
            for hypothesis_id in case.evidence_by_id()[evidence_id].supports
            for direction in ["supports"]
        } | {
            (hypothesis_id, evidence_id, direction)
            for evidence_id in visible
            for hypothesis_id in case.evidence_by_id()[evidence_id].contradicts
            for direction in ["contradicts"]
        }
        actual_relations = {
            (item.id, evidence_id, "supports")
            for item in response.hypotheses
            for evidence_id in item.supporting_evidence_ids
        } | {
            (item.id, evidence_id, "contradicts")
            for item in response.hypotheses
            for evidence_id in item.contradicting_evidence_ids
        }
        relation_score = _relation_f1(expected_relations, actual_relations)

        source_scores: list[float] = []
        group_counts = Counter(evidence[eid].correlation_group for eid in visible)
        submitted_sources = {
            assessment.evidence_id: assessment for assessment in response.source_assessments
        }
        for evidence_id in visible:
            assessment = submitted_sources.get(evidence_id)
            if assessment is None:
                source_scores.append(0.0)
                continue
            target = evidence[evidence_id]
            independence_target = 1.0 if group_counts[target.correlation_group] == 1 else 0.4
            source_scores.append(
                1.0
                - (
                    abs(assessment.reliability - target.reliability)
                    + abs(assessment.deception_risk - target.deception_risk)
                    + abs(assessment.independence - independence_target)
                    + abs(assessment.relevance - 1.0)
                )
                / 4.0
            )
        source_score = sum(source_scores) / len(source_scores) if source_scores else 0.0
        scores.append(0.65 * relation_score + 0.35 * source_score)
        selected_ids.update(order.action_id for order in response.collection_orders)
    return 15.0 * sum(scores) / len(scores)


def _rubric_scores(
    case: ScenarioCase,
    responses: list[RoundResponse],
    decisions: dict[str, ValidationDecision] | None,
) -> tuple[dict[str, float], list[str], float]:
    scores: dict[str, float] = {}
    human_review: list[str] = []
    automated = 0
    for rubric in case.rubric:
        evaluation_response = responses[1] if rubric.dimension == "alternatives" else responses[-1]
        decision = decisions.get(rubric.id) if decisions else None
        if decision and decision.status == ValidationStatus.accepted and decision.score is not None:
            scores[rubric.id] = decision.score
            automated += 1
        elif decision:
            scores[rubric.id] = 0.0
            human_review.append(rubric.id)
        else:
            screen = deterministic_topic_screen(evaluation_response, rubric)
            if screen.label.value == "fail" and screen.confidence >= 0.9:
                scores[rubric.id] = 0.0
                automated += 1
            else:
                # Candidate retrieval and lexical screening never award points. The item
                # remains scoreless until an accepted judge cascade or human label exists.
                scores[rubric.id] = 0.0
                human_review.append(rubric.id)
    coverage = automated / len(case.rubric) if case.rubric else 1.0
    return scores, human_review, coverage


def _average_dimension(case: ScenarioCase, scores: dict[str, float], dimension: str) -> float:
    values = [scores[item.id] for item in case.rubric if item.dimension == dimension]
    return sum(values) / len(values) if values else 0.0


def _consistency_violations(case: ScenarioCase, responses: list[RoundResponse]) -> list[str]:
    del case
    violations: list[str] = []
    for response in responses:
        if len({item.evidence_id for item in response.source_assessments}) != len(
            response.source_assessments
        ):
            violations.append(f"round_{response.round}:duplicate_source_assessment")
        if len({item.id for item in response.hypotheses}) != 4:
            violations.append(f"round_{response.round}:duplicate_hypothesis_id")
        if len({item.id for item in response.forecasts}) != 6:
            violations.append(f"round_{response.round}:duplicate_forecast_id")
    return violations


def _collection_scores(case: ScenarioCase, responses: list[RoundResponse]) -> tuple[float, float]:
    value_ratios: list[float] = []
    coverage_scores: list[float] = []
    for response in responses[:2]:
        prior = {item.id: item.probability for item in response.hypotheses}
        available = case.actions_for_round(response.round)
        selected_ids = {order.action_id for order in response.collection_orders}
        selected = [action for action in available if action.id in selected_ids]
        budget = case.manifest.collection_budgets[response.round]
        _, own_optimum = optimal_collection_portfolio(available, prior, budget)
        own_actual = portfolio_information_gain(selected, prior)
        own_ratio = own_actual / own_optimum if own_optimum else 1.0
        uniform_prior = {item.id: 1.0 / len(case.hypotheses) for item in case.hypotheses}
        _, robust_optimum = optimal_collection_portfolio(available, uniform_prior, budget)
        robust_actual = portfolio_information_gain(selected, uniform_prior)
        robust_ratio = robust_actual / robust_optimum if robust_optimum else 1.0
        value_ratios.append(0.5 * own_ratio + 0.5 * robust_ratio)
        if selected:
            diversity = len({item.correlation_group for item in selected}) / len(selected)
            spend = sum(item.cost for item in selected) / budget
            coverage_scores.append(0.7 * diversity + 0.3 * min(1.0, spend))
        else:
            coverage_scores.append(0.0)
    return 15.0 * sum(value_ratios) / 2.0, 5.0 * sum(coverage_scores) / 2.0


def _policy_scores(
    case: ScenarioCase, response: RoundResponse, rubric_scores: dict[str, float]
) -> tuple[float, float, float, list[dict[str, object]]]:
    allocations = {item.action_id: item.allocation / 100.0 for item in response.policy_actions}
    consequences_by_action: dict[str, list[float]] = {}
    for consequence in case.policy_consequences:
        desirability = (
            consequence.probability_if_selected
            if consequence.desirable
            else 1.0 - consequence.probability_if_selected
        )
        consequences_by_action.setdefault(consequence.action_id, []).append(desirability)
    consequence_score = 0.0
    for action_id, allocation in allocations.items():
        values = consequences_by_action.get(action_id, [0.5])
        consequence_score += allocation * sum(values) / len(values)

    weighted_task_total = 0.0
    task_weight_total = 0.0
    task_diagnostics: list[dict[str, object]] = []
    for task in case.critical_tasks:
        positive_allocation = sum(
            allocations.get(action_id, 0.0) for action_id in task.positive_action_ids
        )
        prohibited_allocation = sum(
            allocations.get(action_id, 0.0) for action_id in task.prohibited_action_ids
        )
        positive_progress = (
            1.0
            if not task.positive_action_ids
            else min(1.0, positive_allocation / task.minimum_allocation)
        )
        prohibited_penalty = min(1.0, prohibited_allocation / 0.10)
        value = max(0.0, positive_progress * (1.0 - prohibited_penalty))
        weight = 2.0 if task.critical else 1.0
        weighted_task_total += weight * value
        task_weight_total += weight
        task_diagnostics.append(
            {
                "task_id": task.id,
                "minimum_allocation": task.minimum_allocation,
                "positive_allocation": positive_allocation,
                "prohibited_allocation": prohibited_allocation,
                "score": value,
            }
        )
    task_score = weighted_task_total / task_weight_total if task_weight_total else 0.0
    policy_rubric = _average_dimension(case, rubric_scores, "policy")
    memo_rubric = _average_dimension(case, rubric_scores, "memo")
    return (
        8.0 * consequence_score,
        8.0 * (0.6 * task_score + 0.4 * policy_rubric),
        4.0 * memo_rubric,
        task_diagnostics,
    )


def score_session(
    case: ScenarioCase,
    responses: list[RoundResponse],
    rubric_decisions: list[ValidationDecision] | None = None,
) -> BenchmarkScore:
    validate_session(case, responses)
    decisions = {item.rubric_id: item for item in rubric_decisions or []}
    rubric_scores, human_review, coverage = _rubric_scores(case, responses, decisions)

    forecast, weighted_brier = _forecast_score(case, responses)
    evidence = _evidence_score(case, responses)
    strategic_reasoning = 20.0 * _average_dimension(case, rubric_scores, "alternatives")
    consistency_violations = _consistency_violations(case, responses)
    collection_value, collection_coverage = _collection_scores(case, responses)
    policy_consequences, policy_tasks, memo_quality, policy_task_diagnostics = _policy_scores(
        case, responses[-1], rubric_scores
    )

    epistemics = forecast + evidence + strategic_reasoning
    collection = collection_value + collection_coverage
    policy = policy_consequences + policy_tasks + memo_quality
    breakdown = ScoreBreakdown(
        forecast_accuracy=forecast,
        evidence_handling=evidence,
        strategic_reasoning=strategic_reasoning,
        collection_value=collection_value,
        collection_coverage=collection_coverage,
        policy_consequences=policy_consequences,
        policy_tasks=policy_tasks,
        memo_quality=memo_quality,
    )
    return BenchmarkScore(
        total=epistemics + collection + policy,
        epistemics=epistemics,
        collection=collection,
        policy=policy,
        breakdown=breakdown,
        automation_coverage=coverage,
        human_review_items=human_review,
        diagnostics={
            "weighted_brier_loss": weighted_brier,
            "forecast_skill_vs_uninformed": max(
                0.0, min(1.0, 1.0 - weighted_brier / UNINFORMED_BRIER_LOSS)
            ),
            "uninformed_brier_loss": UNINFORMED_BRIER_LOSS,
            "forecast_trajectory": [
                {
                    "round": response.round,
                    "multiclass_brier": _brier_components(case, response)[0],
                    "binary_brier": _brier_components(case, response)[1],
                    "resolved_hypothesis_probability": next(
                        item.probability
                        for item in response.hypotheses
                        if item.id == case.world_bible.resolved_hypothesis
                    ),
                }
                for response in responses
            ],
            "rubric_items": len(case.rubric),
            "human_review_count": len(human_review),
            "consistency_violations": consistency_violations,
            "policy_task_allocations": policy_task_diagnostics,
            "deterministic_points_available": 72.8,
        },
    )
