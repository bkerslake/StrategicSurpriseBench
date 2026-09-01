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
    assert scores["perfect"] >= 79


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
    assert result.breakdown.alternatives == 0
    assert result.breakdown.memo_quality == 0


def test_accepted_adjudicated_rubrics_complete_score(
    lattice, perfect_session, accepted_rubric_decisions
):
    result = score_session(lattice, perfect_session, accepted_rubric_decisions)
    assert result.automation_coverage == 1
    assert result.human_review_items == []
    assert result.breakdown.alternatives == 10
    assert result.breakdown.memo_quality == 4
    assert result.total > 95
    assert result.total == pytest.approx(result.epistemics + result.collection + result.policy)
