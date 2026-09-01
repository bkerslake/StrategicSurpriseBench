"""Bounded note-taking tools for the analyst-agent condition.

The tools persist only information supplied by the evaluated model. They cannot read the
scenario package, hidden world bible, network, filesystem, environment, or scorer state.
"""

from __future__ import annotations

from typing import Literal

from inspect_ai.tool import Tool, tool
from inspect_ai.util import StoreModel, store_as
from pydantic import Field


class AnalystNotebook(StoreModel):
    evidence: dict[str, str] = Field(default_factory=dict)
    hypotheses: dict[str, dict[str, object]] = Field(default_factory=dict)
    timeline: dict[str, str] = Field(default_factory=dict)
    collection: dict[str, dict[str, object]] = Field(default_factory=dict)


@tool(parallel=False)
def evidence_ledger() -> Tool:
    """Maintain an evidence ledger without retrieving any new evidence."""

    async def execute(
        operation: Literal["record", "view"],
        evidence_id: str | None = None,
        assessment: str | None = None,
    ) -> dict[str, str]:
        """Record or view the analyst's own evidence notes.

        Args:
            operation: `record` a note or `view` the current ledger.
            evidence_id: Case evidence ID when recording.
            assessment: Your concise source and relevance assessment.
        """
        notebook = store_as(AnalystNotebook)
        if operation == "record":
            if not evidence_id or assessment is None:
                return {"error": "record requires evidence_id and assessment"}
            notebook.evidence[evidence_id] = assessment
        return dict(notebook.evidence)

    return execute


@tool(parallel=False)
def hypothesis_table() -> Tool:
    """Maintain probabilities and evidence links without calculating or revealing answers."""

    async def execute(
        operation: Literal["update", "view"],
        hypothesis_id: str | None = None,
        probability: float | None = None,
        supporting_evidence_ids: list[str] | None = None,
        contradicting_evidence_ids: list[str] | None = None,
    ) -> dict[str, dict[str, object]]:
        """Update or view the analyst's own hypothesis table.

        Args:
            operation: `update` one hypothesis or `view` the whole table.
            hypothesis_id: Case hypothesis ID.
            probability: Current probability between zero and one.
            supporting_evidence_ids: Evidence IDs you treat as supporting.
            contradicting_evidence_ids: Evidence IDs you treat as contradicting.
        """
        notebook = store_as(AnalystNotebook)
        if operation == "update":
            if not hypothesis_id or probability is None or not 0 <= probability <= 1:
                return {"error": {"message": "update requires an ID and probability in [0,1]"}}
            notebook.hypotheses[hypothesis_id] = {
                "probability": probability,
                "supporting_evidence_ids": supporting_evidence_ids or [],
                "contradicting_evidence_ids": contradicting_evidence_ids or [],
            }
        return dict(notebook.hypotheses)

    return execute


@tool(parallel=False)
def timeline() -> Tool:
    """Maintain a model-authored timeline without revealing scenario state."""

    async def execute(
        operation: Literal["record", "view"],
        event_id: str | None = None,
        timing_and_significance: str | None = None,
    ) -> dict[str, str]:
        """Record or view time-ordering notes.

        Args:
            operation: `record` an event or `view` the current timeline.
            event_id: Evidence or analyst-defined event ID.
            timing_and_significance: Your timing and causal interpretation.
        """
        notebook = store_as(AnalystNotebook)
        if operation == "record":
            if not event_id or timing_and_significance is None:
                return {"error": "record requires event_id and timing_and_significance"}
            notebook.timeline[event_id] = timing_and_significance
        return dict(notebook.timeline)

    return execute


@tool(parallel=False)
def collection_plan() -> Tool:
    """Maintain a proposed collection portfolio; this does not execute collection."""

    async def execute(
        operation: Literal["record", "remove", "view"],
        action_id: str | None = None,
        stated_cost: int | None = None,
        purpose: str | None = None,
        discriminates_hypotheses: list[str] | None = None,
    ) -> dict[str, dict[str, object]]:
        """Record, remove, or view collection-planning notes.

        Args:
            operation: `record`, `remove`, or `view` the plan.
            action_id: Case collection-action ID.
            stated_cost: Cost copied from the visible menu.
            purpose: What uncertainty the action should reduce.
            discriminates_hypotheses: Hypothesis IDs the action discriminates.
        """
        notebook = store_as(AnalystNotebook)
        if operation == "record":
            if not action_id or stated_cost is None or purpose is None:
                return {"error": {"message": "record requires action_id, cost, and purpose"}}
            notebook.collection[action_id] = {
                "stated_cost": stated_cost,
                "purpose": purpose,
                "discriminates_hypotheses": discriminates_hypotheses or [],
            }
        elif operation == "remove" and action_id:
            notebook.collection.pop(action_id, None)
        return dict(notebook.collection)

    return execute


def bounded_analyst_tools() -> list[Tool]:
    return [evidence_ledger(), hypothesis_table(), timeline(), collection_plan()]
