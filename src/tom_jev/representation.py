"""Representations of a scenario, and re-representation between them.

A *representation* is one way of presenting a scenario to Jev. Jev takes a
`state` mapping rather than a prompt string, so a representation produces a
dict: the keys name the parts of the state, the values carry the content.

*Re-representation* transforms one representation into another while
preserving content — the manipulation under test in
`experiments/02_rerepresentation.py`.
"""

from __future__ import annotations

from collections.abc import Callable

from . import graph
from .models import Scenario

State = dict[str, str]


def sparse(scenario: Scenario) -> State:
    """Minimal presentation: relational structure only, no narrative."""
    return {"structure": graph.describe(graph.build(scenario))}


def rich(scenario: Scenario) -> State:
    """Full presentation: the scenario's narrative text."""
    return {"narrative": scenario.text}


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
