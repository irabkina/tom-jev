"""Background knowledge about the predicates themselves.

What a predicate's arguments mean is a standing fact about the domain, not
about any episode, so it is declared in `knowledge/predicates.yaml` beside
what goals require rather than inferred from the shape of a proposition.

The only thing declared so far is functionality: whether at most one value
of an argument can hold at once. `located` is functional in its location
and `available` is not, which is the difference between a later sighting
elsewhere meaning the thing moved and it meaning nothing at all.

Both the graph and the in-memory reference read this, so there is one
statement of the algebra rather than two hardcoded guesses that happen to
agree. `tests/test_world.py` holds them to each other.
"""

from __future__ import annotations

import functools
import pathlib

import yaml

#: Arguments a predicate may be declared functional in. Only `location` is
#: implemented; anything else raises rather than being quietly dropped,
#: because a declaration that does nothing is worse than no declaration.
SUPPORTED = frozenset({"location"})

PREDICATES = pathlib.Path(__file__).resolve().parents[2] / "knowledge" / "predicates.yaml"


@functools.cache
def functional() -> dict[str, str]:
    """Each predicate that is functional, and the argument it is functional in."""
    if not PREDICATES.exists():
        return {}
    document = yaml.safe_load(PREDICATES.read_text()) or {}
    declared: dict[str, str] = {}
    for entry in document.get("predicates", []):
        argument = entry.get("functional_in")
        if argument is None:
            continue
        if argument not in SUPPORTED:
            raise ValueError(
                f"{entry['name']} is declared functional in {argument!r}, which is not "
                f"implemented; supported: {sorted(SUPPORTED)}"
            )
        declared[entry["name"]] = argument
    return declared


def functional_in_location() -> list[str]:
    """Predicates for which a location is exclusive — one place at a time."""
    return sorted(name for name, argument in functional().items() if argument == "location")
