"""Public API for v0.3. Legacy contracts remain in their original submodules."""

from strategic_surprise_bench.assessment import (
    AssessmentCase,
    AssessmentTranscript,
    GradeSheet,
    list_assessment_cases,
    load_assessment_case,
    render_assessment,
)
from strategic_surprise_bench.assessment_scoring import score_assessment
from strategic_surprise_bench.versions import BENCHMARK_VERSION

__all__ = [
    "AssessmentCase",
    "AssessmentTranscript",
    "GradeSheet",
    "list_assessment_cases",
    "load_assessment_case",
    "render_assessment",
    "score_assessment",
]

__version__ = BENCHMARK_VERSION
