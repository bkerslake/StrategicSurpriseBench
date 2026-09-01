"""Scenario discovery and validation."""

from __future__ import annotations

from importlib.resources import files

import yaml

from strategic_surprise_bench.models import ScenarioCase


def _scenario_root():
    """Return a Traversable so scenarios also load from zipped wheels."""
    return files("strategic_surprise_bench").joinpath("scenarios")


def list_case_ids() -> list[str]:
    return sorted(
        item.name.removesuffix(".yaml")
        for item in _scenario_root().iterdir()
        if item.is_file() and item.name.endswith(".yaml")
    )


def load_case(case_id: str) -> ScenarioCase:
    resource = _scenario_root().joinpath(f"{case_id}.yaml")
    if not resource.is_file():
        available = ", ".join(list_case_ids())
        raise KeyError(f"unknown case {case_id!r}; available cases: {available}")
    raw = yaml.safe_load(resource.read_text(encoding="utf-8"))
    return ScenarioCase.model_validate(raw)


def load_all_cases() -> list[ScenarioCase]:
    return [load_case(case_id) for case_id in list_case_ids()]
