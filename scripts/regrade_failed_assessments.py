"""Explicit, bounded retries of missing grades; preserve accepted grades and raw attempts."""

import argparse
import asyncio
import json
from pathlib import Path

from inspect_ai.model import ChatMessageSystem, ChatMessageUser, GenerateConfig, get_model
from run_assessment_pilot import load_credentials

from strategic_surprise_bench.assessment import AssessmentTranscript, GradeSheet
from strategic_surprise_bench.assessment_scoring import (
    JUDGE_INSTRUCTIONS,
    parse_stage_grades,
    review_packet,
    score_assessment,
)


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


async def run(source, destination):
    destination.mkdir(parents=True, exist_ok=False)
    model = get_model("anthropic/claude-opus-5")
    semaphore = asyncio.Semaphore(2)

    async def retry(path):
        transcript = AssessmentTranscript.model_validate_json(path.read_text())
        grade_path = path.with_suffix(".grades.json")
        if not grade_path.exists():
            return
        original = GradeSheet.model_validate_json(grade_path.read_text())
        sheet = original.model_copy(deep=True)
        before = score_assessment(transcript, original)
        attempts = []
        if not transcript.generation_issues:
            for stage in (1, 2):
                packet = review_packet(transcript, stage)
                expected = {c["dimension"] for c in packet["criteria"]}
                for number in range(1, 4):
                    current = score_assessment(transcript, sheet)
                    missing = expected.intersection(current["missing"])
                    if not missing:
                        break
                    attempt = {"stage": stage, "attempt": number, "missing": sorted(missing)}
                    try:
                        async with semaphore:
                            output = await model.generate(
                                [
                                    ChatMessageSystem(content=JUDGE_INSTRUCTIONS),
                                    ChatMessageUser(content=json.dumps(packet, ensure_ascii=False)),
                                ],
                                config=GenerateConfig(max_tokens=4096, max_retries=2, timeout=240),
                            )
                        attempt["output"] = output.model_dump(mode="json")
                        if any(
                            c.stop_reason in {"max_tokens", "content_filter"}
                            for c in output.choices
                        ):
                            raise ValueError("Incomplete judge output")
                        grades = parse_stage_grades(output.completion, expected)
                        replacements = {g.dimension: g for g in grades if g.dimension in missing}
                        candidate = sheet.model_copy(deep=True)
                        candidate.grades = [replacements.get(g.dimension, g) for g in sheet.grades]
                        candidate_score = score_assessment(transcript, candidate)
                        # Accept the first valid retry, regardless of score.
                        accepted = {
                            d for d in missing if candidate_score["dimensions"][d] is not None
                        }
                        sheet.grades = [
                            replacements[g.dimension] if g.dimension in accepted else g
                            for g in sheet.grades
                        ]
                        attempt["accepted"] = sorted(accepted)
                    except Exception as error:
                        attempt["error"] = type(error).__name__
                    attempts.append(attempt)
                    save(destination / (path.stem + ".attempts.json"), attempts)
                    print(
                        json.dumps(
                            {
                                "sample": path.stem,
                                "stage": stage,
                                "attempt": number,
                                "accepted": attempt.get("accepted", []),
                                "error": attempt.get("error"),
                            }
                        ),
                        flush=True,
                    )
        after = score_assessment(transcript, sheet)
        for dimension, value in before["dimensions"].items():
            if value is not None:
                assert after["dimensions"][dimension] == value
                assert next(g for g in original.grades if g.dimension == dimension) == next(
                    g for g in sheet.grades if g.dimension == dimension
                )
        save(destination / path.name, transcript.model_dump())
        save(destination / grade_path.name, sheet.model_dump())
        save(destination / (path.stem + ".score.json"), after)
        save(
            destination / (path.stem + ".audit.json"),
            {"before": before, "after": after, "judge_calls": len(attempts)},
        )

    await asyncio.gather(*(retry(p) for p in sorted(source.glob("sample-???.json"))))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    load_credentials(args.env_file)
    asyncio.run(run(args.source, args.output_dir))
