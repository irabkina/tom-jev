"""Loading scenarios from disk.

A scenario file is YAML (`.yaml` or `.yml`) and holds either a single
scenario mapping, or a set of them under a top-level `scenarios:` key — the
latter keeps structurally matched variants side by side in one file, which
is how `coffee.yaml` is organised.

`schema.yaml` documents the format and is not itself a scenario, so it is
skipped.
"""

from __future__ import annotations

import pathlib
from typing import Any

import yaml

from .models import Scenario

SUFFIXES = (".yaml", ".yml")
NOT_SCENARIOS = {"schema", "README"}


def scenario_files(directory: pathlib.Path) -> list[pathlib.Path]:
    """Every scenario file in `directory`, sorted, excluding documentation."""
    return sorted(
        p
        for p in directory.iterdir()
        if p.suffix in SUFFIXES and p.stem not in NOT_SCENARIOS and not p.name.startswith("_")
    )


def parse(document: Any, source: pathlib.Path) -> list[Scenario]:
    """Turn one parsed YAML document into scenarios.

    Accepts either a single scenario mapping or `{"scenarios": [...]}`.
    """
    if not isinstance(document, dict):
        raise TypeError(f"{source}: expected a mapping, got {type(document).__name__}")

    entries = document.get("scenarios", [document])
    if not isinstance(entries, list):
        raise TypeError(f"{source}: 'scenarios' must be a list, got {type(entries).__name__}")

    return [Scenario.model_validate(entry) for entry in entries]


def load(directory: pathlib.Path) -> list[Scenario]:
    """Load every scenario under `directory`.

    Raises on a duplicate id — two scenarios sharing one would silently
    collapse together in analysis.
    """
    scenarios: list[Scenario] = []
    origin: dict[str, pathlib.Path] = {}

    for path in scenario_files(directory):
        for scenario in parse(yaml.safe_load(path.read_text()), path):
            if scenario.id in origin:
                raise ValueError(
                    f"duplicate scenario id {scenario.id!r} in {path} and {origin[scenario.id]}"
                )
            origin[scenario.id] = path
            scenarios.append(scenario)

    return scenarios
