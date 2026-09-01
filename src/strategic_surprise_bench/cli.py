"""Command-line validation, offline scoring, calibration, and reporting."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

from strategic_surprise_bench.calibration import (
    evaluate_calibration,
    gate_allows_automated_scoring,
    load_corpus,
)
from strategic_surprise_bench.loader import list_case_ids, load_case
from strategic_surprise_bench.mock import transcript_payload
from strategic_surprise_bench.models import RoundResponse, ValidationDecision
from strategic_surprise_bench.reporting import RunRecord, summarize_runs
from strategic_surprise_bench.scoring import score_session
from strategic_surprise_bench.validation import validate_repository_cases


def _write_or_print(value: object, destination: str | None) -> None:
    text = json.dumps(value, indent=2, sort_keys=True, default=str) + "\n"
    if destination:
        Path(destination).write_text(text)
    else:
        print(text, end="")


def _validate(_: argparse.Namespace) -> int:
    report = validate_repository_cases()
    _write_or_print(asdict(report), None)
    return 0 if report.passed else 1


def _list(_: argparse.Namespace) -> int:
    rows = []
    for case_id in list_case_ids():
        case = load_case(case_id)
        rows.append(
            {
                "id": case_id,
                "title": case.manifest.title,
                "domain": case.manifest.domain,
                "version": case.manifest.version,
            }
        )
    _write_or_print(rows, None)
    return 0


def _mock(args: argparse.Namespace) -> int:
    payload = transcript_payload(load_case(args.case), args.quality)
    _write_or_print(payload, args.output)
    return 0


def _score(args: argparse.Namespace) -> int:
    payload = json.loads(Path(args.transcript).read_text())
    case_id = args.case or payload.get("case_id")
    if not case_id:
        raise ValueError("case ID must be supplied in the transcript or with --case")
    raw_responses = payload.get("responses", payload)
    responses = [RoundResponse.model_validate(item) for item in raw_responses]
    decisions: list[ValidationDecision] = []
    if args.decisions:
        raw_decisions = json.loads(Path(args.decisions).read_text())
        decisions = [ValidationDecision.model_validate(item) for item in raw_decisions]
    result = score_session(load_case(case_id), responses, decisions)
    _write_or_print(result.model_dump(mode="json"), args.output)
    return 0


def _calibrate(args: argparse.Namespace) -> int:
    report = evaluate_calibration(load_corpus(args.corpus))
    _write_or_print(report.to_dict(), args.output)
    return 0 if report.passed else 1


def _release_check(args: argparse.Namespace) -> int:
    scenario_report = validate_repository_cases()
    calibration_passed = gate_allows_automated_scoring(args.calibration_report)
    payload = {
        "scenario_validation": asdict(scenario_report),
        "calibration_gate": calibration_passed,
        "passed": scenario_report.passed and calibration_passed,
        "note": (
            "Synthetic tests never satisfy the expert calibration gate."
            if not calibration_passed
            else "Locked expert holdout and scenario-review gates passed."
        ),
    }
    _write_or_print(payload, None)
    return 0 if payload["passed"] else 1


def _summarize(args: argparse.Namespace) -> int:
    raw = json.loads(Path(args.records).read_text())
    records = [RunRecord.model_validate(item) for item in raw]
    report = summarize_runs(records, bootstrap_samples=args.bootstrap_samples)
    _write_or_print(report, args.output)
    return 0


def _schema(args: argparse.Namespace) -> int:
    from strategic_surprise_bench.calibration import CalibrationCorpus
    from strategic_surprise_bench.models import ScenarioCase

    value = (
        RoundResponse.model_json_schema()
        if args.kind == "response"
        else ScenarioCase.model_json_schema()
        if args.kind == "scenario"
        else CalibrationCorpus.model_json_schema()
    )
    _write_or_print(value, args.output)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="strategic-surprise")
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate = subparsers.add_parser("validate", help="Validate all six cases and leakage rules")
    validate.set_defaults(handler=_validate)
    list_command = subparsers.add_parser("list", help="List public cases")
    list_command.set_defaults(handler=_list)

    mock = subparsers.add_parser("mock", help="Create a credential-free test transcript")
    mock.add_argument("--case", required=True, choices=list_case_ids())
    mock.add_argument(
        "--quality", default="perfect", choices=["perfect", "calibrated", "uniform", "wrong"]
    )
    mock.add_argument("--output")
    mock.set_defaults(handler=_mock)

    score = subparsers.add_parser("score", help="Score a three-round transcript")
    score.add_argument("transcript")
    score.add_argument("--case", choices=list_case_ids())
    score.add_argument("--decisions", help="Accepted judge or adjudicated human decisions JSON")
    score.add_argument("--output")
    score.set_defaults(handler=_score)

    calibrate = subparsers.add_parser(
        "calibrate", help="Evaluate locked judge labels against expert labels"
    )
    calibrate.add_argument("corpus")
    calibrate.add_argument("--output")
    calibrate.set_defaults(handler=_calibrate)

    release = subparsers.add_parser(
        "release-check", help="Fail unless scenarios and expert calibration pass"
    )
    release.add_argument(
        "--calibration-report",
        default="calibration/private/gate-report.json",
        help=(
            "Locked holdout gate report (default: calibration/private/gate-report.json). "
            "A missing report fails closed."
        ),
    )
    release.set_defaults(handler=_release_check)

    summarize = subparsers.add_parser("summarize", help="Summarize pilot run records")
    summarize.add_argument("records")
    summarize.add_argument("--bootstrap-samples", type=int, default=5000)
    summarize.add_argument("--output")
    summarize.set_defaults(handler=_summarize)

    schema = subparsers.add_parser("schema", help="Export a JSON schema")
    schema.add_argument("kind", choices=["response", "scenario", "calibration"])
    schema.add_argument("--output")
    schema.set_defaults(handler=_schema)
    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        code = args.handler(args)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        parser.error(str(error))
        return
    sys.exit(code)


if __name__ == "__main__":
    main()
