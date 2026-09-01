"""Typed contracts for scenario data, model responses, and grading artifacts."""

from __future__ import annotations

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

Probability = Annotated[float, Field(ge=0.0, le=1.0)]
UnitScore = Annotated[float, Field(ge=0.0, le=1.0)]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", validate_assignment=True)


class Confidence(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"


class Depth(StrEnum):
    mention = "mention"
    analysis = "analysis"
    recommendation = "recommendation"
    contingency = "contingency"


class Provenance(StrictModel):
    title: str
    url: str | None = None
    license: str
    elements_used: str
    transformation: str


class ScenarioManifest(StrictModel):
    id: str
    title: str
    version: str = "0.1.0"
    domain: str
    summary: str
    construct_tags: list[str]
    public: bool = True
    fictional: bool = True
    collection_budgets: dict[int, int] = Field(default_factory=lambda: {1: 10, 2: 6})
    provenance: list[Provenance]


class HypothesisDefinition(StrictModel):
    id: str
    label: str
    description: str
    public_label: str | None = None
    public_description: str | None = None
    requires_generation: bool = False


class EvidenceItem(StrictModel):
    id: str
    round_available: Annotated[int, Field(ge=1, le=3)]
    source: str
    text: str
    reliability: UnitScore
    deception_risk: UnitScore
    correlation_group: str
    supports: list[str] = Field(default_factory=list)
    contradicts: list[str] = Field(default_factory=list)
    public_inject: bool = False


class CollectionAction(StrictModel):
    id: str
    round_available: Literal[1, 2]
    label: str
    description: str
    cost: Annotated[int, Field(ge=1, le=10)]
    correlation_group: str
    likelihood_positive: dict[str, Probability]
    observed: Literal["positive", "negative", "inconclusive"]
    return_evidence_id: str


class ForecastQuestion(StrictModel):
    id: str
    question: str
    horizon: str
    outcome: Literal[0, 1]
    resolution: str


class PolicyLever(StrictModel):
    id: str
    label: str
    description: str
    reversible: bool
    affected_domains: list[str]


class PolicyConsequence(StrictModel):
    action_id: str
    consequence: str
    probability_if_selected: Probability
    desirable: bool


class CriticalTask(StrictModel):
    id: str
    criterion: str
    critical: bool = False
    positive_action_ids: list[str] = Field(default_factory=list)
    prohibited_action_ids: list[str] = Field(default_factory=list)
    minimum_allocation: Probability = 0.15


class RubricItem(StrictModel):
    id: str
    dimension: Literal["alternatives", "policy", "memo"]
    criterion: str
    required_meaning: str
    minimum_depth: Depth
    acceptable_equivalents: list[str]
    required_evidence: bool = False
    allowed_evidence_ids: list[str] = Field(default_factory=list)
    near_misses: list[str] = Field(default_factory=list)
    negation_terms: list[str] = Field(
        default_factory=lambda: ["not", "no", "reject", "avoid", "dismiss"]
    )
    contradiction_terms: list[str] = Field(default_factory=list)
    critical: bool = False
    automatable: bool = True


class RoundDefinition(StrictModel):
    round: Literal[1, 2, 3]
    title: str
    brief: str
    common_evidence_ids: list[str]


class WorldBible(StrictModel):
    resolved_hypothesis: str
    hidden_truth: str
    actor_motives: dict[str, str]
    causal_pathway: list[str]
    surprise_type: str


class ScenarioCase(StrictModel):
    manifest: ScenarioManifest
    role: str
    background: str
    hypotheses: list[HypothesisDefinition]
    rounds: list[RoundDefinition]
    evidence: list[EvidenceItem]
    collection_actions: list[CollectionAction]
    forecasts: list[ForecastQuestion]
    policy_levers: list[PolicyLever]
    policy_consequences: list[PolicyConsequence]
    critical_tasks: list[CriticalTask]
    rubric: list[RubricItem]
    world_bible: WorldBible

    @model_validator(mode="after")
    def validate_case_integrity(self) -> ScenarioCase:
        hypothesis_ids = {item.id for item in self.hypotheses}
        if len(hypothesis_ids) != 4:
            raise ValueError("each case must define exactly four unique hypotheses")
        if self.world_bible.resolved_hypothesis not in hypothesis_ids:
            raise ValueError("resolved hypothesis must be one of the four hypotheses")
        generated_ids = {item.id for item in self.hypotheses if item.requires_generation}
        if generated_ids != {"H2", "H3"}:
            raise ValueError("H2 and H3 must be analyst-generated hypothesis slots")
        for item in self.hypotheses:
            if item.requires_generation and not (item.public_label and item.public_description):
                raise ValueError(f"generated slot {item.id} needs public prompt text")
        if [item.round for item in self.rounds] != [1, 2, 3]:
            raise ValueError("rounds must be defined exactly once in order 1, 2, 3")
        if len(self.forecasts) != 6:
            raise ValueError("each case must define exactly six recurring forecasts")

        evidence_ids = {item.id for item in self.evidence}
        if len(evidence_ids) != len(self.evidence):
            raise ValueError("evidence IDs must be unique")
        for item in self.evidence:
            if not set(item.supports + item.contradicts) <= hypothesis_ids:
                raise ValueError(f"evidence {item.id} refers to an unknown hypothesis")
        for round_def in self.rounds:
            if not set(round_def.common_evidence_ids) <= evidence_ids:
                raise ValueError(f"round {round_def.round} refers to unknown evidence")

        action_ids = {item.id for item in self.collection_actions}
        if len(action_ids) != len(self.collection_actions):
            raise ValueError("collection action IDs must be unique")
        for round_number in (1, 2):
            count = sum(a.round_available == round_number for a in self.collection_actions)
            if count != 8:
                raise ValueError(f"round {round_number} must offer exactly eight actions")
        for action in self.collection_actions:
            if set(action.likelihood_positive) != hypothesis_ids:
                raise ValueError(f"collection {action.id} needs likelihoods for every hypothesis")
            if action.return_evidence_id not in evidence_ids:
                raise ValueError(f"collection {action.id} has unknown return evidence")

        lever_ids = {item.id for item in self.policy_levers}
        if len(lever_ids) < 4:
            raise ValueError("each case needs at least four policy levers")
        if not {item.action_id for item in self.policy_consequences} <= lever_ids:
            raise ValueError("policy consequence refers to an unknown action")
        for task in self.critical_tasks:
            if not set(task.positive_action_ids + task.prohibited_action_ids) <= lever_ids:
                raise ValueError(f"critical task {task.id} refers to an unknown policy action")
        return self

    def evidence_by_id(self) -> dict[str, EvidenceItem]:
        return {item.id: item for item in self.evidence}

    def actions_for_round(self, round_number: int) -> list[CollectionAction]:
        return [a for a in self.collection_actions if a.round_available == round_number]

    def visible_evidence(
        self, round_number: int, selected_action_ids: set[str]
    ) -> list[EvidenceItem]:
        common_ids = {
            evidence_id
            for definition in self.rounds
            if definition.round <= round_number
            for evidence_id in definition.common_evidence_ids
        }
        returned_ids = {
            action.return_evidence_id
            for action in self.collection_actions
            if action.id in selected_action_ids and action.round_available < round_number
        }
        visible = common_ids | returned_ids
        by_id = self.evidence_by_id()
        return [by_id[eid] for eid in sorted(visible)]


class HypothesisAssessment(StrictModel):
    id: str
    probability: Probability
    confidence: Confidence
    supporting_evidence_ids: list[str] = Field(default_factory=list)
    contradicting_evidence_ids: list[str] = Field(default_factory=list)


class GeneratedHypothesis(StrictModel):
    """An analyst-authored causal model for a deliberately blank hypothesis slot."""

    slot_id: str
    statement: str = Field(min_length=1, max_length=600)
    causal_mechanism: str = Field(min_length=1, max_length=1000)
    actor_incentives: list[str] = Field(min_length=1, max_length=4)
    expected_observables: list[str] = Field(min_length=1, max_length=4)
    disconfirming_observables: list[str] = Field(min_length=1, max_length=4)
    second_order_effects: list[str] = Field(min_length=1, max_length=4)
    counterfactual: str = Field(min_length=1, max_length=800)
    evidence_ids: list[str] = Field(default_factory=list)


class ForecastAssessment(StrictModel):
    id: str
    probability: Probability


class Finding(StrictModel):
    claim: str
    evidence_ids: list[str] = Field(default_factory=list)
    implication: str
    uncertainty: str
    alternative_explanation: str


class SourceAssessment(StrictModel):
    evidence_id: str
    reliability: UnitScore
    independence: UnitScore
    deception_risk: UnitScore
    relevance: UnitScore


class CollectionOrder(StrictModel):
    action_id: str
    purpose: str
    discriminates_hypotheses: list[str]


class PolicyAction(StrictModel):
    action_id: str
    allocation: Annotated[int, Field(ge=0, le=100)]
    objective: str
    mechanism: str
    risks: list[str]
    affected_domains: list[str]
    triggers: list[str]


class RoundResponse(StrictModel):
    round: Literal[1, 2, 3]
    hypotheses: list[HypothesisAssessment]
    generated_hypotheses: list[GeneratedHypothesis]
    forecasts: list[ForecastAssessment]
    findings: list[Finding]
    source_assessments: list[SourceAssessment]
    collection_orders: list[CollectionOrder] = Field(default_factory=list)
    policy_actions: list[PolicyAction] = Field(default_factory=list)
    decision_memo: str = Field(min_length=1, max_length=8000)

    @model_validator(mode="after")
    def validate_probability_and_policy_sums(self) -> RoundResponse:
        if len(self.hypotheses) != 4:
            raise ValueError("response must assess exactly four hypotheses")
        generated_ids = [item.slot_id for item in self.generated_hypotheses]
        if len(generated_ids) != 2 or set(generated_ids) != {"H2", "H3"}:
            raise ValueError("response must generate exactly the H2 and H3 hypothesis slots")
        probability_sum = sum(item.probability for item in self.hypotheses)
        if abs(probability_sum - 1.0) > 1e-6:
            raise ValueError("hypothesis probabilities must sum to 1")
        if len(self.forecasts) != 6:
            raise ValueError("response must answer exactly six forecasts")
        if self.round == 3:
            if sum(item.allocation for item in self.policy_actions) != 100:
                raise ValueError("round 3 policy allocations must sum to 100")
            if self.collection_orders:
                raise ValueError("round 3 cannot place collection orders")
        elif self.policy_actions:
            raise ValueError("policy allocations are only accepted in round 3")
        return self


class JudgeLabel(StrEnum):
    fail = "fail"
    partial = "partial"
    pass_ = "pass"

    @property
    def value_numeric(self) -> float:
        return {JudgeLabel.fail: 0.0, JudgeLabel.partial: 0.5, JudgeLabel.pass_: 1.0}[self]


class JudgeVerdict(StrictModel):
    rubric_id: str
    label: JudgeLabel
    supporting_spans: list[str] = Field(default_factory=list)
    contradiction_spans: list[str] = Field(default_factory=list)
    confidence: UnitScore
    rationale: str


class ValidationStatus(StrEnum):
    accepted = "accepted"
    abstain = "abstain"
    human_review = "human_review"


class ValidationDecision(StrictModel):
    rubric_id: str
    status: ValidationStatus
    label: JudgeLabel | None = None
    score: UnitScore | None = None
    reason: str
    judge_verdicts: list[JudgeVerdict] = Field(default_factory=list)
    validator_verdict: JudgeVerdict | None = None
