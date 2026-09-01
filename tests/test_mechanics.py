from __future__ import annotations

import pytest

from strategic_surprise_bench.mechanics import (
    ResponseValidationError,
    optimal_collection_portfolio,
    portfolio_information_gain,
    validate_round_response,
    validate_session,
)
from strategic_surprise_bench.models import CollectionOrder


def test_optimal_collection_is_budgeted_and_prior_dependent(lattice):
    truth = lattice.world_bible.resolved_hypothesis
    prior = {item.id: (0.7 if item.id == truth else 0.1) for item in lattice.hypotheses}
    actions, value = optimal_collection_portfolio(
        lattice.actions_for_round(1), prior, lattice.manifest.collection_budgets[1]
    )
    assert sum(item.cost for item in actions) <= 10
    assert value == portfolio_information_gain(actions, prior)
    assert value > 0


def test_correlated_collection_is_not_double_counted(lattice):
    prior = {item.id: 0.25 for item in lattice.hypotheses}
    actions = lattice.actions_for_round(1)
    first = actions[0].model_copy(deep=True)
    second = actions[1].model_copy(deep=True)
    second.correlation_group = first.correlation_group
    grouped = (first, second)
    pair_value = portfolio_information_gain(list(grouped), prior)
    assert pair_value == max(
        portfolio_information_gain([grouped[0]], prior),
        portfolio_information_gain([grouped[1]], prior),
    )


def test_unavailable_evidence_is_rejected(perfect_session, lattice):
    response = perfect_session[0].model_copy(deep=True)
    response.findings[0].evidence_ids = [lattice.rounds[2].common_evidence_ids[0]]
    with pytest.raises(ResponseValidationError, match="not visible"):
        validate_round_response(lattice, response)


def test_hallucinated_evidence_id_is_rejected(perfect_session, lattice):
    response = perfect_session[0].model_copy(deep=True)
    response.findings[0].evidence_ids = ["E-NOT-A-REAL-SOURCE"]
    with pytest.raises(ResponseValidationError, match="unknown evidence"):
        validate_round_response(lattice, response)


def test_budget_violation_is_rejected(perfect_session, lattice):
    response = perfect_session[0].model_copy(deep=True)
    response.collection_orders = [
        CollectionOrder(
            action_id=item.id,
            purpose=item.description,
            discriminates_hypotheses=list(item.likelihood_positive),
        )
        for item in lattice.actions_for_round(1)
    ]
    with pytest.raises(ResponseValidationError, match="budget"):
        validate_round_response(lattice, response)


def test_perfect_fixture_is_a_valid_session(perfect_session, lattice):
    validated = validate_session(lattice, perfect_session)
    assert [item.response.round for item in validated] == [1, 2, 3]
