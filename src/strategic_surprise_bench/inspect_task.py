"""Inspect task package for Strategic Surprise Bench."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.model import ChatMessageUser, GenerateConfig
from inspect_ai.scorer import Score, mean, scorer
from inspect_ai.solver import Generate, Solver, TaskState, solver, system_message
from pydantic import ValidationError

from strategic_surprise_bench.calibration import gate_allows_automated_scoring
from strategic_surprise_bench.loader import list_case_ids, load_case
from strategic_surprise_bench.mechanics import ResponseValidationError, validate_round_response
from strategic_surprise_bench.models import RoundResponse, ValidationDecision
from strategic_surprise_bench.prompts import (
    AGENT_ADDENDUM,
    SYSTEM_PROMPT,
    render_round_prompt,
    repair_prompt,
)
from strategic_surprise_bench.rubric import InspectJudgeBackend, JudgeCascade
from strategic_surprise_bench.scoring import score_session
from strategic_surprise_bench.tools import bounded_analyst_tools
from strategic_surprise_bench.versions import BENCHMARK_VERSION

Condition = Literal["plain", "agent"]
JudgeMode = Literal["off", "calibration", "published"]
MAX_OUTPUT_TOKENS = 8000
MESSAGE_LIMIT = 80


def _parse_response(text: str) -> RoundResponse:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL)
    try:
        payload = json.loads(cleaned)
    except json.JSONDecodeError:
        start, end = cleaned.find("{"), cleaned.rfind("}")
        if start < 0 or end <= start:
            raise
        payload = json.loads(cleaned[start : end + 1])
    return RoundResponse.model_validate(payload)


@solver
def strategic_session(condition: Condition = "plain") -> Solver:
    """Run all three rounds while preserving contemporaneous submissions."""
    if condition not in {"plain", "agent"}:
        raise ValueError("condition must be 'plain' or 'agent'")

    async def solve(state: TaskState, generate: Generate) -> TaskState:
        case = load_case(str(state.metadata["case_id"]))
        if condition == "agent":
            state.tools = bounded_analyst_tools()
            state.tool_choice = "auto"

        responses: list[RoundResponse] = []
        selected_action_ids: set[str] = set()
        repair_used: list[bool] = []
        for round_number in (1, 2, 3):
            if round_number > 1:
                state.messages.append(
                    ChatMessageUser(
                        content=render_round_prompt(case, round_number, selected_action_ids)
                    )
                )
            state = await generate(
                state,
                temperature=0.2,
                max_tokens=MAX_OUTPUT_TOKENS,
            )
            try:
                response = _parse_response(state.output.completion)
                validate_round_response(case, response, selected_action_ids)
                repaired = False
            except (json.JSONDecodeError, ValidationError, ResponseValidationError) as error:
                state.messages.append(ChatMessageUser(content=repair_prompt(str(error))))
                state = await generate(
                    state,
                    temperature=0.2,
                    max_tokens=MAX_OUTPUT_TOKENS,
                )
                try:
                    response = _parse_response(state.output.completion)
                    validate_round_response(case, response, selected_action_ids)
                    repaired = True
                except (
                    json.JSONDecodeError,
                    ValidationError,
                    ResponseValidationError,
                ) as final_error:
                    state.metadata["round_responses"] = [
                        item.model_dump(mode="json") for item in responses
                    ]
                    state.metadata["schema_failure_round"] = round_number
                    state.metadata["schema_failure"] = str(final_error)
                    return state
            if response.round != round_number:
                state.metadata["round_responses"] = [
                    item.model_dump(mode="json") for item in responses
                ]
                state.metadata["schema_failure_round"] = round_number
                state.metadata["schema_failure"] = (
                    f"expected round {round_number}, received {response.round}"
                )
                return state
            responses.append(response)
            repair_used.append(repaired)
            selected_action_ids.update(item.action_id for item in response.collection_orders)

        state.metadata["round_responses"] = [item.model_dump(mode="json") for item in responses]
        state.metadata["schema_repairs"] = repair_used
        state.metadata["condition"] = condition
        return state

    return solve


def _judge_families_are_independent(judge_a: str, judge_b: str) -> bool:
    return judge_a.split("/", 1)[0].casefold() != judge_b.split("/", 1)[0].casefold()


@scorer(metrics=[mean()])
def strategic_surprise_scorer(
    *,
    judge_mode: JudgeMode = "off",
    judge_a: str | None = None,
    judge_b: str | None = None,
    validator: str | None = None,
    calibration_report: str | None = None,
) -> object:
    async def score(state: TaskState, target: object) -> Score:
        del target
        case = load_case(str(state.metadata["case_id"]))
        raw_responses = state.metadata.get("round_responses", [])
        if len(raw_responses) != 3:
            return Score(
                value=0.0,
                answer=state.output.completion,
                explanation=str(state.metadata.get("schema_failure", "incomplete session")),
                reason="invalid_response_format",
                metadata={
                    "case_id": case.manifest.id,
                    "schema_failure_round": state.metadata.get("schema_failure_round"),
                },
            )
        try:
            responses = [RoundResponse.model_validate(item) for item in raw_responses]
        except ValidationError as error:
            return Score(value=0.0, explanation=str(error), reason="invalid_response_format")

        decisions: list[ValidationDecision] = []
        publishable = False
        judge_status = "off"
        if judge_mode != "off":
            if not all([judge_a, judge_b, validator]):
                return Score(
                    value=0.0,
                    explanation="judge mode requires judge_a, judge_b, and validator",
                    reason="scoring_failed",
                )
            if not _judge_families_are_independent(str(judge_a), str(judge_b)):
                return Score(
                    value=0.0,
                    explanation="Judge A and Judge B must use different provider families.",
                    reason="scoring_failed",
                )
            publishable = judge_mode == "published" and gate_allows_automated_scoring(
                calibration_report
            )
            if judge_mode == "published" and not publishable:
                judge_status = "blocked_by_calibration_gate"
            else:
                judge_status = "calibration_only" if judge_mode == "calibration" else "published"
                cascade = JudgeCascade(
                    InspectJudgeBackend(str(judge_a), "judge-a"),
                    InspectJudgeBackend(str(judge_b), "judge-b"),
                    InspectJudgeBackend(str(validator), "validator"),
                )
                selected = {
                    order.action_id
                    for response in responses
                    for order in response.collection_orders
                }
                authorized_facts = [
                    f"[{item.id}] {item.text}" for item in case.visible_evidence(3, selected)
                ]
                for rubric in case.rubric:
                    decisions.append(
                        await cascade.evaluate(rubric, responses[-1], authorized_facts)
                    )

        result = score_session(case, responses, decisions)
        metadata = result.model_dump(mode="json")
        metadata.update(
            {
                "case_id": case.manifest.id,
                "condition": state.metadata.get("condition"),
                "judge_mode": judge_mode,
                "judge_status": judge_status,
                "publishable_automated_rubric_score": publishable,
                "judge_decisions": [item.model_dump(mode="json") for item in decisions],
                "schema_repairs": state.metadata.get("schema_repairs", []),
            }
        )
        return Score(
            value=result.total / 100.0,
            answer=responses[-1].decision_memo,
            explanation=(
                f"Strategic Surprise Score {result.total:.2f}/100; "
                f"{len(result.human_review_items)} rubric items require human review."
            ),
            metadata=metadata,
        )

    return score


@task
def strategic_surprise(
    condition: Condition = "plain",
    case_id: str | None = None,
    judge_mode: JudgeMode = "off",
    judge_a: str | None = None,
    judge_b: str | None = None,
    validator: str | None = None,
    calibration_report: str | None = None,
) -> Task:
    """Create the complete six-case task or a selected case."""
    if condition not in {"plain", "agent"}:
        raise ValueError("condition must be 'plain' or 'agent'")
    selected = [case_id] if case_id else list_case_ids()
    unknown = set(selected) - set(list_case_ids())
    if unknown:
        raise ValueError(f"unknown case IDs: {sorted(unknown)}")
    cases = [load_case(item) for item in selected]
    dataset = [
        Sample(
            id=case.manifest.id,
            input=render_round_prompt(case, 1),
            metadata={"case_id": case.manifest.id},
        )
        for case in cases
    ]
    system = SYSTEM_PROMPT + ("\n\n" + AGENT_ADDENDUM if condition == "agent" else "")
    return Task(
        dataset=dataset,
        setup=system_message(system),
        solver=strategic_session(condition),
        scorer=strategic_surprise_scorer(
            judge_mode=judge_mode,
            judge_a=judge_a,
            judge_b=judge_b,
            validator=validator,
            calibration_report=(
                str(Path(calibration_report).expanduser()) if calibration_report else None
            ),
        ),
        config=GenerateConfig(temperature=0.2, max_tokens=MAX_OUTPUT_TOKENS),
        message_limit=MESSAGE_LIMIT,
        version=BENCHMARK_VERSION,
        metadata={
            "condition": condition,
            "judge_mode": judge_mode,
            "benchmark_version": BENCHMARK_VERSION,
        },
    )
