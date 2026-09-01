"""Strategic Surprise Bench public API."""

from strategic_surprise_bench.loader import list_case_ids, load_all_cases, load_case
from strategic_surprise_bench.models import RoundResponse, ScenarioCase
from strategic_surprise_bench.scoring import BenchmarkScore, score_session
from strategic_surprise_bench.versions import BENCHMARK_VERSION

__all__ = [
    "BenchmarkScore",
    "RoundResponse",
    "ScenarioCase",
    "list_case_ids",
    "load_all_cases",
    "load_case",
    "score_session",
]

__version__ = BENCHMARK_VERSION
