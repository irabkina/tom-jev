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

from .models import Goal, MentalState, Observation, Proposition, Scenario

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
    """Render one proposition as `predicate(subject, ...) = value`."""
    parts = [names.get(prop.subject, prop.subject)]
    if prop.object is not None:
        parts.append(names.get(prop.object, prop.object))
    if prop.location is not None:
        parts.append(f"at {names.get(prop.location, prop.location)}")
    return f"{prop.predicate}({', '.join(parts)}) = {prop.value}"


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


RENDERERS: dict[str, Callable[[Scenario], State]] = {
    "sparse": sparse,
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
