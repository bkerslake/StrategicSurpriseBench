"""Opt-in live provider smoke test; no credentials are read or written by this script."""

from __future__ import annotations

import os
import sys
import tempfile

from inspect_ai import eval

from strategic_surprise_bench.inspect_task import strategic_surprise


def main() -> int:
    configured = os.environ.get("SSB_SMOKE_MODELS", "")
    models = [item.strip() for item in configured.split(",") if item.strip()]
    if not models:
        print("SKIP: set SSB_SMOKE_MODELS to explicit provider/model IDs")
        return 0
    failures: list[str] = []
    with tempfile.TemporaryDirectory(prefix="strategic-surprise-smoke-") as log_dir:
        for model in models:
            logs = eval(
                strategic_surprise(condition="plain", case_id="lattice_signal"),
                model=model,
                limit=1,
                display="none",
                log_dir=log_dir,
            )
            status = logs[0].status if logs else "missing-log"
            print(f"{model}: {status}")
            if status != "success":
                failures.append(model)
    if failures:
        print("FAILED: " + ", ".join(failures), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
