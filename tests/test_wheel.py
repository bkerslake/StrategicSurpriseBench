from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def test_built_wheel_exposes_all_scenarios_when_present():
    """Regression test for resource loading from a zip-imported wheel."""
    wheels = sorted(Path("dist").glob("strategic_surprise_bench-*.whl"))
    if not wheels:
        return
    code = (
        "import sys; "
        f"sys.path.insert(0, {str(wheels[-1])!r}); "
        "from strategic_surprise_bench.loader import load_all_cases; "
        "assert len(load_all_cases()) == 6"
    )
    subprocess.run([sys.executable, "-I", "-c", code], check=True)
