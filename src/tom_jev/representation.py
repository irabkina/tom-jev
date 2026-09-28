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
        return f"{subject} is{negation} {proposition.predicate}"
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

    This was once thought to be the weaker rendering — a claim asserted
    True and then False reading as two contradictory facts, where the
    narration reads as an event someone was or was not there for. Measured
    against a fully prose arm, that is wrong: register is worth +0.03
    acceptable mass at the history level and nothing at all at sparse, and
    prose *costs* 0.08 at rich, entirely in nested beliefs. The earlier
    difference came from comparing two renderings that both sat inside an
    otherwise symbolic state.

    So this is the rendering that matches the rest of the state and gives
    up nothing measurable for it. See *Surface form: prose does not help,
    and hurts nested attitudes* in notes/experimental_design.md.
    """
    claim = _describe_proposition(event.proposition, names)
    seen = (
        ", ".join(names.get(w, w) for w in event.witnessed_by) if event.witnessed_by else "nobody"
    )
    return f"{index}. {claim} [witnessed by {seen}]"


#: How to narrate an observed event, by type: the verb, and the field
#: holding what it acts on. The corpus uses two; anything else falls back
#: to the type itself, which reads badly but never silently drops content.
OBSERVATION_VERBS: dict[str, tuple[str, str]] = {
    "walks_to": ("walks toward", "destination"),
    "carries": ("is carrying", "object"),
}

#: How to narrate a goal, by type. Same shape, same fallback.
GOAL_VERBS: dict[str, tuple[str, str]] = {
    "meet": ("meet", "target_agent"),
    "obtain": ("get", "object"),
}

#: How an attitude reads when its holder is the sentence subject.
ATTITUDE_CLAUSES = {"belief": "believes", "believes": "believes"}


def _capitalise(text: str) -> str:
    """Upper-case the first character only; `the report` has no name in it."""
    return text[:1].upper() + text[1:]


def _sentence(text: str) -> str:
    """A clause as a sentence."""
    return _capitalise(text) + "."


def _narrate_observation(obs: Observation, entities: Entities) -> str:
    """`Sam walks toward the kitchen.`"""
    actor = _subject(entities, obs.agent)
    verb, field = OBSERVATION_VERBS.get(obs.type, (obs.type.replace("_", " "), ""))
    target = obs.arguments().get(field) if field else None
    if target is None:
        return _sentence(f"{actor} {verb}")
    return _sentence(f"{actor} {verb} {_subject(entities, str(target))}")


def _narrate_goal(goal: Goal, entities: Entities) -> str:
    """`Sam wants to get the report.`"""
    actor = _subject(entities, goal.agent)
    verb, field = GOAL_VERBS.get(goal.type, (goal.type.replace("_", " "), ""))
    target = goal.arguments().get(field) if field else None
    if target is None:
        return _sentence(f"{actor} wants to {verb}")
    return _sentence(f"{actor} wants to {verb} {_subject(entities, str(target))}")


def _belief_clause(proposition: Proposition, entities: Entities) -> str:
    """The content of an attitude, at any depth.

    A nested claim reads as another attitude rather than as a state:
    `Alex believes that the meeting is in the office`.
    """
    if proposition.proposition is None:
        return _state_clause(proposition, entities)
    holder = _subject(entities, proposition.subject)
    verb = ATTITUDE_CLAUSES.get(proposition.predicate, proposition.predicate)
    return f"{holder} {verb} that {_belief_clause(proposition.proposition, entities)}"


def _narrate_mental_state(ms: MentalState, entities: Entities) -> str:
    """`Sam believes that Alex believes that the meeting is in the office.`"""
    holder = _subject(entities, ms.agent)
    verb = ATTITUDE_CLAUSES.get(ms.type, ms.type)
    return _sentence(f"{holder} {verb} that {_belief_clause(ms.proposition, entities)}")


def _observable_prose(scenario: Scenario) -> State:
    """What `_observable` renders, written as sentences.

    Same content, same section keys, same order — only the wording
    differs, so a prose condition can be set against its symbolic twin
    with nothing else varying.
    """
    entities = scenario.entities
    return _nonempty(
        {
            "observations": "\n".join(
                _narrate_observation(o, entities) for o in scenario.observations
            ),
            "world_state": "\n".join(
                _sentence(_state_clause(p, entities)) for p in scenario.world_state
            ),
            "goals": "\n".join(_narrate_goal(g, entities) for g in scenario.goals),
        }
    )


#: `VERBS`, in the past tense. A history is a sequence of things that
#: already happened, and in prose the tense is what says so — it is the
#: closest thing the narration has to the supersession rule that
#: HISTORY_PREAMBLE has to state outright for the symbolic form.
PAST_VERBS: dict[tuple[str, bool, bool], tuple[str, str | None]] = {
    ("located", True, True): ("arrived", "at"),
    ("located", True, False): ("was put", None),
    ("located", False, True): ("left", ""),
    ("located", False, False): ("was taken", "from"),
    ("available", True, False): ("was stocked", "in"),
    ("available", False, False): ("ran out", "in"),
}

#: `ATTITUDE_VERBS`, in the past tense.
PAST_ATTITUDE_VERBS = {"believes": "came to think"}


def _witnesses(event: HistoryEvent, names: dict[str, str]) -> str:
    """`and Sam saw it`, `and nobody saw it` — who the event reached."""
    seen = [names.get(w, w) for w in event.witnessed_by]
    if not seen:
        return "and nobody saw it"
    if len(seen) == 1:
        return f"and {seen[0]} saw it"
    return f"and {', '.join(seen[:-1])} and {seen[-1]} saw it"


def _narrate_event_prose(event: HistoryEvent, first: bool, entities: Entities) -> str:
    """One event as a sentence, in the register the rest of the state uses.

    The same content `_narrate_event` renders, without the list
    scaffolding: no number, no parenthetical witness tag, past tense, and
    a full stop. `Then` marks every event after the first, so the sequence
    is carried by the prose rather than by the numbering.

    The claim held inside an attitude stays in the present tense — it is
    what the agent thinks now, not something that happened.
    """
    names = entities.names()
    claim = event.proposition
    subject = _subject(entities, claim.subject)

    if claim.proposition is not None:
        verb = PAST_ATTITUDE_VERBS.get(claim.predicate, f"came to {claim.predicate}")
        what = f"{subject} {verb} that {_state_clause(claim.innermost(), entities)}"
    else:
        agents = {e.id for e in entities.agents}
        verb, preposition = PAST_VERBS.get(
            (claim.predicate, bool(claim.value), claim.subject in agents), ("changed", "in")
        )
        where = f" {_place(entities, claim.location, preposition)}" if claim.location else ""
        what = f"{subject} {verb}{where}"

    opening = "" if first else "then "
    return _sentence(f"{opening}{what}, {_witnesses(event, names)}")


def sparse_prose(scenario: Scenario) -> State:
    """`sparse`, written in prose."""
    return _observable_prose(scenario)


def rich_prose(scenario: Scenario) -> State:
    """`rich`, written in prose — including the belief itself.

    The condition the surface-form question turns on. If prose lifts this
    as much as it lifts `history_mixed`, the effect is about wording generally;
    if it does not, the narration is doing something specific to events.
    """
    state = _observable_prose(scenario)
    mental = "\n".join(_narrate_mental_state(m, scenario.entities) for m in scenario.mental_state)
    if mental:
        state["mental_state"] = mental
    return state


#: The three ways a history's events can be written. Each takes a scenario
#: and returns the event lines, so the rendering is a parameter rather than
#: a copy of the renderer.
EVENT_FORMS: dict[str, Callable[[Scenario], list[str]]] = {}


def _symbolic_events(scenario: Scenario) -> list[str]:
    """`1. available(coffee, at kitchen) = True [witnessed by Sam]`."""
    names = scenario.entities.names()
    return [_describe_event(e, i, names) for i, e in enumerate(scenario.history, start=1)]


def _listed_events(scenario: Scenario) -> list[str]:
    """`1. the coffee is stocked in the kitchen (seen by Sam)`."""
    agents = {e.id for e in scenario.entities.agents}
    return [
        _narrate_event(e, i, scenario.entities, agents)
        for i, e in enumerate(scenario.history, start=1)
    ]


def _narrated_events(scenario: Scenario) -> list[str]:
    """`The coffee was stocked in the kitchen, and Sam saw it.`"""
    return [
        _narrate_event_prose(e, i == 0, scenario.entities) for i, e in enumerate(scenario.history)
    ]


EVENT_FORMS.update(
    symbolic=_symbolic_events,
    listed=_listed_events,
    narrated=_narrated_events,
)


def _history_state(scenario: Scenario, *, events: str, prose: bool, preamble: bool) -> State:
    """A history condition, as the three factors that distinguish one.

    `events` names an entry in EVENT_FORMS, `prose` says whether the
    surrounding sections are narrated, and `preamble` whether
    HISTORY_PREAMBLE is prefixed. Every history condition is a point in
    that space, so two of them can be compared knowing exactly what
    differs — which the earlier hand-written renderers made easy to get
    wrong. See notes/experimental_design.md, *Where the mixed rendering's
    advantage comes from*.
    """
    state = _observable_prose(scenario) if prose else _observable(scenario)
    lines = EVENT_FORMS[events](scenario)
    if lines:
        state["history"] = "\n".join([HISTORY_PREAMBLE, *lines] if preamble else lines)
    return state


def history_mixed(scenario: Scenario) -> State:
    """Everything sparse has, plus how the agents came to know what they know.

    Events are listed in the order they happened, so a later one
    supersedes an earlier one about the same claim — for whoever was there
    to see it.

    The middle condition as originally built, and mixed in register: the
    events are narrated while everything around them is symbolic. That was
    not a design choice, and it is worth about 0.06 of acceptable mass in
    contrast against its surroundings alone. Kept because the 68-scenario
    results were produced with it; prefer `history` for anything
    new.
    """
    return _history_state(scenario, events="listed", prose=False, preamble=False)


def history(scenario: Scenario) -> State:
    """The middle condition, in the notation the rest of the state uses.

    With `sparse` and `rich` this is the internally consistent symbolic
    arm: one notation throughout, no preamble, and nothing about the
    history's formatting that sets it apart from its surroundings. That
    makes it the defensible middle condition, and the one that gives the
    smaller and more honest estimate of what evidence for a belief affords.
    """
    return _history_state(scenario, events="symbolic", prose=False, preamble=False)


def history_narrated(scenario: Scenario) -> State:
    """Narrated sentences inside a state that is symbolic everywhere else.

    Differs from `history_mixed` in the event wording alone, and from
    `history_prose` in the surroundings alone, so it is the pivot for both
    of those factors.
    """
    return _history_state(scenario, events="narrated", prose=False, preamble=False)


def history_prose(scenario: Scenario) -> State:
    """The middle condition with every section of the state in prose.

    The internally consistent narrative arm, with `sparse_prose` and
    `rich_prose`. Measured against the symbolic arm, prose is worth +0.03
    here and *costs* 0.08 at the rich level, all of it in nested beliefs —
    so this arm is the weaker of the two and kept for the comparison
    rather than for use.
    """
    return _history_state(scenario, events="narrated", prose=True, preamble=False)


#: The preamble-bearing variants. HISTORY_PREAMBLE was measured harmful —
#: -0.08 acceptable mass where the events are narrated, and nothing at all
#: where they are symbolic — so no condition above carries it. These exist
#: only so the experiments that established that stay reproducible, and
#: should not be used for anything new.
def history_mixed_preamble(scenario: Scenario) -> State:
    """`history_mixed` plus the preamble: isolates the preamble, nothing else."""
    return _history_state(scenario, events="listed", prose=False, preamble=True)


def history_narrated_preamble(scenario: Scenario) -> State:
    """`history_narrated` plus the preamble."""
    return _history_state(scenario, events="narrated", prose=False, preamble=True)


def history_prose_preamble(scenario: Scenario) -> State:
    """`history_prose` plus the preamble."""
    return _history_state(scenario, events="narrated", prose=True, preamble=True)


def history_preamble(scenario: Scenario) -> State:
    """`history` plus the preamble."""
    return _history_state(scenario, events="symbolic", prose=False, preamble=True)


RENDERERS: dict[str, Callable[[Scenario], State]] = {
    # The three conditions. One notation throughout, no preamble; they
    # differ in what they say about the agent's mind and in nothing else.
    "sparse": sparse,
    "history": history,
    "rich": rich,
    # The narrative arm, for the surface-form comparison. Weaker at the
    # rich level, where prose costs 0.08 on nested beliefs.
    "sparse_prose": sparse_prose,
    "history_prose": history_prose,
    "rich_prose": rich_prose,
    # Renderings kept so the experiments that established the above stay
    # reproducible. `history_mixed` is what `history` was until the
    # formatting was measured; the rest vary one factor each.
    "history_mixed": history_mixed,
    "history_narrated": history_narrated,
    "history_preamble": history_preamble,
    "history_mixed_preamble": history_mixed_preamble,
    "history_narrated_preamble": history_narrated_preamble,
    "history_prose_preamble": history_prose_preamble,
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
