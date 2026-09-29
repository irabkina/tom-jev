"""Loading scenarios from disk.

Scenario files live under a taxonomy that the directory path encodes:

    scenarios/<split>/<task_family>/<template>/<domain>/<condition>/<lex>.yaml

    split           dev or test — see `scenarios/test/README.md`
    task_family     what Jev is asked — goal_recognition, action_prediction
    template        belief structure — first_order, second_order, attribution
    domain          surface content — bakery, clinic, workshop, ...
    condition       the cell of the template's 2x2
    lexicalization  wording variant of the same condition

The path is the source of truth for those six, so a scenario file carries
only its content and the loader fills the taxonomy in from where the file
sits. That keeps one fact in one place: moving a file reclassifies it, and
a file cannot disagree with its own directory.

`split` is first because it is the one level that must not be got wrong by
accident. Anything measured on `test` after the policy was fixed stops
being held out, so `load` takes a split and every experiment names the one
it means rather than taking whatever is on disk.

A file holds either a single scenario mapping or several under a top-level
`scenarios:` key. `schema.yaml` and `README.md` document the format and are
skipped, as is anything whose name starts with `_`.
"""

from __future__ import annotations

import pathlib
from typing import Any

import yaml

from .models import Scenario, Taxonomy

SUFFIXES = (".yaml", ".yml")
NOT_SCENARIOS = {"schema", "README"}

#: Path levels below the scenarios root, in order.
LEVELS = ("split", "task_family", "template", "domain", "condition", "lexicalization")


def scenario_files(root: pathlib.Path) -> list[pathlib.Path]:
    """Every scenario file under `root`, at any depth, sorted by path."""
    return sorted(
        p
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix in SUFFIXES
        and p.stem not in NOT_SCENARIOS
        and not p.name.startswith("_")
    )


def taxonomy(path: pathlib.Path, root: pathlib.Path) -> Taxonomy:
    """Read the taxonomy off a file's location under `root`.

    A file sitting shallower than the full depth leaves the deeper levels
    unset rather than failing, so a flat directory still loads.
    """
    parts = path.relative_to(root).parts
    values = dict(zip(LEVELS, (*parts[:-1], path.stem), strict=False))
    return Taxonomy(**values)


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


def load(root: pathlib.Path, split: str | None = None) -> list[Scenario]:
    """Load every scenario under `root`, tagging each with its taxonomy.

    `split` restricts the result to one arm of the corpus. It is not a
    convenience: `test` is held out, and an experiment that loads the whole
    root once it has content has quietly spent it. Passing None loads
    everything and is right for the corpus tests, which check both arms.

    Raises on a duplicate id — two scenarios sharing one would silently
    collapse together in analysis.
    """
    scenarios: list[Scenario] = []
    origin: dict[str, pathlib.Path] = {}

    for path in scenario_files(root):
        where = taxonomy(path, root)
        if split is not None and where.split != split:
            continue
        for scenario in parse(yaml.safe_load(path.read_text()), path):
            if scenario.id in origin:
                raise ValueError(
                    f"duplicate scenario id {scenario.id!r} in {path} and {origin[scenario.id]}"
                )
            origin[scenario.id] = path
            scenario.taxonomy = where
            scenarios.append(scenario)

    return scenarios
