from __future__ import annotations

from strategic_surprise_bench.loader import load_all_cases
from strategic_surprise_bench.prompts import render_round_prompt
from strategic_surprise_bench.validation import validate_repository_cases


def test_six_cases_pass_repository_validation():
    report = validate_repository_cases()
    assert report.passed, report.failures
    assert report.case_count == 6


def test_case_contract_and_warning_path():
    for case in load_all_cases():
        assert len(case.rounds) == 3
        assert len(case.hypotheses) == 4
        assert len(case.forecasts) == 6
        assert len(case.actions_for_round(1)) == 8
        assert len(case.actions_for_round(2)) == 8
        assert case.manifest.collection_budgets == {1: 10, 2: 6}
        truth = case.world_bible.resolved_hypothesis
        assert any(truth in item.supports for item in case.visible_evidence(1, set()))


def test_hidden_truth_and_future_injects_do_not_enter_prompts():
    for case in load_all_cases():
        round_one = render_round_prompt(case, 1)
        assert case.world_bible.hidden_truth not in round_one
        assert "world_bible" not in round_one.casefold()
        later_common = {
            evidence_id
            for definition in case.rounds[1:]
            for evidence_id in definition.common_evidence_ids
        }
        assert later_common.isdisjoint(item.id for item in case.visible_evidence(1, set()))
        assert all(f"[{item}]" not in round_one for item in later_common)


def test_answer_hypotheses_are_blank_generation_slots_in_prompts():
    for case in load_all_cases():
        prompt = render_round_prompt(case, 1)
        generated = [item for item in case.hypotheses if item.requires_generation]
        assert {item.id for item in generated} == {"H2", "H3"}
        assert "DELIBERATELY INCOMPLETE, NOT AN ANSWER LIST" in prompt
        for item in generated:
            assert f"- {item.id}: {item.label}" not in prompt
            assert item.description not in prompt
            assert f"- {item.id}: {item.public_label}" in prompt


def test_creative_reasoning_has_case_specific_atomic_coverage():
    for case in load_all_cases():
        alternatives = [item for item in case.rubric if item.dimension == "alternatives"]
        assert len(case.rubric) == 6
        assert len(alternatives) == 4
        assert any("counterfactual" in item.criterion.casefold() for item in alternatives)


def test_private_source_is_only_structural_provenance():
    lattice = next(case for case in load_all_cases() if case.manifest.id == "lattice_signal")
    serialized = lattice.model_dump_json().casefold()
    assert "quantum surprise scenario" not in serialized
    assert "china's encryption pivot" not in serialized
    assert "bitcoin wallet breach" not in serialized
    private_record = lattice.manifest.provenance[0]
    assert "not redistributed" in private_record.license.casefold()
