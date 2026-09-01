from __future__ import annotations

import tomllib
from pathlib import Path


def test_required_provider_clients_are_declared():
    project = tomllib.loads(Path("pyproject.toml").read_text())["project"]
    dependencies = project["dependencies"]
    assert any(item.startswith("openai>=") for item in dependencies)
    assert any(item.startswith("anthropic>=") for item in dependencies)
