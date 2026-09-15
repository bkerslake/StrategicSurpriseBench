"""Commands for the neutral-assessment benchmark; old commands require `legacy`."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

from strategic_surprise_bench.assessment import (
    SYSTEM,
    AssessmentCase,
    AssessmentTranscript,
    GradeSheet,
    list_assessment_cases,
    load_assessment_case,
    render_assessment,
)
from strategic_surprise_bench.assessment_scoring import (
    grade_template,
    judge_assessment,
    review_packet,
    score_assessment,
    summarize_assessments,
)


def _read(path: str):
    return json.loads(Path(path).read_text())


def _transcript(path: str) -> AssessmentTranscript:
    return AssessmentTranscript.model_validate(_read(path))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="strategic-surprise")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("list", help="List the six v0.3 fictional crises")
    commands.add_parser("validate", help="Validate current cases and matched updates")
    preview = commands.add_parser("preview", help="Show exactly what the target receives")
    preview.add_argument("--case", required=True)
    preview.add_argument("--stage", type=int, choices=[1, 2], default=1)
    preview.add_argument("--variant", choices=["a", "b"], default="a")
    for name, help_text in [
        ("review", "Export a stage-isolated review packet"),
        ("grade-template", "Create an empty human grade sheet bound to a transcript"),
        ("grade", "Run provisional grading with one explicitly chosen judge model"),
        ("score", "Score a prose transcript using optional human/model grades"),
    ]:
        sub = commands.add_parser(name, help=help_text)
        sub.add_argument("transcript")
        sub.add_argument("--output")
        if name == "review":
            sub.add_argument("--stage", type=int, choices=[1, 2], required=True)
        if name == "grade":
            sub.add_argument("--judge", required=True)
        if name == "score":
            sub.add_argument("--grades")
    export = commands.add_parser("extract", help="Export v0.3 transcripts from an Inspect log")
    export.add_argument("log")
    export.add_argument("--output-dir", required=True)
    summary = commands.add_parser("summarize", help="Summarize a JSON array of v0.3 scores")
    summary.add_argument("results")
    summary.add_argument("--output")
    schema = commands.add_parser("schema", help="Export an offline artifact schema")
    schema.add_argument("kind", choices=["transcript", "grades", "scenario"])
    schema.add_argument("--output")
    legacy = commands.add_parser("legacy", help="Run archived v0.2 commands (incompatible scores)")
    legacy.add_argument("args", nargs=argparse.REMAINDER)
    return parser


def _run(args: argparse.Namespace):
    if args.command == "list":
        return [
            {
                "id": case.id,
                "title": case.title,
                "domain": case.domain,
                "version": case.version,
                "variants": [item.id for item in case.updates],
            }
            for case in map(load_assessment_case, list_assessment_cases())
        ]
    if args.command == "validate":
        cases = [load_assessment_case(item) for item in list_assessment_cases()]
        return {
            "passed": bool(cases),
            "cases": len(cases),
            "variants": sum(len(case.updates) for case in cases),
            "version": "0.3.0",
        }
    if args.command == "preview":
        return {
            "system": SYSTEM,
            "user": render_assessment(load_assessment_case(args.case), args.stage, args.variant),
        }
    if args.command in {"review", "grade-template", "grade", "score"}:
        transcript = _transcript(args.transcript)
        if args.command == "review":
            return review_packet(transcript, args.stage)
        if args.command == "grade-template":
            return grade_template(transcript).model_dump()
        if args.command == "grade":
            return asyncio.run(judge_assessment(transcript, args.judge)).model_dump()
        sheet = GradeSheet.model_validate(_read(args.grades)) if args.grades else None
        return score_assessment(transcript, sheet)
    if args.command == "extract":
        from inspect_ai.log import read_eval_log

        log = read_eval_log(args.log)
        destination = Path(args.output_dir)
        destination.mkdir(parents=True, exist_ok=True)
        exported = []
        skipped = 0
        for index, sample in enumerate(log.samples or []):
            raw = (sample.metadata or {}).get("assessment_transcript")
            if raw is None:
                skipped += 1
                continue
            transcript = AssessmentTranscript.model_validate(raw)
            path = destination / f"sample-{index + 1:03d}.json"
            # Exclusive creation protects an earlier review batch from accidental overwrite.
            with path.open("x") as stream:
                stream.write(transcript.model_dump_json(indent=2) + "\n")
            # Preserve existing provisional labels so review never requires paid re-grading.
            for score in (sample.scores or {}).values():
                metadata = score.metadata or {}
                raw_sheet = metadata.get("grade_sheet")
                if raw_sheet is not None:
                    sheet = GradeSheet.model_validate(raw_sheet)
                    result = score_assessment(transcript, sheet)
                    with path.with_suffix(".grades.json").open("x") as stream:
                        stream.write(sheet.model_dump_json(indent=2) + "\n")
                    with path.with_suffix(".score.json").open("x") as stream:
                        stream.write(json.dumps(result, indent=2) + "\n")
                    break
            exported.append(str(path.resolve()))
        return {"exported": exported, "skipped_incomplete_samples": skipped}
    if args.command == "summarize":
        return summarize_assessments(_read(args.results))
    if args.command == "schema":
        cls = {
            "transcript": AssessmentTranscript,
            "grades": GradeSheet,
            "scenario": AssessmentCase,
        }[args.kind]
        return cls.model_json_schema()
    if args.command == "legacy":
        from strategic_surprise_bench.legacy_cli import main as legacy_main

        legacy_main(args.args)
    raise ValueError(f"unknown command: {args.command}")


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        value = _run(args)
        text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        if getattr(args, "output", None):
            Path(args.output).write_text(text)
        else:
            print(text, end="")
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
        sys.exit(2)


if __name__ == "__main__":
    main()
