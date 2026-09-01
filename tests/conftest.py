from __future__ import annotations

import pytest

from strategic_surprise_bench.loader import load_case
from strategic_surprise_bench.mock import make_mock_session
from strategic_surprise_bench.models import (
    JudgeLabel,
    ValidationDecision,
    ValidationStatus,
)


@pytest.fixture
def lattice():
    return load_case("lattice_signal")


@pytest.fixture
def perfect_session(lattice):
    return make_mock_session(lattice, "perfect")


@pytest.fixture
def accepted_rubric_decisions(lattice):
    return [
        ValidationDecision(
            rubric_id=item.id,
            status=ValidationStatus.accepted,
            label=JudgeLabel.pass_,
            score=1.0,
            reason="Adjudicated fixture label.",
        )
        for item in lattice.rubric
    ]
