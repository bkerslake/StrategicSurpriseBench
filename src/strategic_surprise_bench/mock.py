"""Credential-free mock transcripts for golden and end-to-end tests."""

from __future__ import annotations

from collections import Counter

from strategic_surprise_bench.mechanics import optimal_collection_portfolio
from strategic_surprise_bench.models import (
    CollectionOrder,
    Confidence,
    Finding,
    ForecastAssessment,
    GeneratedHypothesis,
    HypothesisAssessment,
    PolicyAction,
    RoundResponse,
    ScenarioCase,
    SourceAssessment,
)


def _probabilities(case: ScenarioCase, round_number: int, quality: str) -> dict[str, float]:
    ids = [item.id for item in case.hypotheses]
    truth = case.world_bible.resolved_hypothesis
    wrong = next(item for item in ids if item != truth)
    if quality == "uniform":
        return {item: 0.25 for item in ids}
    if quality == "wrong":
        confidence = {1: 0.72, 2: 0.84, 3: 0.94}[round_number]
        remaining = (1.0 - confidence) / 3.0
        return {item: confidence if item == wrong else remaining for item in ids}
    truth_probability = {
        "calibrated": {1: 0.42, 2: 0.64, 3: 0.82},
        "perfect": {1: 0.62, 2: 0.84, 3: 0.97},
    }[quality][round_number]
    remaining = (1.0 - truth_probability) / 3.0
    return {item: truth_probability if item == truth else remaining for item in ids}


def _forecast_probability(outcome: int, round_number: int, quality: str) -> float:
    accuracy = {
        "perfect": {1: 0.84, 2: 0.92, 3: 0.98},
        "calibrated": {1: 0.66, 2: 0.76, 3: 0.86},
        "uniform": {1: 0.50, 2: 0.50, 3: 0.50},
        "wrong": {1: 0.16, 2: 0.10, 3: 0.04},
    }[quality][round_number]
    return accuracy if outcome else 1.0 - accuracy


def _policy_actions(case: ScenarioCase, quality: str) -> list[PolicyAction]:
    if quality == "wrong":
        prohibited = [
            action_id for task in case.critical_tasks for action_id in task.prohibited_action_ids
        ]
        selected = prohibited[:1] or [case.policy_levers[-1].id]
    elif quality == "uniform":
        selected = [case.policy_levers[0].id]
    else:
        selected = list(
            dict.fromkeys(
                action_id
                for task in case.critical_tasks
                for action_id in task.positive_action_ids
                if all(action_id not in item.prohibited_action_ids for item in case.critical_tasks)
            )
        )
    base, remainder = divmod(100, len(selected))
    by_id = {item.id: item for item in case.policy_levers}
    return [
        PolicyAction(
            action_id=action_id,
            allocation=base + (1 if index < remainder else 0),
            objective=f"Meet case-critical tasks through {by_id[action_id].label}.",
            mechanism=by_id[action_id].description,
            risks=["Execution could produce unintended second-order effects."],
            affected_domains=by_id[action_id].affected_domains,
            triggers=["Escalate, reverse, or reallocate if the cited warning evidence changes."],
        )
        for index, action_id in enumerate(selected)
    ]


def make_mock_session(case: ScenarioCase, quality: str = "perfect") -> list[RoundResponse]:
    """Create a valid transcript. It is a test fixture, never an expert label."""
    if quality not in {"perfect", "calibrated", "uniform", "wrong"}:
        raise ValueError("quality must be perfect, calibrated, uniform, or wrong")

    selected_ids: set[str] = set()
    responses: list[RoundResponse] = []
    for round_number in (1, 2, 3):
        probabilities = _probabilities(case, round_number, quality)
        visible = case.visible_evidence(round_number, selected_ids)
        visible_ids = {item.id for item in visible}
        group_counts = Counter(item.correlation_group for item in visible)

        hypotheses: list[HypothesisAssessment] = []
        for definition in case.hypotheses:
            supporting = (
                [item.id for item in visible if definition.id in item.supports]
                if quality in {"perfect", "calibrated"}
                else []
            )
            contradicting = (
                [item.id for item in visible if definition.id in item.contradicts]
                if quality in {"perfect", "calibrated"}
                else []
            )
            hypotheses.append(
                HypothesisAssessment(
                    id=definition.id,
                    probability=probabilities[definition.id],
                    confidence=(
                        Confidence.high
                        if round_number == 3 and quality == "perfect"
                        else Confidence.medium
                    ),
                    supporting_evidence_ids=supporting,
                    contradicting_evidence_ids=contradicting,
                )
            )

        source_assessments = (
            [
                SourceAssessment(
                    evidence_id=item.id,
                    reliability=item.reliability,
                    independence=1.0 if group_counts[item.correlation_group] == 1 else 0.4,
                    deception_risk=item.deception_risk,
                    relevance=0.9,
                )
                for item in visible
            ]
            if quality in {"perfect", "calibrated"}
            else []
        )

        generated_hypotheses: list[GeneratedHypothesis] = []
        by_hypothesis = {item.id: item for item in case.hypotheses}
        for slot_id in ("H2", "H3"):
            definition = by_hypothesis[slot_id]
            supporting_ids = [item.id for item in visible if slot_id in item.supports]
            if quality in {"perfect", "calibrated"}:
                statement = f"{definition.label}: {definition.description}"
                mechanism = " -> ".join(case.world_bible.causal_pathway)
                incentives = [
                    f"{actor}: {motive}"
                    for actor, motive in list(case.world_bible.actor_motives.items())[:2]
                ]
                expected = [
                    f"Evidence {item.id} should be observed: {item.text}"
                    for item in visible
                    if slot_id in item.supports
                ][:3] or ["The causal pathway should produce an independently observable trace."]
                disconfirming = [
                    f"Evidence {item.id} cuts against this slot: {item.text}"
                    for item in visible
                    if slot_id in item.contradicts
                ][:3] or ["Independent evidence tying every event to one cause would weaken it."]
                second_order = [
                    "Attention and policy resources shift toward the vivid headline while the "
                    "quieter pathway compounds."
                ]
                counterfactual = (
                    "If the headline single-actor account were true, independent implementation "
                    "and "
                    "timing evidence would converge instead of separating into these causal layers."
                )
            else:
                statement = f"Generic alternative for {slot_id}."
                mechanism = "The visible events may share an unspecified cause."
                incentives = ["Actors generally prefer favorable outcomes."]
                expected = ["More activity may occur."]
                disconfirming = ["No additional activity may occur."]
                second_order = ["There may be unspecified downstream effects."]
                counterfactual = "A different world could produce different observations."
                supporting_ids = []
            generated_hypotheses.append(
                GeneratedHypothesis(
                    slot_id=slot_id,
                    statement=statement,
                    causal_mechanism=mechanism,
                    actor_incentives=incentives,
                    expected_observables=expected,
                    disconfirming_observables=disconfirming,
                    second_order_effects=second_order,
                    counterfactual=counterfactual,
                    evidence_ids=supporting_ids,
                )
            )

        collection_orders: list[CollectionOrder] = []
        if round_number < 3 and quality in {"perfect", "calibrated"}:
            actions, _ = optimal_collection_portfolio(
                case.actions_for_round(round_number),
                probabilities,
                case.manifest.collection_budgets[round_number],
            )
            collection_orders = [
                CollectionOrder(
                    action_id=action.id,
                    purpose=action.description,
                    discriminates_hypotheses=list(action.likelihood_positive),
                )
                for action in actions
            ]

        findings: list[Finding] = []
        if quality in {"perfect", "calibrated"}:
            for rubric in case.rubric:
                allowed = [item for item in rubric.allowed_evidence_ids if item in visible_ids]
                fallback = [item.id for item in visible[:2]]
                evidence_ids = (
                    (allowed[:2] or fallback) if rubric.required_evidence else allowed[:1]
                )
                findings.append(
                    Finding(
                        claim=rubric.required_meaning,
                        evidence_ids=evidence_ids,
                        implication=(
                            f"This satisfies {rubric.criterion.lower()} at the required depth."
                        ),
                        uncertainty=(
                            "The judgment remains conditional on independent evidence and timing."
                        ),
                        alternative_explanation=(
                            "A competing hypothesis remains possible if the cited "
                            "indicators reverse."
                        ),
                    )
                )
        elif quality == "wrong":
            findings = [
                Finding(
                    claim=(
                        "The most vivid allegation should be accepted without "
                        "further qualification."
                    ),
                    implication="Immediate irreversible action is warranted.",
                    uncertainty="None material.",
                    alternative_explanation="Alternatives are dismissed.",
                )
            ]

        memo_parts = [finding.claim for finding in findings]
        if quality in {"perfect", "calibrated"}:
            memo_parts.append(
                "Treat confidence separately from probability; preserve disconfirming indicators, "
                "second-order effects, and explicit reversal conditions."
            )
        decision_memo = " ".join(memo_parts) or "No supported conclusion; maintain a uniform prior."

        response = RoundResponse(
            round=round_number,
            hypotheses=hypotheses,
            generated_hypotheses=generated_hypotheses,
            forecasts=[
                ForecastAssessment(
                    id=item.id,
                    probability=_forecast_probability(item.outcome, round_number, quality),
                )
                for item in case.forecasts
            ],
            findings=findings,
            source_assessments=source_assessments,
            collection_orders=collection_orders,
            policy_actions=_policy_actions(case, quality) if round_number == 3 else [],
            decision_memo=decision_memo,
        )
        responses.append(response)
        selected_ids.update(order.action_id for order in collection_orders)
    return responses


def transcript_payload(case: ScenarioCase, quality: str = "perfect") -> dict:
    return {
        "case_id": case.manifest.id,
        "fixture_only": True,
        "quality": quality,
        "responses": [item.model_dump(mode="json") for item in make_mock_session(case, quality)],
    }
