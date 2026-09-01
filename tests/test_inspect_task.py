from __future__ import annotations

import json

from inspect_ai import eval
from inspect_ai._util.registry import registry_info
from inspect_ai.model import ModelOutput, ModelUsage, get_model

from strategic_surprise_bench.inspect_task import (
    DEFAULT_JUDGE_A,
    DEFAULT_JUDGE_B,
    DEFAULT_VALIDATOR,
    MAX_OUTPUT_TOKENS,
    MESSAGE_LIMIT,
    _rubric_evaluation_context,
    strategic_surprise,
)
from strategic_surprise_bench.loader import load_case
from strategic_surprise_bench.mock import make_mock_session
from strategic_surprise_bench.prompts import render_round_prompt
from strategic_surprise_bench.tools import bounded_analyst_tools


def test_task_constructs_both_conditions_with_identical_case_input():
    plain = strategic_surprise(condition="plain")
    agent = strategic_surprise(condition="agent")
    assert len(plain.dataset) == len(agent.dataset) == 6
    assert [item.id for item in plain.dataset] == [item.id for item in agent.dataset]
    assert [item.input for item in plain.dataset] == [item.input for item in agent.dataset]
    assert plain.config.max_tokens == agent.config.max_tokens == MAX_OUTPUT_TOKENS == 8000
    assert plain.message_limit == agent.message_limit == MESSAGE_LIMIT == 80


def test_default_judge_cascade_uses_terra_cross_family_and_luna():
    task = strategic_surprise(case_id="lattice_signal", judge_mode="calibration")
    assert DEFAULT_JUDGE_A == "openai/gpt-5.6-terra"
    assert DEFAULT_JUDGE_B.startswith("anthropic/")
    assert DEFAULT_VALIDATOR == "openai/gpt-5.6-luna"
    assert task.metadata["judge_models"] == {
        "judge_a": DEFAULT_JUDGE_A,
        "judge_b": DEFAULT_JUDGE_B,
        "validator": DEFAULT_VALIDATOR,
    }


def test_strategic_judge_context_is_pre_reveal(lattice):
    responses = make_mock_session(lattice, "perfect")
    strategic = next(item for item in lattice.rubric if item.dimension == "alternatives")
    policy = next(item for item in lattice.rubric if item.dimension == "policy")
    strategic_response, strategic_facts = _rubric_evaluation_context(
        lattice, responses, strategic
    )
    policy_response, policy_facts = _rubric_evaluation_context(lattice, responses, policy)
    round_three_ids = set(lattice.rounds[2].common_evidence_ids)
    assert strategic_response.round == 2
    assert all(not any(f"[{item}]" in fact for item in round_three_ids) for fact in strategic_facts)
    assert policy_response.round == 3
    assert any(any(f"[{item}]" in fact for item in round_three_ids) for fact in policy_facts)


def test_agent_tools_are_bounded_note_takers():
    names = {registry_info(item).name for item in bounded_analyst_tools()}
    assert names == {"evidence_ledger", "hypothesis_table", "timeline", "collection_plan"}
    assert names.isdisjoint({"bash", "web_search", "read_file", "python"})


def test_round_prompt_exposes_only_selected_returns(lattice):
    action = lattice.actions_for_round(1)[0]
    without = render_round_prompt(lattice, 2, set())
    with_selected = render_round_prompt(lattice, 2, {action.id})
    returned = lattice.evidence_by_id()[action.return_evidence_id]
    assert returned.text not in without
    assert returned.text in with_selected


def test_mock_model_runs_end_to_end_without_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("INSPECT_TRACE_FILE", str(tmp_path / "inspect-trace.log"))
    monkeypatch.setattr("inspect_ai._util.appdirs.user_data_path", lambda package_name: tmp_path)
    case = load_case("lattice_signal")
    responses = make_mock_session(case, "perfect")
    malformed = ModelOutput.from_content(model="mockllm/model", content="not json")
    malformed.usage = ModelUsage(input_tokens=1, output_tokens=1, total_tokens=2)
    outputs = [malformed]
    for response in responses:
        output = ModelOutput.from_content(
            model="mockllm/model",
            content=json.dumps(response.model_dump(mode="json")),
        )
        output.usage = ModelUsage(input_tokens=1, output_tokens=1, total_tokens=2)
        outputs.append(output)
    model = get_model("mockllm/model", custom_outputs=outputs, memoize=False)
    logs = eval(
        strategic_surprise(condition="agent", case_id=case.manifest.id),
        model=model,
        display="none",
        log_dir=str(tmp_path),
    )
    assert len(logs) == 1
    assert logs[0].status == "success"
    assert logs[0].results is not None
    sample = logs[0].samples[0]
    score = next(iter(sample.scores.values()))
    assert score.metadata["schema_repairs"] == [True, False, False]
