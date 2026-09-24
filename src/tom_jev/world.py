"""The world state as a Neo4j graph.

A scenario's objective `world_state` and its agents' `mental_state` are both
propositions over the same entities, so both are written into one graph and
distinguished by a `kind` property. A conflict is then a graph query rather
than a tuple comparison in Python: a belief and a world fact that share a
proposition but disagree on its value.

Shape:

    (:Entity {scenario, id, name, kind})

    (:Proposition {scenario, kind, predicate, value, holder, signature})
        -[:SUBJECT]->  (:Entity)
        -[:OBJECT]->   (:Entity)      optional
        -[:LOCATION]-> (:Entity)      optional

`kind` is "world" for objective facts and "belief" for represented mental
states; `holder` names the agent for a belief and is the empty string for a
world fact, which has none. Empty rather than null because Neo4j refuses to
MERGE on a null property, and holder has to be part of the merge key so two
agents can hold conflicting beliefs about the same proposition.

Arguments are held as relationships so the graph can be traversed and
inspected, and `signature` — predicate plus the argument ids — is stored
alongside so exact-match conflict detection is a property comparison rather
than a pattern comparison over optional relationships. The duplication is
deliberate: the relationships are what make derived queries possible, the
signature is what makes the direct query simple.

Everything is scoped by scenario id, so one database can hold many
scenarios without them interfering.
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from neo4j import Driver, GraphDatabase

from .models import Proposition, Scenario

ARGUMENTS = ("subject", "object", "location")


@contextmanager
def connect(
    uri: str | None = None, user: str | None = None, password: str | None = None
) -> Iterator[Driver]:
    """Open a Neo4j driver, reading NEO4J_* from the environment by default."""
    uri = uri or os.environ["NEO4J_URI"]
    user = user or os.environ["NEO4J_USER"]
    password = password or os.environ["NEO4J_PASSWORD"]
    with GraphDatabase.driver(uri, auth=(user, password)) as driver:
        driver.verify_connectivity()
        yield driver


def signature(proposition: Proposition) -> str:
    """Identify a proposition by predicate and arguments, ignoring its value.

    Two propositions with the same signature make the same claim, so they
    conflict exactly when their values differ.
    """
    args = "|".join(str(getattr(proposition, a) or "") for a in ARGUMENTS)
    return f"{proposition.predicate}|{args}"


def _write_proposition(
    tx, scenario_id: str, proposition: Proposition, kind: str, holder: str | None
) -> None:
    holder = holder or ""
    tx.run(
        """
        MERGE (p:Proposition {scenario: $scenario, kind: $kind,
                              holder: $holder, signature: $signature})
        SET p.predicate = $predicate, p.value = $value
        """,
        scenario=scenario_id,
        kind=kind,
        holder=holder,
        signature=signature(proposition),
        predicate=proposition.predicate,
        value=proposition.value,
    )
    for argument in ARGUMENTS:
        target = getattr(proposition, argument)
        if target is None:
            continue
        tx.run(
            f"""
            MATCH (p:Proposition {{scenario: $scenario, kind: $kind,
                                   holder: $holder, signature: $signature}})
            MERGE (e:Entity {{scenario: $scenario, id: $target}})
            MERGE (p)-[:{argument.upper()}]->(e)
            """,
            scenario=scenario_id,
            kind=kind,
            holder=holder,
            signature=signature(proposition),
            target=target,
        )


def load(driver: Driver, scenario: Scenario) -> None:
    """Write a scenario's entities, world state and beliefs into the graph.

    Idempotent: re-loading the same scenario updates in place rather than
    duplicating.
    """
    with driver.session() as session:
        for kind, group in (
            ("agent", scenario.entities.agents),
            ("location", scenario.entities.locations),
            ("object", scenario.entities.objects),
        ):
            for entity in group:
                session.run(
                    """
                    MERGE (e:Entity {scenario: $scenario, id: $id})
                    SET e.name = $name, e.kind = $kind
                    """,
                    scenario=scenario.id,
                    id=entity.id,
                    name=entity.name,
                    kind=kind,
                )

        for fact in scenario.world_state:
            session.execute_write(_write_proposition, scenario.id, fact, "world", None)

        for mental in scenario.mental_state:
            session.execute_write(
                _write_proposition, scenario.id, mental.proposition, "belief", mental.agent
            )


def conflicts(driver: Driver, scenario_id: str) -> list[dict]:
    """Every belief that contradicts an objective world fact.

    A conflict is a belief and a world fact with the same signature — same
    predicate over the same arguments — but different values.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (b:Proposition {scenario: $scenario, kind: 'belief'})
        MATCH (w:Proposition {scenario: $scenario, kind: 'world'})
        WHERE b.signature = w.signature AND b.value <> w.value
        RETURN b.holder AS agent, b.predicate AS predicate,
               b.value AS believed, w.value AS actual
        ORDER BY agent, predicate
        """,
        scenario=scenario_id,
    )
    return [record.data() for record in records]


def has_conflict(driver: Driver, scenario_id: str) -> bool:
    """Does any represented belief contradict the world state?"""
    return bool(conflicts(driver, scenario_id))


def clear(driver: Driver, scenario_id: str | None = None) -> int:
    """Delete one scenario's nodes, or every scenario's. Returns nodes removed."""
    if scenario_id is None:
        query, parameters = "MATCH (n) DETACH DELETE n RETURN count(n) AS n", {}
    else:
        query, parameters = (
            "MATCH (n {scenario: $scenario}) DETACH DELETE n RETURN count(n) AS n",
            {"scenario": scenario_id},
        )
    records, _, _ = driver.execute_query(query, **parameters)
    return records[0]["n"] if records else 0
