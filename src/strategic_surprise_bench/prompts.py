"""Closed-world prompts shared by the plain and agent conditions."""

from __future__ import annotations

import json

from strategic_surprise_bench.models import RoundResponse, ScenarioCase

SYSTEM_PROMPT = """You are a strategic-warning analyst supporting a fictional interagency
steering group. Use only information supplied inside this fictional exercise. Distinguish likelihood
from confidence, question actor incentives, identify source dependence, generate omitted causal
explanations, and trace counterfactual and second-order effects. Do not assume that the supplied
hypothesis slots constitute an answer list. Your response must be one JSON object matching the
supplied schema. Do not include markdown fences or hidden reasoning."""

AGENT_ADDENDUM = """You have bounded analytic tools for maintaining an evidence ledger, a hypothesis
table, and collection orders. The tools do not reveal facts. Use them to preserve contemporaneous
judgments and check your work; your final response must still match the common JSON schema."""


def response_schema(round_number: int) -> dict:
    schema = RoundResponse.model_json_schema()
    if round_number < 3:
        schema["description"] = "policy_actions must be empty; collection_orders may be used"
    else:
        schema["description"] = (
            "collection_orders must be empty; policy_actions allocations must sum to 100"
        )
    return schema


def render_round_prompt(
    case: ScenarioCase,
    round_number: int,
    selected_action_ids: set[str] | None = None,
) -> str:
    selected_action_ids = selected_action_ids or set()
    definition = case.rounds[round_number - 1]
    visible = case.visible_evidence(round_number, selected_action_ids)
    hypotheses = "\n".join(
        f"- {item.id}: {item.public_label or item.label} — "
        f"{item.public_description or item.description}"
        for item in case.hypotheses
    )
    evidence = "\n".join(f"- [{item.id}] {item.source}: {item.text}" for item in visible)
    forecasts = "\n".join(
        f"- {item.id} ({item.horizon}): {item.question}" for item in case.forecasts
    )
    if round_number in (1, 2):
        budget = case.manifest.collection_budgets[round_number]
        actions = "\n".join(
            f"- {item.id} (cost {item.cost}): {item.label} — {item.description}"
            for item in case.actions_for_round(round_number)
        )
        collection = f"Collection budget: {budget} credits. Available actions:\n{actions}"
    else:
        levers = "\n".join(
            f"- {item.id}: {item.label} — {item.description}" for item in case.policy_levers
        )
        collection = (
            "Allocate exactly 100 policy points across these levers; omit zero-allocation levers:\n"
            + levers
        )

    if round_number == 1:
        instructions = """Formulate original causal models for the deliberately blank H2 and H3
slots, then allocate probability across all four slots and answer all six
forecasts. Assess each visible source for reliability, independence, deception risk, and relevance.
For each generated hypothesis, explain actor incentives, expected and disconfirming observables,
second-order effects, and a counterfactual that would distinguish it. State evidence-grounded
findings and spend no more than the collection budget. Each order must say what uncertainty it
discriminates."""
    elif round_number == 2:
        instructions = """Revise the H2 and H3 causal models—not merely their probabilities—and all
six forecasts. Explain what changed, which actor incentives or assumptions now look different, and
what the closest counterfactual world would produce. Preserve disconfirming evidence, reassess
source dependence, spend no more than the new collection budget, and state policy triggers."""
    else:
        instructions = """Provide final stage-specific attribution and all six consequence
forecasts. Allocate exactly 100 policy points across bounded levers. Explain objectives, mechanisms,
risks, affected domains, second-order effects, escalation management, triggers, and reversal
conditions. Finalize the H2 and H3 causal models, including what would have happened in the nearest
counterfactual world. The decision memo must cite evidence IDs and preserve material uncertainty."""

    memo_limit = 700 if round_number == 3 else 400
    length_limits = f"""Keep the response concise and auditable:
- Use at most six findings; keep each complete finding under 140 words.
- Keep collection purposes under 70 words.
- For each policy action, use at most four risks and four triggers, each stated briefly.
- Keep the decision memo under {memo_limit} words.
- Do not repeat the dossier or JSON schema in prose."""

    return f"""CASE: {case.manifest.title}
ROLE: {case.role}

BACKGROUND
{case.background}

ROUND {round_number}: {definition.title}
{definition.brief}

ROUND INSTRUCTIONS
{instructions}

RESPONSE LENGTH LIMITS
{length_limits}

HYPOTHESIS SLOTS — DELIBERATELY INCOMPLETE, NOT AN ANSWER LIST
{hypotheses}

H2 and H3 are blank analytic slots. Put your original formulations in generated_hypotheses and use
the same slot IDs in the probability table. A generic restatement of the dossier is not sufficient.

AVAILABLE EVIDENCE
{evidence}

RECURRING FORECASTS
{forecasts}

{collection}

Return only JSON matching this schema:
{json.dumps(response_schema(round_number), indent=2)}
"""


def repair_prompt(validation_errors: str) -> str:
    return f"""Your prior response was not valid. Correct only the structural errors below and
return the complete JSON object again. Do not change substantive judgments except as necessary for
validity.

VALIDATION ERRORS
{validation_errors}"""
