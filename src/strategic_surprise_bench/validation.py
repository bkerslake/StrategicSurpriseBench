"""Static scenario, leakage, provenance, and protocol validation."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from strategic_surprise_bench.loader import load_all_cases
from strategic_surprise_bench.prompts import render_round_prompt


@dataclass(frozen=True)
class ValidationReport:
    passed: bool
    case_count: int
    checks: int
    failures: tuple[str, ...]


def validate_repository_cases() -> ValidationReport:
    cases = load_all_cases()
    failures: list[str] = []
    checks = 0
    expected_ids = {
        "lattice_signal",
        "black_current",
        "ember_guarantee",
        "meridian_shock",
        "sable_patch",
        "red_harvest",
    }
    checks += 1
    if {case.manifest.id for case in cases} != expected_ids:
        failures.append("portfolio:case_set")

    for case in cases:
        prefix = case.manifest.id
        checks += 19
        if not case.manifest.public or not case.manifest.fictional:
            failures.append(f"{prefix}:public_fictional_flags")
        if len(case.rounds) != 3:
            failures.append(f"{prefix}:round_count")
        if len(case.forecasts) * len(case.rounds) < 18:
            failures.append(f"{prefix}:forecast_decision_count")
        if len(case.evidence) != 24:
            failures.append(f"{prefix}:evidence_count")
        if any(len(case.actions_for_round(round_number)) != 8 for round_number in (1, 2)):
            failures.append(f"{prefix}:collection_menu_size")
        if case.manifest.collection_budgets != {1: 10, 2: 6}:
            failures.append(f"{prefix}:collection_budgets")

        truth = case.world_bible.resolved_hypothesis
        generated_ids = {item.id for item in case.hypotheses if item.requires_generation}
        if generated_ids != {"H2", "H3"}:
            failures.append(f"{prefix}:generated_hypothesis_slots")
        first_round = case.visible_evidence(1, set())
        if not any(truth in item.supports and item.reliability >= 0.75 for item in first_round):
            failures.append(f"{prefix}:pre_surprise_warning_path")
        group_counts = Counter(item.correlation_group for item in case.evidence)
        if not any(
            item.deception_risk >= 0.60 and group_counts[item.correlation_group] > 1
            for item in case.evidence
        ):
            failures.append(f"{prefix}:correlated_deception")
        if len({item.correlation_group for item in first_round}) < 3:
            failures.append(f"{prefix}:independent_evidence")

        evidence = case.evidence_by_id()
        if any(
            evidence[action.return_evidence_id].round_available != action.round_available + 1
            for action in case.collection_actions
        ):
            failures.append(f"{prefix}:collection_return_timing")
        if any(
            evidence[action.return_evidence_id].public_inject for action in case.collection_actions
        ):
            failures.append(f"{prefix}:collection_return_leak")
        if {item.action_id for item in case.policy_consequences} != {
            item.id for item in case.policy_levers
        }:
            failures.append(f"{prefix}:policy_consequence_coverage")
        if not case.manifest.provenance or any(
            not item.license or not item.transformation for item in case.manifest.provenance
        ):
            failures.append(f"{prefix}:provenance")

        for round_number in (1, 2, 3):
            prompt = render_round_prompt(case, round_number, set())
            if case.world_bible.hidden_truth in prompt:
                failures.append(f"{prefix}:hidden_truth_leak_round_{round_number}")
            if "world_bible" in prompt.casefold() or "resolved_hypothesis" in prompt.casefold():
                failures.append(f"{prefix}:answer_key_label_leak_round_{round_number}")
            for item in case.hypotheses:
                if item.requires_generation and (
                    f"- {item.id}: {item.label}" in prompt or item.description in prompt
                ):
                    failures.append(f"{prefix}:latent_hypothesis_leak_round_{round_number}")
        if any(not item.required_meaning or not item.near_misses for item in case.rubric):
            failures.append(f"{prefix}:atomic_rubric_completeness")
        if len(case.rubric) != 6 or sum(
            item.dimension == "alternatives" for item in case.rubric
        ) != 4:
            failures.append(f"{prefix}:creative_rubric_coverage")

    return ValidationReport(
        passed=not failures,
        case_count=len(cases),
        checks=checks,
        failures=tuple(sorted(set(failures))),
    )
