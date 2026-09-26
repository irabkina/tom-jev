"""Representations of a scenario, and re-representation between them.

Jev takes a `state` mapping rather than a prompt string, so a representation
produces a dict: the keys name the parts of the state, the values carry the
content.

The two base representations differ in exactly one thing:

    sparse = observations + world_state + goals
    rich   = observations + world_state + goals + mental_state

Nothing else varies between them. `ground_truth` and `annotations` are
researcher metadata and are never included in either — that exclusion lives
here, so no caller can leak an answer into the model input by accident.
"""

from __future__ import annotations

from collections.abc import Callable

from .models import (
    Entities,
    Goal,
    HistoryEvent,
    MentalState,
    Observation,
    Proposition,
    Scenario,
)

State = dict[str, str]


def _arguments(args: dict[str, object], names: dict[str, str]) -> str:
    """Render an argument mapping, resolving entity ids to display names."""
    return ", ".join(f"{k}={names.get(str(v), v)}" for k, v in args.items())


def _describe_observation(obs: Observation, names: dict[str, str]) -> str:
    """Render one observation as `actor event (args)`."""
    actor = names.get(obs.agent, obs.agent)
    args = _arguments(obs.arguments(), names)
    return f"{actor} {obs.type}" + (f" ({args})" if args else "")


def _describe_proposition(prop: Proposition, names: dict[str, str]) -> str:
    """Render one proposition as `predicate(subject, ...) = value`.

    A proposition holding another renders its content in brackets rather
    than a value, so second-order belief reads as one nested expression:

        believes(Alex)[located(meeting, at office) = True]
    """
    parts = [names.get(prop.subject, prop.subject)]
    if prop.object is not None:
        parts.append(names.get(prop.object, prop.object))
    if prop.location is not None:
        parts.append(f"at {names.get(prop.location, prop.location)}")
    head = f"{prop.predicate}({', '.join(parts)})"
    if prop.proposition is not None:
        return f"{head}[{_describe_proposition(prop.proposition, names)}]"
    return f"{head} = {prop.value}"


def _describe_goal(goal: Goal, names: dict[str, str]) -> str:
    """Render one goal as `agent wants to type (args)`."""
    actor = names.get(goal.agent, goal.agent)
    args = _arguments(goal.arguments(), names)
    return f"{actor} wants to {goal.type}" + (f" ({args})" if args else "")


def _describe_mental_state(ms: MentalState, names: dict[str, str]) -> str:
    """Render one mental state as `agent <type>: proposition`."""
    holder = names.get(ms.agent, ms.agent)
    return f"{holder} {ms.type}: {_describe_proposition(ms.proposition, names)}"


def _nonempty(state: dict[str, str]) -> State:
    """Drop sections with no content.

    An empty string would otherwise be sent as a state key, telling the
    model a section exists while saying nothing about it.
    """
    return {k: v for k, v in state.items() if v}


def _observable(scenario: Scenario) -> State:
    """The part both representations share: observations, world, goals."""
    names = scenario.entities.names()
    return _nonempty(
        {
            "observations": "\n".join(
                _describe_observation(o, names) for o in scenario.observations
            ),
            "world_state": "\n".join(_describe_proposition(p, names) for p in scenario.world_state),
            "goals": "\n".join(_describe_goal(g, names) for g in scenario.goals),
        }
    )


def sparse(scenario: Scenario) -> State:
    """Observable events, objective world state, and stated goals.

    Mental states are withheld, so any belief an agent holds must be
    inferred — or not — from behaviour and circumstance alone.
    """
    return _observable(scenario)


def rich(scenario: Scenario) -> State:
    """Everything sparse has, plus agents' explicit mental states."""
    names = scenario.entities.names()
    state = _observable(scenario)
    mental = "\n".join(_describe_mental_state(m, names) for m in scenario.mental_state)
    if mental:
        state["mental_state"] = mental
    return state


#: Prefixed to every history, so a superseded early event does not read as
#: a contradiction of the current world_state. Fixed text, identical for
#: every scenario, so it cannot favour one of them.
HISTORY_PREAMBLE = (
    "Earlier events, in the order they happened. A later event supersedes an "
    "earlier one about the same claim; world_state is the situation now."
)

#: How to narrate an event settling a flat claim, by predicate, the value
#: it settles, and whether the subject is an agent. Agents arrive and
#: leave; objects are put somewhere and taken away. `None` means the
#: location supplies the preposition, since that depends on the place
#: rather than the verb.
VERBS: dict[tuple[str, bool, bool], tuple[str, str | None]] = {
    ("located", True, True): ("arrives", "at"),
    ("located", True, False): ("is put", None),
    ("located", False, True): ("leaves", ""),
    ("located", False, False): ("is taken", "from"),
    ("available", True, False): ("is stocked", "in"),
    ("available", False, False): ("runs out", "in"),
}

#: How to narrate an agent coming to hold a belief. The attitude is an
#: event like any other — something that happens, that someone may or may
#: not be there for.
ATTITUDE_VERBS = {"believes": "comes to think"}


def _place(entities: Entities, location: str, preposition: str | None) -> str:
    """`at the front desk`, `on platform three` — the place decides."""
    entity = entities.by_id(location)
    return entity.phrase(preposition) if entity else f"in {location}"


def _subject(entities: Entities, entity_id: str) -> str:
    """A subject as it appears in a sentence: `Alex`, but `the meeting`.

    An agent is a name and takes no article; anything else does, unless
    its own `article` says otherwise.
    """
    entity = entities.by_id(entity_id)
    if entity is None:
        return entity_id
    if entity in entities.agents or not entity.article:
        return entity.name
    return f"the {entity.name}"


def _state_clause(proposition: Proposition, entities: Entities) -> str:
    """A claim as a statement of fact: `the meeting is in the office`.

    Used inside a belief, where the content is a state of affairs rather
    than something happening.
    """
    subject = _subject(entities, proposition.subject)
    negation = "" if proposition.value else " not"
    if proposition.location is None:
        return f"{subject} is{negation} available"
    where = _place(entities, proposition.location, None)
    if proposition.predicate == "available":
        return f"{subject} is{negation} available {where}"
    return f"{subject} is{negation} {where}"


def _narrate_event(event: HistoryEvent, index: int, entities: Entities, agents: set[str]) -> str:
    """Render one history event as `n. what happened (who saw it)`."""
    names = entities.names()
    claim = event.proposition
    subject = _subject(entities, claim.subject)

    if claim.proposition is not None:
        # A nested claim: an agent coming to hold a belief. Narrated as an
        # event, because that is what it is — Sam can witness it, or miss
        # it, exactly as with the coffee running out.
        verb = ATTITUDE_VERBS.get(claim.predicate, f"comes to {claim.predicate}")
        what = f"{subject} {verb} that {_state_clause(claim.innermost(), entities)}"
    else:
        verb, preposition = VERBS.get(
            (claim.predicate, bool(claim.value), claim.subject in agents), ("changes", "in")
        )
        where = f" {_place(entities, claim.location, preposition)}" if claim.location else ""
        what = f"{subject} {verb}{where}"

    seen = (
        ", ".join(names.get(w, w) for w in event.witnessed_by) if event.witnessed_by else "nobody"
    )
    return f"{index}. {what} (seen by {seen})"


def _describe_event(event: HistoryEvent, index: int, names: dict[str, str]) -> str:
    """Render one history event in the symbolic form world_state uses.

    The alternative to narrating it, and measurably a weaker one: a claim
    asserted True and then False reads as two contradictory facts, where
    the narration reads as an event someone was or was not there for. On
    the first-order set this costs most of the effect, and all of the cost
    falls in the false-belief cells (bakery_false_positive 0.51 -> 0.01
    acceptable mass); the true-belief cells do not move.

    Kept because it is the only rendering that matches the rest of the
    state, including the `mental_state` that `rich` adds — so it bounds
    how much of the `history` -> `rich` gap is style rather than
    explicitness. See notes/experimental_design.md.
    """
    claim = _describe_proposition(event.proposition, names)
    seen = (
        ", ".join(names.get(w, w) for w in event.witnessed_by) if event.witnessed_by else "nobody"
    )
    return f"{index}. {claim} [witnessed by {seen}]"


def history(scenario: Scenario) -> State:
    """Everything sparse has, plus how the agents came to know what they know.

    Events are listed in the order they happened, so a later one
    supersedes an earlier one about the same claim — for whoever was there
    to see it.

    The middle condition. It carries the evidence from which a belief
    follows — who was present when the world changed — without stating the
    belief. Comparing it against `rich` separates needing the information
    from needing it made explicit; comparing it against `sparse` says
    whether the evidence alone suffices.
    """
    agents = {e.id for e in scenario.entities.agents}
    state = _observable(scenario)
    events = [
        _narrate_event(e, i, scenario.entities, agents)
        for i, e in enumerate(scenario.history, start=1)
    ]
    if events:
        state["history"] = "\n".join(events)
    return state


def history_symbolic(scenario: Scenario) -> State:
    """`history`, written in the symbolic form the rest of the state uses.

    A robustness check, not the primary condition. It removes the style
    difference between `history` and `rich` at the cost of weakening what
    the history affords — see `_describe_event`. Because it is the weaker
    of the two, the gap it leaves to `rich` is an upper bound on what
    stating a belief buys over merely entailing it.
    """
    names = scenario.entities.names()
    state = _observable(scenario)
    events = [_describe_event(e, i, names) for i, e in enumerate(scenario.history, start=1)]
    if events:
        state["history"] = "\n".join([HISTORY_PREAMBLE, *events])
    return state


RENDERERS: dict[str, Callable[[Scenario], State]] = {
    "sparse": sparse,
    "history": history,
    "history_symbolic": history_symbolic,
    "rich": rich,
}


def render(scenario: Scenario, name: str) -> State:
    """Render `scenario` under the named representation."""
    try:
        return RENDERERS[name](scenario)
    except KeyError:
        raise ValueError(f"unknown representation {name!r}; have {sorted(RENDERERS)}") from None


def rerepresent(scenario: Scenario, source: str, target: str) -> State:
    """Convert a scenario from one representation into another.

    TODO: implement the transformation under study. `source` and `target`
    name representations in RENDERERS. The result is a state dict, same as
    the renderers produce, so it can be passed straight to `jev.evaluate`.
    """
    raise NotImplementedError("TODO: implement re-representation")
