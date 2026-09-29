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


def test_materialised_beliefs_match_the_reference(driver, loaded):
    """What the graph derives from the history must equal the reference.

    `world.materialise` works the beliefs out in Cypher — last settlement
    the chain witnessed, plus locative exclusivity — and
    `analysis.entailed_beliefs` works them out in Python. Same definition,
    two implementations, and the one that reaches the model is the graph's,
    so the Python one is what keeps it honest.
    """
    for scenario in loaded:
        if not scenario.history:
            continue
        derived = {}
        for mental in world.materialise(driver, scenario):
            holders, held = world.unfold(mental)
            nested = held
            for holder in reversed(holders[1:]):
                nested = held.__class__(
                    predicate=world.NESTING_PREDICATE, subject=holder, proposition=nested
                )
            derived[(holders[0], nested.signature())] = held.value
        assert derived == analysis.entailed_beliefs(scenario), scenario.id


def test_materialising_restricts_to_one_agent(driver, loaded):
    """A pass gets the question's agent, not everyone in the scenario.

    The history represents one agent's access by design, so asking for
    another agent's beliefs should return nothing rather than someone
    else's. See `analysis.history_matches_mental_state`.
    """
    for scenario in loaded:
        if not scenario.history:
            continue
        asked = scenario.question.agent
        assert all(m.agent == asked for m in world.materialise(driver, scenario, agent=asked))


def test_derived_beliefs_are_stored_beside_the_stated_ones(driver, loaded):
    """The graph must be able to say which beliefs it worked out.

    Materialising writes under the `derived` perspective rather than over
    `belief`, so a reader can tell a belief the graph was told from one it
    derived — and so the two can be compared at all.
    """
    scenario = next(s for s in loaded if s.history and s.mental_state)
    world.materialise(driver, scenario)
    with driver.session() as session:
        rows = session.run(
            """
            MATCH (p:Proposition {scenario: $scenario})
            RETURN p.perspective AS perspective, count(*) AS n
            """,
            scenario=scenario.id,
        ).data()
    perspectives = {r["perspective"]: r["n"] for r in rows}
    assert world.DERIVED in perspectives
    assert world.BELIEF in perspectives


def test_supersession_survives_without_exclusivity(driver, loaded):
    """Being out of date and being negated are separate things.

    They were not always. Supersession of a locative claim used to be
    carried by exclusivity — a later sighting replaced an earlier one
    only because seeing a thing in the office is seeing it not in the
    conference room — so asking for the beliefs without exclusivity left
    two sightings settling different keys, neither replacing the other,
    and the agent believing the meeting was in two places.

    `world.load` now writes SUPERSEDES between settlements at load time,
    which is a fact about the events and not about who saw them. So the
    unexclusive rendering is sound: fewer claims, none of them in
    contradiction.
    """
    for scenario in loaded:
        if not scenario.history:
            continue
        direct = world.materialise(
            driver, scenario, agent=scenario.question.agent, exclusivity=False
        )
        placed = {}
        for mental in direct:
            inner = mental.proposition.innermost()
            if inner.predicate != "located" or inner.value is not True:
                continue
            key = (mental.agent, inner.subject)
            assert key not in placed, (
                f"{scenario.id}: {key} placed at both {placed.get(key)} and {inner.location}"
            )
            placed[key] = inner.location


def test_the_graph_and_the_reference_agree_on_supersession(driver, loaded):
    """`analysis._supersedes` and the SUPERSEDES edge are one definition.

    The graph writes the edge at load; the reference recomputes it when
    working out what a history entails. Two implementations again, so
    something has to check them.
    """
    for scenario in loaded:
        if len(scenario.history) < 2:
            continue
        with driver.session() as session:
            edges = {
                (row["later"], row["earlier"])
                for row in session.run(
                    """
                    MATCH (l:Entity:Settlement {scenario: $scenario})-[:SUPERSEDES]->
                          (e:Entity:Settlement {scenario: $scenario})
                    RETURN l.index AS later, e.index AS earlier
                    """,
                    scenario=scenario.id,
                ).data()
            }
        expected = {
            (j, i)
            for i, earlier in enumerate(scenario.history)
            for j, later in enumerate(scenario.history)
            if j > i and analysis._supersedes(later, earlier)
        }
        assert edges == expected, scenario.id
