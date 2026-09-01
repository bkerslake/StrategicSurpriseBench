from __future__ import annotations

import pytest

from strategic_surprise_bench.loader import load_all_cases
from strategic_surprise_bench.mock import make_mock_session
from strategic_surprise_bench.scoring import score_session


@pytest.mark.parametrize("case", load_all_cases(), ids=lambda case: case.manifest.id)
def test_golden_score_ordering(case):
    scores = {
        quality: score_session(case, make_mock_session(case, quality)).total
        for quality in ("perfect", "calibrated", "uniform", "wrong")
    }
    assert scores["perfect"] > scores["calibrated"] > scores["uniform"] > scores["wrong"]
    assert scores["perfect"] >= 65
    assert scores["calibrated"] - scores["uniform"] >= 45
    assert scores["uniform"] - scores["wrong"] >= 5


def test_non_updating_transcript_scores_below_calibrated(lattice):
    calibrated = make_mock_session(lattice, "calibrated")
    non_updating = make_mock_session(lattice, "calibrated")
    initial_hypotheses = {
        item.id: item.probability for item in non_updating[0].hypotheses
    }
    initial_forecasts = {item.id: item.probability for item in non_updating[0].forecasts}
    for response in non_updating[1:]:
        for item in response.hypotheses:
            item.probability = initial_hypotheses[item.id]
        for item in response.forecasts:
            item.probability = initial_forecasts[item.id]
    assert score_session(lattice, non_updating).total < score_session(lattice, calibrated).total


def test_open_rubrics_fail_closed_until_review(lattice, perfect_session):
    result = score_session(lattice, perfect_session)
    assert result.automation_coverage == 0
    assert set(result.human_review_items) == {item.id for item in lattice.rubric}
    assert result.breakdown.strategic_reasoning == 0
    assert result.breakdown.memo_quality == 0


def test_accepted_adjudicated_rubrics_complete_score(
    lattice, perfect_session, accepted_rubric_decisions
):
    result = score_session(lattice, perfect_session, accepted_rubric_decisions)
    assert result.automation_coverage == 1
    assert result.human_review_items == []
    assert result.breakdown.strategic_reasoning == 20
    assert result.breakdown.memo_quality == 4
    assert result.total > 94
    assert result.total == pytest.approx(result.epistemics + result.collection + result.policy)


def test_uninformed_forecasts_receive_no_forecast_skill(lattice):
    result = score_session(lattice, make_mock_session(lattice, "uniform"))
    assert result.breakdown.forecast_accuracy == 0
    assert result.diagnostics["forecast_skill_vs_uninformed"] == 0


def test_token_policy_allocations_do_not_complete_tasks(lattice, perfect_session):
    strong = score_session(lattice, perfect_session)
    token = make_mock_session(lattice, "perfect")
    for action in token[-1].policy_actions:
        action.allocation = 1
    prohibited = token[-1].policy_actions[0].model_copy(
        update={"action_id": "LS-P04", "allocation": 100 - len(token[-1].policy_actions)}
    )
    token[-1].policy_actions.append(prohibited)
    weak = score_session(lattice, token)
    assert weak.breakdown.policy_tasks < strong.breakdown.policy_tasks / 2


def test_consistency_is_diagnostic_not_a_point_bucket(lattice, perfect_session):
    result = score_session(lattice, perfect_session)
    assert "consistency" not in result.breakdown.model_dump()
    assert result.diagnostics["consistency_violations"] == []
