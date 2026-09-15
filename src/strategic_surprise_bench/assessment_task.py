"""Inspect runner: two neutral prose requests, no target tools or response schema."""

from __future__ import annotations

from inspect_ai import Epochs, Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageUser, GenerateConfig
from inspect_ai.scorer import (
    Metric,
    SampleScore,
    Score,
    ScoreReducer,
    metric,
    score_reducer,
    scorer,
)
from inspect_ai.solver import Generate, Solver, TaskState, solver, system_message

from strategic_surprise_bench.assessment import (
    SYSTEM,
    VERSION,
    AssessmentTranscript,
    list_assessment_cases,
    load_assessment_case,
    render_assessment,
)
from strategic_surprise_bench.assessment_scoring import (
    DEFAULT_JUDGE_ATTEMPTS,
    judge_assessment,
    score_assessment,
)


@score_reducer
def preserve_missing() -> ScoreReducer:
    """Inspect's standard mean reducer maps nonnumeric labels to zero; we must not."""

    def reduce(scores: list[Score]) -> Score:
        values = [score.value for score in scores]
        complete = bool(values) and all(isinstance(value, (int, float)) for value in values)
        return Score(value=sum(values) / len(values) if complete else "U")

    return reduce


@metric
def complete_assessment_mean() -> Metric:
    """Never turn an ungraded sample into zero. The unqualified mean needs every sample graded;
    the mean over graded samples is reported under an explicit name with its sample count."""

    def compute(scores: list[SampleScore]) -> dict[str, float]:
        values = [item.score.value for item in scores]
        numeric = [value for value in values if isinstance(value, (int, float))]
        result = {
            "graded_fraction": len(numeric) / len(values) if values else 0.0,
            "graded_samples": float(len(numeric)),
        }
        if numeric:
            result["mean_of_graded_samples_out_of_10"] = sum(numeric) / len(numeric)
        if values and len(numeric) == len(values):
            result["mean_out_of_10"] = sum(numeric) / len(numeric)
        return result

    return compute


@solver
def assessment_session() -> Solver:
    async def solve(state: TaskState, generate: Generate) -> TaskState:
        case = load_assessment_case(state.metadata["case_id"])
        variant = state.metadata["variant"]
        state.tools = []
        responses = []
        issues = []
        for stage in (1, 2):
            if stage == 2:
                state.messages.append(
                    ChatMessageUser(
                        content=render_assessment(case, 2, variant),
                    )
                )
            state = await generate(state)
            responses.append(state.output.completion)
            for choice in state.output.choices:
                if choice.stop_reason in {"max_tokens", "content_filter"}:
                    issues.append({"stage": stage, "stop_reason": choice.stop_reason})
        transcript = AssessmentTranscript(
            case_id=case.id,
            variant=variant,
            responses=responses,
            generation_issues=issues,
        )
        state.metadata["assessment_transcript"] = transcript.model_dump()
        state.metadata["generation_issues"] = issues
        return state

    return solve


@scorer(metrics=[complete_assessment_mean()])
def assessment_scorer(judge: str | None = None, judge_attempts: int = DEFAULT_JUDGE_ATTEMPTS):
    async def score(state: TaskState, target: object) -> Score:
        del target
        transcript = AssessmentTranscript.model_validate(state.metadata["assessment_transcript"])
        sheet = None
        # Truncated/filtered target calls are execution issues, not confirmed analytical failures.
        if judge and not state.metadata.get("generation_issues"):
            sheet = await judge_assessment(transcript, judge, attempts=judge_attempts)
        result = score_assessment(transcript, sheet)
        return Score(
            value=result["total"] if result["total"] is not None else "U",
            answer=transcript.responses[-1],
            explanation=(
                "Provisional model grading; human review is needed for validation."
                if sheet
                else "Ungraded. Export the transcript for human review."
            ),
            metadata={
                **result,
                "assessment_transcript": transcript.model_dump(),
                "grade_sheet": sheet.model_dump() if sheet else None,
                "generation_issues": state.metadata.get("generation_issues", []),
            },
        )

    return score


@task
def strategic_surprise(
    case_id: str | None = None,
    variant: str = "both",
    judge: str | None = None,
    max_tokens: int = 4096,
    judge_attempts: int = DEFAULT_JUDGE_ATTEMPTS,
) -> Task:
    """v0.3: spontaneous strategic assessment, with optional provisional single-model grading."""
    if variant not in {"a", "b", "both"}:
        raise ValueError("variant must be a, b, or both")
    if max_tokens < 1:
        raise ValueError("max_tokens must be positive")
    if judge_attempts < 1:
        raise ValueError("judge_attempts must be positive")
    cases = [
        load_assessment_case(item) for item in ([case_id] if case_id else list_assessment_cases())
    ]
    variants = ("a", "b") if variant == "both" else (variant,)
    dataset = [
        Sample(
            id=f"{case.id}_{item}",
            input=render_assessment(case, 1),
            metadata={"case_id": case.id, "variant": item},
        )
        for case in cases
        for item in variants
    ]
    return Task(
        dataset=dataset,
        setup=system_message(SYSTEM),
        solver=assessment_session(),
        scorer=assessment_scorer(judge, judge_attempts),
        config=GenerateConfig(max_tokens=max_tokens),
        epochs=Epochs(1, reducer=preserve_missing()),
        message_limit=6,
        version=VERSION,
        metadata={
            "benchmark_version": VERSION,
            "protocol": "unprompted_assessment",
            "judge": judge,
            "judge_attempts_per_stage": judge_attempts if judge else None,
            "grading": "provisional" if judge else "human_pending",
            "variants": list(variants),
            "target_calls_per_sample": 2,
        },
    )
