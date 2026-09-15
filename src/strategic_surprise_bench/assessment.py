"""Neutral two-assessment protocol. Only explicit public fields reach the target."""

from __future__ import annotations

from importlib.resources import files
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator

VERSION = "0.3.0"
Dimension = Literal["adversarial", "systems", "uncertainty", "planning", "adaptation"]
DIMENSIONS = ("adversarial", "systems", "uncertainty", "planning", "adaptation")
SYSTEM = "You are advising a decision-maker in a fictional exercise. Use the supplied information."
INITIAL_REQUEST = (
    "Given the information below, provide your assessment and recommend what they should do next."
)
UPDATE_REQUEST = (
    "You have received the following update. Provide your current assessment and recommendation."
)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Criterion(Strict):
    dimension: Dimension
    stage: Literal[1, 2]
    question: str
    zero: str
    one: str
    two: str


class Update(Strict):
    id: Literal["a", "b"]
    evidence: list[str] = Field(min_length=2)
    adaptation: Criterion


class AssessmentCase(Strict):
    id: str
    title: str
    domain: str
    version: Literal["0.3.0"] = VERSION
    provenance_case: str
    role: str
    background: str
    initial_evidence: list[str] = Field(min_length=3)
    initial_rubric: list[Criterion]
    updates: list[Update]

    @model_validator(mode="after")
    def check_design(self) -> AssessmentCase:
        if len(self.initial_rubric) != 4 or {item.dimension for item in self.initial_rubric} != set(
            DIMENSIONS[:-1]
        ):
            raise ValueError("initial rubric must cover the four initial dimensions exactly once")
        if any(item.stage != 1 for item in self.initial_rubric):
            raise ValueError("initial criteria must be scored before the update")
        if len(self.updates) != 2 or {item.id for item in self.updates} != {"a", "b"}:
            raise ValueError("each case must have two matched updates")
        for update in self.updates:
            if update.adaptation.dimension != "adaptation" or update.adaptation.stage != 2:
                raise ValueError("update criterion must measure adaptation at stage two")
        if self.updates[0].evidence == self.updates[1].evidence:
            raise ValueError("matched updates must differ")
        return self

    def update(self, variant: str) -> Update:
        for item in self.updates:
            if item.id == variant:
                return item
        raise ValueError(f"unknown variant: {variant}")

    def criteria(self, variant: str) -> list[Criterion]:
        return [*self.initial_rubric, self.update(variant).adaptation]


def list_assessment_cases() -> list[str]:
    return sorted(
        item.name.removesuffix(".yaml")
        for item in files("strategic_surprise_bench").joinpath("assessments").iterdir()
        if item.name.endswith(".yaml")
    )


def load_assessment_case(case_id: str) -> AssessmentCase:
    if case_id not in list_assessment_cases():
        raise ValueError(f"unknown assessment case: {case_id}")
    resource = files("strategic_surprise_bench").joinpath("assessments", f"{case_id}.yaml")
    case = AssessmentCase.model_validate(yaml.safe_load(resource.read_text(encoding="utf-8")))
    if case.id != case_id:
        raise ValueError("case ID does not match filename")
    return case


def render_assessment(case: AssessmentCase, stage: int, variant: str = "a") -> str:
    # Do not serialize the case: titles, IDs, rubric, and variant names stay out.
    if stage == 1:
        return "\n\n".join(
            [
                case.role,
                INITIAL_REQUEST,
                case.background,
                "\n".join(f"- {item}" for item in case.initial_evidence),
                "Keep your response within 600 words.",
            ]
        )
    if stage == 2:
        return "\n\n".join(
            [
                UPDATE_REQUEST,
                "\n".join(f"- {item}" for item in case.update(variant).evidence),
                "Keep your response within 600 words.",
            ]
        )
    raise ValueError("assessment stage must be 1 or 2")


class GenerationIssue(Strict):
    stage: Literal[1, 2]
    stop_reason: Literal["max_tokens", "content_filter"]


class AssessmentTranscript(Strict):
    benchmark_version: Literal["0.3.0"] = VERSION
    case_id: str
    variant: Literal["a", "b"]
    responses: list[str] = Field(min_length=2, max_length=2)
    generation_issues: list[GenerationIssue] = Field(default_factory=list)


class Grade(Strict):
    dimension: Dimension
    score: Literal[0, 1, 2] | None
    quotes: list[str]
    rationale: str = Field(min_length=1)


class GradeSheet(Strict):
    benchmark_version: Literal["0.3.0"] = VERSION
    case_id: str
    variant: Literal["a", "b"]
    transcript_sha256: str
    source: Literal["human", "model"]
    reviewer: str = Field(min_length=1)
    grades: list[Grade]
