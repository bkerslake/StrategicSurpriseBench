"""Closed-world collection mechanics and response validation."""

from __future__ import annotations

import itertools
import math
from dataclasses import dataclass

from strategic_surprise_bench.models import CollectionAction, RoundResponse, ScenarioCase


class ResponseValidationError(ValueError):
    """Raised when a structurally valid response violates a case-specific rule."""


def binary_entropy(probability: float) -> float:
    if probability <= 0.0 or probability >= 1.0:
        return 0.0
    return -probability * math.log2(probability) - (1.0 - probability) * math.log2(
        1.0 - probability
    )


def action_information_gain(action: CollectionAction, prior: dict[str, float]) -> float:
    positive_probability = sum(
        prior[hypothesis_id] * likelihood
        for hypothesis_id, likelihood in action.likelihood_positive.items()
    )
    expected_conditional_entropy = sum(
        prior[hypothesis_id] * binary_entropy(likelihood)
        for hypothesis_id, likelihood in action.likelihood_positive.items()
    )
    return max(0.0, binary_entropy(positive_probability) - expected_conditional_entropy)


def portfolio_information_gain(actions: list[CollectionAction], prior: dict[str, float]) -> float:
    """Approximate joint value without double counting correlated collection."""
    best_by_group: dict[str, float] = {}
    for action in actions:
        value = action_information_gain(action, prior)
        best_by_group[action.correlation_group] = max(
            value, best_by_group.get(action.correlation_group, 0.0)
        )
    return sum(best_by_group.values())


def optimal_collection_portfolio(
    actions: list[CollectionAction], prior: dict[str, float], budget: int
) -> tuple[list[CollectionAction], float]:
    best_actions: list[CollectionAction] = []
    best_value = 0.0
    for count in range(len(actions) + 1):
        for candidate in itertools.combinations(actions, count):
            if sum(action.cost for action in candidate) > budget:
                continue
            value = portfolio_information_gain(list(candidate), prior)
            if value > best_value + 1e-12:
                best_actions = list(candidate)
                best_value = value
    return best_actions, best_value


@dataclass(frozen=True)
class ValidatedRound:
    response: RoundResponse
    visible_evidence_ids: frozenset[str]
    selected_actions: tuple[CollectionAction, ...]
    collection_cost: int


def validate_round_response(
    case: ScenarioCase,
    response: RoundResponse,
    prior_selected_action_ids: set[str] | None = None,
) -> ValidatedRound:
    prior_selected_action_ids = prior_selected_action_ids or set()
    hypothesis_ids = {item.id for item in case.hypotheses}
    forecast_ids = {item.id for item in case.forecasts}
    response_hypothesis_ids = [item.id for item in response.hypotheses]
    response_forecast_ids = [item.id for item in response.forecasts]
    if set(response_hypothesis_ids) != hypothesis_ids or len(response_hypothesis_ids) != 4:
        raise ResponseValidationError("response hypothesis IDs must exactly match the case")
    if set(response_forecast_ids) != forecast_ids or len(response_forecast_ids) != 6:
        raise ResponseValidationError("response forecast IDs must exactly match the case")

    visible_ids = {
        item.id for item in case.visible_evidence(response.round, prior_selected_action_ids)
    }
    cited_ids: set[str] = set()
    for item in response.hypotheses:
        cited_ids.update(item.supporting_evidence_ids)
        cited_ids.update(item.contradicting_evidence_ids)
    for item in response.findings:
        cited_ids.update(item.evidence_ids)
    cited_ids.update(item.evidence_id for item in response.source_assessments)
    unknown_evidence = cited_ids - set(case.evidence_by_id())
    if unknown_evidence:
        raise ResponseValidationError(
            f"response cites unknown evidence IDs: {sorted(unknown_evidence)}"
        )
    unavailable = cited_ids - visible_ids
    if unavailable:
        raise ResponseValidationError(
            f"response cites evidence not visible in round {response.round}: {sorted(unavailable)}"
        )

    if response.round in (1, 2):
        available_actions = {item.id: item for item in case.actions_for_round(response.round)}
        order_ids = [item.action_id for item in response.collection_orders]
        if len(order_ids) != len(set(order_ids)):
            raise ResponseValidationError("collection orders must be unique")
        unknown = set(order_ids) - set(available_actions)
        if unknown:
            raise ResponseValidationError(f"unknown collection actions: {sorted(unknown)}")
        selected = tuple(available_actions[action_id] for action_id in order_ids)
        cost = sum(item.cost for item in selected)
        budget = case.manifest.collection_budgets[response.round]
        if cost > budget:
            raise ResponseValidationError(
                f"collection costs {cost} but the round budget is {budget}"
            )
    else:
        selected = ()
        cost = 0
        policy_ids = {item.id for item in case.policy_levers}
        submitted_policy_ids = [item.action_id for item in response.policy_actions]
        if len(submitted_policy_ids) != len(set(submitted_policy_ids)):
            raise ResponseValidationError("policy action IDs must be unique")
        unknown = set(submitted_policy_ids) - policy_ids
        if unknown:
            raise ResponseValidationError(f"unknown policy actions: {sorted(unknown)}")

    return ValidatedRound(
        response=response,
        visible_evidence_ids=frozenset(visible_ids),
        selected_actions=selected,
        collection_cost=cost,
    )


def validate_session(case: ScenarioCase, responses: list[RoundResponse]) -> list[ValidatedRound]:
    if [response.round for response in responses] != [1, 2, 3]:
        raise ResponseValidationError("a session must contain responses for rounds 1, 2, and 3")
    selected: set[str] = set()
    validated: list[ValidatedRound] = []
    for response in responses:
        round_result = validate_round_response(case, response, selected)
        validated.append(round_result)
        selected.update(action.id for action in round_result.selected_actions)
    return validated
