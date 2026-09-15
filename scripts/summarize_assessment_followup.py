"""Report the additional Sol run and explicitly requested Sonnet grading retries."""

import json
from pathlib import Path

from summarize_assessment_pilot import summarize

from strategic_surprise_bench.assessment import VERSION

ROOT = Path("outputs/private/v0.3-screen-2026-09-15")


def main():
    data = summarize(ROOT)
    assert len(data["models"]) == 4
    assert all(m["status"] == "success" and m["sessions"] == 12 for m in data["models"])
    audits = [json.loads(p.read_text()) for p in (ROOT / "sonnet-regrade").glob("*.audit.json")]
    changes = {(a["after"]["case_id"], a["after"]["variant"]): a for a in audits}
    rows = []
    for model in data["models"]:
        scores = model["rows"]
        if "sonnet" in model["model"]:
            scores = [
                changes[(r["case_id"], r["variant"])]["after"]
                if (r["case_id"], r["variant"]) in changes
                else r
                for r in scores
            ]
        values = [v for s in scores for v in s["dimensions"].values()]
        known = [v for v in values if v is not None]
        rows.append(
            {
                "model": model["model"],
                "label": model["label"],
                "grading_pass": "failed-grade retries"
                if "sonnet" in model["model"]
                else "original",
                "accepted_grades": len(known),
                "expected_grades": 60,
                "complete_sessions": sum(s["total"] is not None for s in scores),
                "mean": sum(known) / 12 if len(known) == 60 else None,
                "bounds": [sum(known) / 12, (sum(known) + 2 * (60 - len(known))) / 12],
                "scores": scores,
            }
        )
    recovered = sum(
        sum(v is not None for v in a["after"]["dimensions"].values())
        - sum(v is not None for v in a["before"]["dimensions"].values())
        for a in audits
    )
    calls = sum(a["judge_calls"] for a in audits)
    result = {
        "benchmark_version": VERSION,
        "models": rows,
        "sonnet_recovered_grades": recovered,
        "sonnet_retry_judge_calls": calls,
        "original_runs": data,
    }
    Path("results/V0_3_FOLLOWUP_2026-09-15.json").write_text(json.dumps(result, indent=2) + "\n")
    lines = [
        "# v0.3 follow-up: Sol and Sonnet grading retries",
        "",
        f"Sonnet recovered {recovered}/17 missing grades in {calls} additional Opus calls. "
        "All 33 previously accepted grades and all target responses were preserved. "
        "The two Red Harvest sessions remain unavailable because of target content filtering.",
        "",
        "| Model | Grading pass | Accepted grades | Complete sessions | Mean /10 | "
        "Possible range /10 |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        mean = "—" if row["mean"] is None else f"{row['mean']:.2f}"
        lines.append(
            f"| {row['label']} | {row['grading_pass']} | {row['accepted_grades']}/60 | "
            f"{row['complete_sessions']}/12 | {mean} | "
            f"{row['bounds'][0]:.2f}–{row['bounds'][1]:.2f} |"
        )
    lines += [
        "",
        "Ranges assign each missing grade every possible value from 0 to 2; "
        "they are not confidence intervals or score estimates. Incomplete models have no mean.",
        "",
        "Sol used the same 12 sessions, neutral prompts, 4096-token cap, medium reasoning "
        "effort, and Opus judge as the original protocol. Sonnet retries used identical "
        "stage-isolated packets and judge instructions, up to three attempts per failed "
        "stage, plus one logged quote-format reminder for a repeatedly ellipsized quote. "
        "Only the first valid replacement of a missing grade was accepted, regardless "
        "of its value. This explicitly requested retry pass is separate from the default "
        "no-retry protocol. Original logs and every retry output are retained privately.",
        "",
        "These are provisional model grades from one run across six scenario families. "
        "They have not been validated by expert reviewers.",
        "",
        "Sol received full credit on all 50 accepted rubric grades; 10 grades remain missing. "
        "Together with Luna and Sonnet clustering near the maximum, this suggests a ceiling "
        "problem remains for stronger models. Quote-validation failures are also a substantial "
        "grading reliability problem. These results do not establish fine distinctions among them.",
        "",
        "## Case scores",
        "",
        "| Case / variant | " + " | ".join(r["label"] for r in rows) + " |",
        "|---|" + "---:|" * len(rows),
    ]
    for case in rows[0]["scores"]:
        key = (case["case_id"], case["variant"])
        totals = [
            next(s["total"] for s in r["scores"] if (s["case_id"], s["variant"]) == key)
            for r in rows
        ]
        lines.append(
            "| "
            + " / ".join(key)
            + " | "
            + " | ".join("—" if v is None else str(v) for v in totals)
            + " |"
        )
    Path("results/V0_3_FOLLOWUP_2026-09-15.md").write_text("\n".join(lines) + "\n")
    print(json.dumps([{k: v for k, v in r.items() if k != "scores"} for r in rows], indent=2))


if __name__ == "__main__":
    main()
