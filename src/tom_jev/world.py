"""The world state as a Neo4j graph.

Ontology
--------

    Entity
    ├── Agent
    ├── Object
    ├── Location
    └── Event

    Proposition                     a claim; not an Entity, it qualifies one

    (:Entity)-[:SUBJECT_OF]->(:Proposition {predicate, value})
    (:Proposition)-[:LOCATION]->(:Location)     optional
    (:Proposition)-[:OBJECT]->(:Entity)         optional

    (:Agent)-[:HAS_GOAL {type}]->(:Entity)

    (:Agent)-[:ACTOR_OF]->(:Event)
    (:Event)-[:TO]->(:Location)                 optional
    (:Event)-[:OBJECT]->(:Entity)               optional

Reifying the proposition makes every predicate the same shape whatever its
arity. `empty(mug) = false` is a Proposition with no argument edges;
`located(report, office) = true` adds a LOCATION; `requires(coffee, cup)`
adds an OBJECT. Nothing needs to know in advance which predicates are
locative, so a new predicate is new data rather than a new relation.

An Event's arguments are edges rather than properties, so an observed
action is traversable from either end: from the agent who performed it
through ACTOR_OF, and to the place it was directed through TO. OBJECT is
reused from the proposition arguments, since an event's object argument
means the same thing. Any argument without a relation of its own stays on
the node as text.

Perspective
-----------

A scenario states both what is true and what agents believe, and the
experiment turns on comparing them. Rather than a separate relation for
belief, every Proposition records who it is true *for*:

    perspective  "world" or "belief"
    holders      [] for the world; ["sam"] for Sam's belief; ["sam", "alex"]
                 for Sam's belief about Alex's belief

So a fact and a belief about that fact are the same structure differing
only in whose it is, a conflict is one query over propositions sharing a
claim, and second-order belief is a longer holder chain rather than a
different shape.

Two derived properties carry the keys that make this queryable:

    claim      predicate and arguments — *what* is asserted, regardless of
               who holds it. Two propositions conflict when they share a
               claim and disagree on value.
    signature  claim plus perspective and holders — the identity of the
               proposition, so MERGE is idempotent. Argument edges cannot
               participate in a MERGE key, which is why this is a property.

Known gap: nesting is flattened rather than reified. `sam believes alex
believes X` stores one Proposition for X with holders ["sam", "alex"], and
there is no (:Proposition)-[:CONTENT]->(:Proposition). That keeps conflict
a single comparison and makes attribution easy to query, but an attitude is
not itself a node and cannot carry properties of its own.
"""

from __future__ import annotations

import os
from collections.abc import Iterator, Sequence
from contextlib import contextmanager

from neo4j import Driver, GraphDatabase

from .models import MentalState, Proposition, Scenario

WORLD = "world"
BELIEF = "belief"


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


def claim_of(proposition: Proposition) -> str:
    """What a proposition asserts, ignoring its value and who holds it."""
    return "|".join(
        (
            proposition.predicate,
            proposition.subject,
            proposition.object or "",
            proposition.location or "",
        )
    )


#: The only attitude the flattened representation can express. See
#: notes/graph_ontology.md — collapsing a chain to a holders list keeps only
#: who holds the claim, so every level must be the same attitude.
ATTITUDE = "belief"
NESTING_PREDICATE = "believes"


def unfold(mental: MentalState) -> tuple[list[str], Proposition]:
    """Split a mental state into its chain of holders and its claim.

    `sam believes alex believes located(...)` unfolds to
    `(["sam", "alex"], located(...))`. The innermost proposition is the only
    one making a claim about the world; every level above it attributes an
    attitude, and becomes a holder.

    Raises on any attitude other than belief. Flattening discards the
    attitude type, so storing `knowledge` would make it indistinguishable
    from belief — and knowledge implies truth where belief does not. Better
    to refuse than to represent it wrongly in silence.
    """
    if mental.type != ATTITUDE:
        raise ValueError(
            f"{mental.agent} holds a {mental.type!r}; the flattened representation "
            f"can only express {ATTITUDE!r}. Reify the nesting to support more "
            f"(see notes/graph_ontology.md)."
        )

    holders = [mental.agent]
    proposition = mental.proposition
    while proposition.proposition is not None:
        if proposition.predicate != NESTING_PREDICATE:
            raise ValueError(
                f"nested proposition uses {proposition.predicate!r}; the flattened "
                f"representation keeps only the subject of each level and so can "
                f"only express {NESTING_PREDICATE!r}."
            )
        holders.append(proposition.subject)
        proposition = proposition.proposition
    return holders, proposition


def _entity(tx, scenario: str, entity_id: str, label: str, name: str | None = None) -> None:
    tx.run(
        f"""
        MERGE (e:Entity:{label} {{scenario: $scenario, id: $id}})
        SET e.name = coalesce($name, e.name, $id)
        """,
        scenario=scenario,
        id=entity_id,
        name=name,
    )


def _proposition(
    tx, scenario: str, proposition: Proposition, perspective: str, holders: Sequence[str]
) -> None:
    """Write one proposition as a node, with its subject and arguments."""
    holders = list(holders)
    claim = claim_of(proposition)
    signature = f"{claim}|{perspective}|{'>'.join(holders)}"

    tx.run(
        """
        MATCH (subject:Entity {scenario: $scenario, id: $subject})
        MERGE (p:Proposition {scenario: $scenario, signature: $signature})
        SET p.predicate = $predicate, p.value = $value, p.claim = $claim,
            p.perspective = $perspective, p.holders = $holders
        MERGE (subject)-[:SUBJECT_OF]->(p)
        """,
        scenario=scenario,
        subject=proposition.subject,
        signature=signature,
        predicate=proposition.predicate,
        value=proposition.value,
        claim=claim,
        perspective=perspective,
        holders=holders,
    )

    for relation, argument in (("LOCATION", proposition.location), ("OBJECT", proposition.object)):
        if argument is None:
            continue
        tx.run(
            f"""
            MATCH (p:Proposition {{scenario: $scenario, signature: $signature}})
            MATCH (target:Entity {{scenario: $scenario, id: $target}})
            MERGE (p)-[:{relation}]->(target)
            """,
            scenario=scenario,
            signature=signature,
            target=argument,
        )


def load(driver: Driver, scenario: Scenario) -> None:
    """Write a scenario's entities, world state, goals, events and beliefs.

    Idempotent: re-loading updates in place rather than duplicating.
    """
    with driver.session() as session:
        for label, group in (
            ("Agent", scenario.entities.agents),
            ("Location", scenario.entities.locations),
            ("Object", scenario.entities.objects),
        ):
            for entity in group:
                session.execute_write(_entity, scenario.id, entity.id, label, entity.name)

        for fact in scenario.world_state:
            session.execute_write(_proposition, scenario.id, fact, WORLD, [])

        for mental in scenario.mental_state:
            holders, held = unfold(mental)
            session.execute_write(_proposition, scenario.id, held, BELIEF, holders)

        for goal in scenario.goals:
            for target in goal.arguments().values():
                session.run(
                    """
                    MATCH (agent:Entity:Agent {scenario: $scenario, id: $agent})
                    MATCH (target:Entity {scenario: $scenario, id: $target})
                    MERGE (agent)-[:HAS_GOAL {type: $type}]->(target)
                    """,
                    scenario=scenario.id,
                    agent=goal.agent,
                    target=target,
                    type=goal.type,
                )

        for index, observation in enumerate(scenario.observations):
            arguments = observation.arguments()
            event_id = f"{observation.type}:{observation.agent}:{index}"
            session.execute_write(_entity, scenario.id, event_id, "Event", observation.type)
            edged = {"destination": "TO", "object": "OBJECT"}
            session.run(
                """
                MATCH (e:Entity:Event {scenario: $scenario, id: $id})
                MATCH (actor:Entity:Agent {scenario: $scenario, id: $actor})
                SET e.type = $type, e.arguments = $arguments
                MERGE (actor)-[:ACTOR_OF]->(e)
                """,
                scenario=scenario.id,
                id=event_id,
                actor=observation.agent,
                type=observation.type,
                # Arguments with a relation of their own become edges below;
                # anything else has nowhere to go but the node.
                arguments=[f"{k}={v}" for k, v in arguments.items() if k not in edged],
            )
            for argument, relation in edged.items():
                if (target := arguments.get(argument)) is None:
                    continue
                session.run(
                    f"""
                    MATCH (e:Entity:Event {{scenario: $scenario, id: $id}})
                    MATCH (target:Entity {{scenario: $scenario, id: $target}})
                    MERGE (e)-[:{relation}]->(target)
                    """,
                    scenario=scenario.id,
                    id=event_id,
                    target=target,
                )


def conflicts(driver: Driver, scenario_id: str) -> list[dict]:
    """Every first-order belief that contradicts the world state.

    Belief and world propositions share a `claim` when they assert the same
    thing of the same arguments, so a conflict is a pair sharing a claim and
    disagreeing on value.

    Only first-order beliefs count — `size(holders) = 1`. A belief about
    another agent's belief makes no claim about the world, since the nested
    belief may itself be wrong.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (subject:Entity {scenario: $scenario})-[:SUBJECT_OF]->(b:Proposition)
        WHERE b.perspective = $belief AND size(b.holders) = 1
        MATCH (subject)-[:SUBJECT_OF]->(w:Proposition)
        WHERE w.perspective = $world AND w.claim = b.claim AND w.value <> b.value
        OPTIONAL MATCH (b)-[:LOCATION]->(place:Entity)
        OPTIONAL MATCH (b)-[:OBJECT]->(object:Entity)
        RETURN b.holders[0] AS agent, b.predicate AS predicate,
               subject.id AS subject, place.id AS location, object.id AS object,
               b.value AS believed, w.value AS actual
        ORDER BY agent, predicate, subject
        """,
        scenario=scenario_id,
        world=WORLD,
        belief=BELIEF,
    )
    return [record.data() for record in records]


def has_conflict(driver: Driver, scenario_id: str) -> bool:
    """Does any first-order belief contradict the world state?"""
    return bool(conflicts(driver, scenario_id))


def attributions(driver: Driver, scenario_id: str) -> list[dict]:
    """Every second-order belief, against what the attributed agent holds.

    An attribution — `sam believes alex believes X` — can be wrong about
    Alex rather than about the world, but only where Alex's own belief is
    represented. Where it is not, `actual` comes back null and the
    attribution is simply uncheckable.

    Kept separate from `conflicts`: one asks whether a belief matches the
    world, the other whether it matches a person.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (subject:Entity {scenario: $scenario})-[:SUBJECT_OF]->(a:Proposition)
        WHERE a.perspective = $belief AND size(a.holders) = 2
        OPTIONAL MATCH (a)-[:LOCATION]->(attributed:Entity)
        OPTIONAL MATCH (subject)-[:SUBJECT_OF]->(own:Proposition)
            WHERE own.perspective = $belief
              AND own.holders = [a.holders[1]]
              AND own.predicate = a.predicate
              AND own.value = true
        OPTIONAL MATCH (own)-[:LOCATION]->(actual:Entity)
        RETURN a.holders[0] AS believer, a.holders[1] AS about,
               a.predicate AS predicate, subject.id AS subject,
               attributed.id AS attributed, actual.id AS actual
        ORDER BY believer, about, subject
        """,
        scenario=scenario_id,
        belief=BELIEF,
    )
    return [record.data() for record in records]


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
