"""The sparse/rich contrast the experiment depends on.

The coffee set is a 2x2 over whether a cup is actually available and
whether Sam believes one is. Two variants at a time share a world and
differ only in belief:

    true_positive  / false_negative   cup available
    false_positive / true_negative    cup unavailable

Since sparse withholds mental state, each of those pairs must render
identically under sparse and differently under rich. If a sparse pair ever
diverges, some belief has leaked into the observable representation and the
manipulation is confounded; if a rich pair ever collapses, the belief is not
reaching the model at all.
"""

from __future__ import annotations

import pathlib

import pytest

from tom_jev import representation, scenarios

SCENARIOS = pathlib.Path(__file__).resolve().parents[1] / "scenarios"

# Variant pairs that share a world state and differ only in Sam's belief.
SAME_WORLD = [
    ("true_positive", "false_negative"),
    ("false_positive", "true_negative"),
]


@pytest.fixture(scope="session")
def coffee() -> dict[str, object]:
    """The coffee scenario set, keyed by variant."""
    items = {
        s.variant.type: s
        for s in scenarios.load(SCENARIOS)
        if s.scenario_set == "coffee" and s.variant
    }
    missing = {v for pair in SAME_WORLD for v in pair} - set(items)
    if missing:
        pytest.fail(f"missing coffee variants: {sorted(missing)}")
    return items


@pytest.mark.parametrize(("a", "b"), SAME_WORLD)
def test_sparse_is_identical_when_only_belief_differs(coffee, a, b):
    """Sparse withholds mental state, so same world means same rendering."""
    assert representation.sparse(coffee[a]) == representation.sparse(coffee[b])


@pytest.mark.parametrize(("a", "b"), SAME_WORLD)
def test_rich_differs_when_belief_differs(coffee, a, b):
    """Rich includes mental state, so differing beliefs must show up."""
    assert representation.rich(coffee[a]) != representation.rich(coffee[b])
