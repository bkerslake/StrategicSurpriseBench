"""Run an explicitly configured live v0.3 screen; never log credential values."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from dotenv import dotenv_values

from strategic_surprise_bench.assessment import VERSION


def load_credentials(path: str) -> None:
    values = dotenv_values(path, interpolate=False)
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
        if values.get(key):
            os.environ[key] = values[key]
    missing = [key for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY") if not os.environ.get(key)]
    if missing:
        raise ValueError("Missing credential variables: " + ", ".join(missing))


async def preflight() -> None:
    from anthropic import AsyncAnthropic
    from openai import AsyncOpenAI

    async def openai_models():
        async with AsyncOpenAI(timeout=30, max_retries=0) as client:
            page = await client.models.list()
            available = {model.id for model in page.data}
            requested = ["gpt-4o", "gpt-4o-2024-11-20", "gpt-5.6-luna"]
            print(
                json.dumps(
                    {
                        "provider": "openai",
                        "available": {name: name in available for name in requested},
                    }
                ),
                flush=True,
            )

    async def anthropic_models():
        async with AsyncAnthropic(timeout=30, max_retries=0) as client:
            page = await client.models.list(limit=100)
            print(
                json.dumps(
                    {
                        "provider": "anthropic",
                        "available": [
                            model.id
                            for model in page.data
                            if "sonnet" in model.id or "opus" in model.id
                        ],
                    }
                ),
                flush=True,
            )

    results = await asyncio.gather(openai_models(), anthropic_models(), return_exceptions=True)
    if any(isinstance(result, Exception) for result in results):
        for result in results:
            if isinstance(result, Exception):
                print(
                    json.dumps(
                        {
                            "preflight_error": type(result).__name__,
                            "status_code": getattr(result, "status_code", None),
                        }
                    ),
                    flush=True,
                )
        raise RuntimeError("Provider preflight failed")


def run(model: str, judge: str, output_dir: str) -> None:
    from inspect_ai import eval

    from strategic_surprise_bench.assessment_task import strategic_surprise

    destination = Path(output_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    if list(destination.glob("*.eval")):
        raise ValueError(
            "Output directory already has a run; use a new directory to avoid duplication"
        )
    os.environ["INSPECT_TRACE_FILE"] = str(destination / "inspect-trace.log")
    settings = {"max_retries": 2, "timeout": 240, "max_tokens": 4096}
    if model.startswith("openai/gpt-5"):
        settings["reasoning_effort"] = "medium"
    elif model.startswith("anthropic/"):
        settings["effort"] = "medium"
    elif model.startswith("openai/gpt-4o"):
        settings["temperature"] = 0.2
    root = Path(__file__).resolve().parents[1]
    source = root / "src" / "strategic_surprise_bench"
    paths = sorted(source.glob("assessment*.py")) + sorted((source / "assessments").glob("*.yaml"))
    manifest = {
        "benchmark_version": VERSION,
        "started_at": datetime.now(UTC).isoformat(),
        "target": model,
        "judge": judge,
        "epochs": 1,
        "variants": "both",
        "target_settings": settings,
        "judge_settings": {"max_tokens": 4096},
        "case_count": 6,
        "session_count": 12,
        "source_hashes": {
            str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in paths
        },
        "status": "running",
    }
    manifest_path = destination / "run-manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"event": "started", "model": model, "judge": judge}), flush=True)
    logs = eval(
        strategic_surprise(judge=judge),
        model=model,
        epochs=1,
        display="none",
        log_dir=str(destination),
        max_samples=2,
        fail_on_error=False,
        **settings,
    )
    manifest.update(
        status=logs[0].status if logs else "no_log", completed_at=datetime.now(UTC).isoformat()
    )
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(
        json.dumps(
            {
                "event": "finished",
                "model": model,
                "status": manifest["status"],
                "samples": len(logs[0].samples or []) if logs else 0,
            }
        ),
        flush=True,
    )
    if not logs or logs[0].status != "success":
        raise RuntimeError("Evaluation did not finish successfully; inspect the private run log")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", required=True)
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--model")
    parser.add_argument("--judge")
    parser.add_argument("--output-dir")
    args = parser.parse_args()
    load_credentials(args.env_file)
    if args.preflight:
        asyncio.run(preflight())
    else:
        if not all((args.model, args.judge, args.output_dir)):
            parser.error("--model, --judge, and --output-dir are required for a live run")
        run(args.model, args.judge, args.output_dir)


if __name__ == "__main__":
    main()
