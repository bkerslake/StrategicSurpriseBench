from __future__ import annotations

from strategic_surprise_bench.reporting import (
    RunRecord,
    hierarchical_bootstrap,
    summarize_runs,
)


def records():
    result = []
    for model in ("openai/example", "anthropic/example"):
        for condition, offset in (("plain", 0), ("agent", 4)):
            for case_index, case_id in enumerate(("case-a", "case-b", "case-c")):
                for run in range(1, 4):
                    result.append(
                        RunRecord(
                            case_id=case_id,
                            model=model,
                            condition=condition,
                            run=run,
                            total=55 + offset + case_index + run,
                            automation_coverage=0.8,
                            human_escalation_rate=0.2,
                        )
                    )
    return result


def test_hierarchical_bootstrap_is_reproducible():
    first = hierarchical_bootstrap(records(), samples=200, seed=7)
    second = hierarchical_bootstrap(records(), samples=200, seed=7)
    assert first == second
    assert first.lower <= first.mean <= first.upper


def test_summary_reports_agent_uplift_and_coverage():
    report = summarize_runs(records(), bootstrap_samples=200)
    assert report["exploratory"] is True
    assert len(report["agent_uplift"]) == 2
    assert all(item["agent_uplift"] == 4 for item in report["agent_uplift"])
    assert all(item["automation_coverage"] == 0.8 for item in report["aggregate"])
