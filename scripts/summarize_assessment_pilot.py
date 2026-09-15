"""Aggregate live-screen logs without exposing raw responses or turning missing grades into zero."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import fmean

from inspect_ai.log import read_eval_log

from strategic_surprise_bench.assessment import DIMENSIONS, VERSION, list_assessment_cases

LABELS = {
    "openai/gpt-4o-2024-11-20": "GPT-4o",
    "openai/gpt-5.6-luna": "GPT-5.6 Luna",
    "openai/gpt-5.6-sol": "GPT-5.6 Sol",
    "anthropic/claude-sonnet-5": "Claude Sonnet 5",
}


def grade_bounds(values: list, expected: int) -> list[float]:
    known = [value for value in values if value is not None]
    return [sum(known), sum(known) + 2 * (expected - len(known))]


def summarize(root: Path) -> dict:
    expected = {(case, variant) for case in list_assessment_cases() for variant in ("a", "b")}
    models = []
    for path in sorted(root.glob("*/*.eval")):
        log = read_eval_log(path)
        manifest = json.loads((path.parent / "run-manifest.json").read_text())
        rows = []
        calls = Counter()
        word_counts = []
        for sample in log.samples or []:
            metadata = sample.metadata or {}
            calls.update(event.model for event in sample.events if event.event == "model")
            word_counts.extend(
                len(text.split())
                for text in metadata.get("assessment_transcript", {}).get("responses", [])
            )
            scores = list((sample.scores or {}).values())
            score = scores[0].metadata if scores else {}
            score = score or {}
            target_usage = (sample.model_usage or {}).get(log.eval.model)
            rows.append(
                {
                    "case_id": metadata.get("case_id"),
                    "variant": metadata.get("variant"),
                    "total": score.get("total"),
                    "dimensions": score.get("dimensions", dict.fromkeys(DIMENSIONS)),
                    "coverage": score.get("coverage", 0),
                    "missing": score.get("missing", {}),
                    "generation_issues": metadata.get("generation_issues", []),
                    "execution_error": sample.error is not None,
                    "total_time": sample.total_time,
                    "target_usage": target_usage.model_dump() if target_usage else None,
                }
            )
        cells = {(row["case_id"], row["variant"]) for row in rows}
        complete = cells == expected and len(rows) == len(expected)
        all_graded = complete and all(row["total"] is not None for row in rows)
        grades = [value for row in rows for value in row["dimensions"].values()]
        graded_totals = [row["total"] for row in rows if row["total"] is not None]
        summary = {
            "model": log.eval.model,
            "label": LABELS.get(log.eval.model, log.eval.model),
            "status": log.status,
            "sessions": len(rows),
            "expected_sessions": len(expected),
            "complete_grades": sum(row["total"] is not None for row in rows),
            "mean": fmean(row["total"] for row in rows) if all_graded else None,
            "mean_of_complete_sessions": fmean(graded_totals) if graded_totals else None,
            "mean_bounds_from_missing_grades": [
                value / len(expected) for value in grade_bounds(grades, len(expected) * 5)
            ],
            "confirmed_grade_counts": dict(Counter(value for value in grades if value is not None)),
            "grading_failure_reasons": dict(
                Counter(reason for row in rows for reason in row["missing"].values())
            ),
            "coverage": sum(row["coverage"] for row in rows) / len(expected),
            "dimension_means": {
                dim: fmean(row["dimensions"][dim] for row in rows)
                if complete and all(row["dimensions"][dim] is not None for row in rows)
                else None
                for dim in DIMENSIONS
            },
            "dimension_bounds_from_missing_grades": {
                dim: [
                    value / len(expected)
                    for value in grade_bounds(
                        [row["dimensions"][dim] for row in rows], len(expected)
                    )
                ]
                for dim in DIMENSIONS
            },
            "generation_issue_sessions": sum(bool(row["generation_issues"]) for row in rows),
            "execution_errors": sum(row["execution_error"] for row in rows),
            "model_calls": dict(calls),
            "responses_over_600_words": sum(count > 600 for count in word_counts),
            "response_word_count_range": [min(word_counts), max(word_counts)]
            if word_counts
            else [],
            "started_at": log.stats.started_at if log.stats else None,
            "completed_at": log.stats.completed_at if log.stats else None,
            "settings": log.eval.model_generate_config.model_dump(exclude_none=True),
            "judge": manifest["judge"],
            "usage": {
                model: usage.model_dump()
                for model, usage in (log.stats.model_usage.items() if log.stats else [])
            },
            "rows": sorted(rows, key=lambda row: (row["case_id"], row["variant"])),
            "log_file": str(path),
        }
        models.append(summary)
    return {
        "benchmark_version": VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "grade_status": "provisional_model_grades",
        "epochs": 1,
        "models": models,
        "note": "Six scenario families with two updates each. Variants are not independent cases. "
        "Incomplete results have no mean. No expert validation or stable ranking is claimed.",
    }


def display(value) -> str:
    return "—" if value is None else f"{value:.2f}"


def report(data: dict) -> str:
    models = data["models"]
    target_calls = sum(model["model_calls"].get(model["model"], 0) for model in models)
    judge_calls = sum(
        sum(value for key, value in model["model_calls"].items() if key != model["model"])
        for model in models
    )
    lines = [
        f"# Strategic Surprise Bench v{VERSION} — paired assessment screen",
        "",
        "Provisional model grades, not expert-validated results. One run per case and variant.",
        "",
        "All targets use the same neutral two-assessment protocol and Claude Opus 5 as the "
        "common judge.",
        "",
        "| Model | Mean /10 (all sessions graded) | Mean of graded sessions /10 | "
        "Bounds from missing grades /10 | Fully graded sessions | Rubric coverage |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for model in models:
        lines.append(
            f"| {model['label']} | {display(model['mean'])} | "
            f"{display(model['mean_of_complete_sessions'])} | "
            + "–".join(display(value) for value in model["mean_bounds_from_missing_grades"])
            + " | "
            f"{model['complete_grades']}/{model['expected_sessions']} | "
            f"{model['coverage']:.1%} |"
        )
    lines += [
        "",
        "The unqualified mean is reported only when all sessions are fully graded. The mean of "
        "graded sessions averages only the sessions in the fully-graded column; sessions the judge "
        "failed on are not a random subset, so read it with that count and the bounds. Bounds show "
        "every possible mean if each missing grade resolves anywhere from 0 to 2. They are not "
        "point estimates or statistical confidence intervals, and assume the existing accepted "
        "model grades are valid. No scoring rule was changed during the run.",
        "",
        "## Dimension bounds from missing grades",
        "",
        "| Model | " + " | ".join(DIMENSIONS) + " |",
        "|---|" + "---:|" * len(DIMENSIONS),
    ]
    for model in models:
        lines.append(
            "| "
            + model["label"]
            + " | "
            + " | ".join(
                "–".join(
                    display(value) for value in model["dimension_bounds_from_missing_grades"][dim]
                )
                for dim in DIMENSIONS
            )
            + " |"
        )
    lines += [
        "",
        "Each dimension is out of 2. A missing judgment is not a zero.",
        "",
        "## Case and variant scores",
        "",
        "| Case / variant | " + " | ".join(model["label"] for model in models) + " |",
        "|---|" + "---:|" * len(models),
    ]
    for case in list_assessment_cases():
        for variant in ("a", "b"):
            values = [
                next(
                    (
                        row["total"]
                        for row in model["rows"]
                        if row["case_id"] == case and row["variant"] == variant
                    ),
                    None,
                )
                for model in models
            ]
            lines.append(f"| {case} / {variant} | " + " | ".join(map(display, values)) + " |")
    lines += [
        "",
        "## Grading and format diagnostics",
        "",
        "| Model | Accepted rubric grades | Full-credit accepted grades | "
        "Responses above 600 words | Provider-filtered sessions |",
        "|---|---:|---:|---:|---:|",
    ]
    for model in models:
        counts = model["confirmed_grade_counts"]
        accepted = sum(counts.values())
        lines.append(
            f"| {model['label']} | {accepted}/60 | {counts.get(2, 0)}/{accepted} | "
            f"{model['responses_over_600_words']}/24 | "
            f"{model['generation_issue_sessions']} |"
        )
    lines += [
        "",
        "Word counts are whitespace-based diagnostics, not additional score penalties.",
        "",
        "## Run settings and limits",
        "",
        "- Six fictional crises, two variants each, two prose assessments per session.",
        f"- Recorded target calls: {target_calls}; judge calls: {judge_calls}.",
        "- Target output cap: 4096 tokens; prompts request no more than 600 words.",
        "- GPT-4o snapshot: `gpt-4o-2024-11-20`, temperature 0.2. "
        "Luna/Sol reasoning effort and Sonnet effort: medium.",
        "- Judge: `anthropic/claude-opus-5`, 4096-token cap, provider-default effort. "
        "Initial grading never sees later evidence or the second response.",
        "- Positive grades require response quotes matched after punctuation normalization. "
        "Missing or ungrounded judgments remain missing; the unqualified model mean is reported "
        "only when all 12 sessions are fully graded.",
        "- Common Anthropic judging may introduce provider-family bias; human checks are "
        "needed before interpreting close differences.",
        "- No human labels, repeated runs, or statistical claims of model superiority.",
        "- Source hashes, settings, raw responses, and full judge decisions are retained in "
        "the private run directory. These scores are incompatible with v0.2.",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    data = summarize(args.root)
    text = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    if args.output:
        args.output.write_text(text)
    else:
        print(text)
    if args.report:
        args.report.write_text(report(data))


if __name__ == "__main__":
    main()
