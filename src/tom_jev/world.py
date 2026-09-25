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
import pathlib
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from enum import StrEnum

import yaml
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


class Consistency(StrEnum):
    """Whether a predicted action squares with the objective world.

    Three-valued on purpose. `not_applicable` is not a quiet `consistent`:
    it says no rule applies, and collapsing the two would let "we cannot
    tell" be counted as "nothing is wrong".
    """

    CONFLICT = "conflict"  # the world says the action does not serve the goal
    CONSISTENT = "consistent"  # the world says it does
    NOT_APPLICABLE = "not_applicable"  # no defensible rule for this scenario


#: Action options are named `go_to_<location id>`. Brittle, and the only
#: place meaning is read out of an option string — an action named another
#: way falls through to NOT_APPLICABLE rather than being judged wrongly.
GO_TO = "go_to_"


#: Background knowledge is scenario-independent, so it is scoped by a name
#: no scenario can use. Everything else keys on a scenario id.
BACKGROUND = "_background"

#: Requirement kinds, from knowledge/goals.yaml.
PRESENT, CARRIED, CO_LOCATED = "present", "carried", "co_located"


def load_knowledge(driver: Driver, path: pathlib.Path) -> int:
    """Load background relational knowledge: what goals require.

    Standing facts about the domain, not about an episode — `get_coffee`
    needs a mug whatever is happening today. Kept out of `world_state` so
    the two can change for different reasons, and so the conflict rule is
    about goals having requirements rather than about any one predicate.

        (:Goal {name})-[:REQUIRES {kind}]->(:Concept {name})

    `kind` is present, carried or co_located. A co_located requirement
    names a role — `target_agent`, `object` — rather than an entity, since
    which entity fills it comes from the scenario's own goal.
    """
    document = yaml.safe_load(path.read_text())
    written = 0
    with driver.session() as session:
        for goal in document["goals"]:
            session.run(
                "MERGE (g:Goal {scenario: $scope, name: $name})",
                scope=BACKGROUND,
                name=goal["name"],
            )
            for requirement in goal.get("requires", []):
                ((kind, what),) = requirement.items()
                session.run(
                    """
                    MATCH (g:Goal {scenario: $scope, name: $name})
                    MERGE (c:Concept {scenario: $scope, name: $what})
                    MERGE (g)-[:REQUIRES {kind: $kind}]->(c)
                    """,
                    scope=BACKGROUND,
                    name=goal["name"],
                    what=str(what),
                    kind=kind,
                )
                written += 1
    return written


def _carrying(driver: Driver, scenario_id: str, agent: str) -> set[str]:
    """Everything the agent is observed to be carrying."""
    records, _, _ = driver.execute_query(
        """
        MATCH (a:Entity:Agent {scenario: $scenario, id: $agent})
              -[:ACTOR_OF]->(:Event)-[:OBJECT]->(thing)
        RETURN DISTINCT thing.id AS thing
        """,
        scenario=scenario_id,
        agent=agent,
    )
    return {r["thing"] for r in records}


def _at(driver: Driver, scenario_id: str, place: str) -> tuple[set[str], set[str]]:
    """What the episodic world puts at a place, and what it puts elsewhere.

    Returned separately because silence is neither: an entity the world
    never mentions is unknown, not absent.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (e:Entity {scenario: $scenario})-[:SUBJECT_OF]->(p:Proposition)
              -[:LOCATION]->(:Entity {scenario: $scenario, id: $place})
        WHERE p.perspective = $world
        RETURN e.id AS entity, p.value AS present
        """,
        scenario=scenario_id,
        place=place,
        world=WORLD,
    )
    here = {r["entity"] for r in records if r["present"]}
    away = {r["entity"] for r in records if r["present"] is False}
    return here, away


def satisfiable(
    driver: Driver, scenario: Scenario, goal: str, place: str, roles: dict[str, str]
) -> Consistency | None:
    """Can this goal be served by being at this place?

    CONSISTENT when every requirement holds, CONFLICT when the world
    explicitly denies one, None when the background knows no such goal or
    the world is silent about a requirement.

    `roles` fills co_located requirements — the entity a `meet` goal
    targets, the object an `obtain` goal seeks — since the requirement
    names the role and the scenario names the filler.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (:Goal {scenario: $scope, name: $goal})-[r:REQUIRES]->(c:Concept)
        RETURN r.kind AS kind, c.name AS what
        """,
        scope=BACKGROUND,
        goal=goal,
    )
    if not records:
        return None

    here, away = _at(driver, scenario.id, place)
    carrying = _carrying(driver, scenario.id, scenario.question.agent)
    unknown = False

    for record in records:
        kind, what = record["kind"], record["what"]
        if kind == CARRIED:
            if what not in carrying:
                return Consistency.CONFLICT
        elif kind in (PRESENT, CO_LOCATED):
            target = roles.get(what, what) if kind == CO_LOCATED else what
            if target in away:
                return Consistency.CONFLICT
            if target not in here:
                unknown = True
    return None if unknown else Consistency.CONSISTENT


def goals_in_play(scenario: Scenario) -> list[tuple[str, dict[str, str]]]:
    """Every goal the agent might be pursuing, with its role fillers.

    Given goals for action prediction, since the scenario states them; the
    candidate options for goal recognition, since there the goal is what is
    being inferred and any option is in play.
    """
    if scenario.goals:
        return [(g.type, {k: str(v) for k, v in g.arguments().items()}) for g in scenario.goals]
    return [(option, {}) for option in scenario.question.options]


def accounted_for(driver: Driver, scenario: Scenario, place: str) -> Consistency:
    """Does the world account for the agent being at this place?

    Background knowledge says what each goal in play requires; the episodic
    world says what is where. A place is accounted for when some goal is
    satisfiable there.

      CONSISTENT      some goal in play is satisfiable at the place
      CONFLICT        every goal in play is explicitly ruled out there
      NOT_APPLICABLE  the background knows none of these goals, or the
                      world is too silent to say

    Silence is not conflict, at either level: a goal whose requirement the
    world never mentions counts as unknown rather than denied, and a place
    with only unknowns is NOT_APPLICABLE rather than a conflict.
    """
    verdicts = [
        satisfiable(driver, scenario, goal, place, roles) for goal, roles in goals_in_play(scenario)
    ]
    known = [v for v in verdicts if v is not None]
    if not known:
        return Consistency.NOT_APPLICABLE
    if Consistency.CONSISTENT in known:
        return Consistency.CONSISTENT
    return Consistency.CONFLICT


def action_consistency(driver: Driver, scenario: Scenario, action: str) -> Consistency:
    """Is a predicted action unaccounted for by the world?

    `accounted_for` asked of the answer. Quiet on a sparse answer, which is
    derived from the world and so rarely contradicts it; it bites on a rich
    answer, which follows a belief that may.
    """
    if not action.startswith(GO_TO):
        return Consistency.NOT_APPLICABLE
    return accounted_for(driver, scenario, action[len(GO_TO) :])


def dependencies(driver: Driver, scenario: Scenario) -> list[dict]:
    """What a prediction rests on, and which supports resolve through a mind.

    The escalation question asked structurally rather than from the output.
    Three output-based signals fail on this corpus — confidence, conflict
    with the world, and the answer being ruled out — because they ask
    whether the sparse pass looks wrong, and it does not: it is reasoning
    correctly over what it was given. This asks instead what the conclusion
    *depends on*, and whether any of those supports is the kind of thing
    only a mind settles.

    Two kinds, and they behave very differently.

    `actor` — the acting agent's own representation of a requirement.
    Universal: whatever the world says about where the report is, the agent
    goes where they *believe* it is. Present in every prediction about an
    agent, so on its own it says escalate always.

    `<agent id>` — a requirement that resolves through *another* agent's
    representation. `meet(alex)` needs co-location with Alex, and where
    Alex is depends on what Alex believes. Selective: only goals whose
    requirements point at an agent.

    Returned one row per support, so a caller can count distinct minds,
    weight them, or ignore the universal one.
    """
    rows: list[dict] = []
    agents = {e.id for e in scenario.entities.agents}
    actor = scenario.question.agent

    for goal, roles in goals_in_play(scenario):
        records, _, _ = driver.execute_query(
            """
            MATCH (:Goal {scenario: $scope, name: $goal})-[r:REQUIRES]->(c:Concept)
            RETURN r.kind AS kind, c.name AS what
            """,
            scope=BACKGROUND,
            goal=goal,
        )
        for record in records:
            kind, what = record["kind"], record["what"]
            filler = roles.get(what, what) if kind == CO_LOCATED else what
            rows.append(
                {
                    "goal": goal,
                    "kind": kind,
                    "requires": filler,
                    # Whose representation settles this. The actor's
                    # always, since they act on what they take to be true;
                    # additionally another agent's when the requirement
                    # points at one, as `meet(alex)` does through Alex.
                    "through": sorted(
                        {actor} | ({filler} if filler in agents and filler != actor else set())
                    ),
                }
            )
    return rows


def mind_dependence(driver: Driver, scenario: Scenario) -> int:
    """How many distinct minds the prediction turns on. Always at least one.

    Depending on some agent's representation is constitutive of predicting
    an agent, so this never returns 0 for a scenario about one, and cannot
    by itself say whether re-representation is worth doing. It measures
    depth of nesting, not need:

    1 — the actor's own representation of objective facts
    2 — the actor's, plus another agent whose own mind settles a
        requirement, as `meet(alex)` does through Alex's

    An earlier version excluded the actor to obtain a signal that fired on
    some scenarios and not others. That was selectivity manufactured by
    deforming the concept, and it missed the largest effects in the corpus,
    all of them first-order. See notes/experimental_design.md, *Dependency
    structure does not give a usable escalation signal either*.

    Computable without any belief: it reads the goal's requirements from
    background knowledge and the cast from the scenario.
    """
    return len({m for row in dependencies(driver, scenario) for m in row["through"]})


def answer_anomaly(driver: Driver, scenario: Scenario, answer: str) -> Consistency:
    """Is the model's own answer contradicted by what is known?

    The trigger candidate. Take the answer the sparse pass actually gave and
    ask whether background knowledge and the episodic world rule it out.
    Nothing here needs a belief, so it is computable before deciding whether
    to re-represent — unlike `conflicts` and `attributions`, which need the
    very thing re-representing supplies.

    Stronger than asking whether *any* goal survives, which is the mistake
    `accounted_for` makes on its own: a place almost always supports some
    goal, so that question is nearly always answered yes and never fires.
    This asks about the specific conclusion drawn.

        action prediction   the answer names a destination; is any goal in
                            play satisfiable there?
        goal recognition    the answer names a goal; is it satisfiable at
                            the place the agent was observed going?

    CONFLICT is the signal to escalate. NOT_APPLICABLE where the background
    knows nothing of the answer, or the world is silent about what it needs
    — an unknown is not a contradiction.
    """
    if answer.startswith(GO_TO):
        return accounted_for(driver, scenario, answer[len(GO_TO) :])

    records, _, _ = driver.execute_query(
        """
        MATCH (:Entity:Agent {scenario: $scenario})-[:ACTOR_OF]->(:Event)-[:TO]->(place)
        RETURN DISTINCT place.id AS place
        """,
        scenario=scenario.id,
    )
    roles = dict(next(iter(goals_in_play(scenario)), ("", {}))[1])
    verdicts = [satisfiable(driver, scenario, answer, record["place"], roles) for record in records]
    known = [v for v in verdicts if v is not None]
    if not known:
        return Consistency.NOT_APPLICABLE
    if Consistency.CONSISTENT in known:
        return Consistency.CONSISTENT
    return Consistency.CONFLICT


def observation_anomaly(driver: Driver, scenario: Scenario) -> Consistency:
    """Is the observed action unaccounted for by the world?

    `accounted_for` asked of what was seen rather than of what was
    predicted, which makes it the only one of these computable *before*
    re-representing: observation and world are both in the sparse
    representation, and no belief or model answer is involved.

    The motivating example, in graph form. Sam is seen walking to the
    kitchen carrying a mug. Background knowledge says getting coffee needs
    a mug and some coffee; the episodic world says there is no coffee
    there. No goal in play is satisfiable, so the walk serves nothing the
    world accounts for — the moment an observer might start wondering what
    Sam believes.
    """
    records, _, _ = driver.execute_query(
        """
        MATCH (:Entity:Agent {scenario: $scenario})-[:ACTOR_OF]->(:Event)-[:TO]->(place)
        RETURN DISTINCT place.id AS place
        """,
        scenario=scenario.id,
    )
    verdicts = [accounted_for(driver, scenario, r["place"]) for r in records]
    if Consistency.CONFLICT in verdicts:
        return Consistency.CONFLICT
    if Consistency.CONSISTENT in verdicts:
        return Consistency.CONSISTENT
    return Consistency.NOT_APPLICABLE


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
