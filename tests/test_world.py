"""The Neo4j world graph agrees with the in-memory reference.

`world.has_conflict` queries the graph, `analysis.world_conflict` compares
propositions in Python. The graph is the source of truth, but two
independent implementations of the same definition only stay honest if
something checks them against each other.

Skipped when no database is reachable, so the suite still runs without
Docker up.
"""

from __future__ import annotations

import pathlib

import pytest
from dotenv import load_dotenv

from tom_jev import analysis, scenarios, world

SCENARIOS = pathlib.Path(__file__).resolve().parents[1] / "scenarios"


@pytest.fixture(scope="session")
def driver():
    """A Neo4j driver, or skip the module if the database is unreachable."""
    load_dotenv()
    try:
        with world.connect() as d:
            yield d
    except Exception as error:  # noqa: BLE001 - any failure means no database
        pytest.skip(f"neo4j unavailable: {type(error).__name__}: {error}")


@pytest.fixture(scope="session")
def loaded(driver):
    """Every scenario loaded into the graph."""
    items = scenarios.load(SCENARIOS)
    for scenario in items:
        world.load(driver, scenario)
    return items


def test_graph_conflicts_match_the_reference(driver, loaded):
    """Both implementations must agree on every scenario."""
    mismatched = [
        s.id for s in loaded if world.has_conflict(driver, s.id) != analysis.world_conflict(s)
    ]
    assert not mismatched, f"graph and in-memory disagree on: {mismatched}"


def test_conflicts_name_the_agent_and_both_values(driver, loaded):
    """A reported conflict carries enough detail to be acted on."""
    conflicting = [s for s in loaded if analysis.world_conflict(s)]
    assert conflicting, "expected at least one conflicting scenario in the corpus"

    for scenario in conflicting:
        found = world.conflicts(driver, scenario.id)
        assert found, f"{scenario.id}: graph found no conflict"
        for row in found:
            assert row["agent"], "conflict must name the believing agent"
            assert row["believed"] != row["actual"], "a conflict must disagree on value"


def test_loading_is_idempotent(driver, loaded):
    """Re-loading a scenario updates in place rather than duplicating."""
    scenario = loaded[0]
    before = world.conflicts(driver, scenario.id)
    world.load(driver, scenario)
    assert world.conflicts(driver, scenario.id) == before


def test_scenarios_are_isolated_from_each_other(driver, loaded):
    """A scenario's conflicts come only from its own propositions."""
    for scenario in loaded:
        agents = {e.id for e in scenario.entities.agents}
        for row in world.conflicts(driver, scenario.id):
            assert row["agent"] in agents, (
                f"{scenario.id}: conflict attributed to {row['agent']}, "
                f"not one of its agents {sorted(agents)}"
            )
