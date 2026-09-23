"""Representations of a scenario, and re-representation between them.

A *representation* is one way of presenting a scenario to a model.
*Re-representation* transforms one into another while preserving content —
the manipulation under test in `experiments/02_rerepresentation.py`.
"""

from __future__ import annotations

from . import graph
from .models import Scenario


def sparse(scenario: Scenario) -> str:
    """Minimal presentation: structure only, no narrative detail."""
    return graph.describe(graph.build(scenario))


def rich(scenario: Scenario) -> str:
    """Full presentation: the scenario's narrative text."""
    return scenario.text


def rerepresent(scenario: Scenario, source: str, target: str) -> str:
    """Convert a scenario from one representation into another.

    TODO: implement the transformation under study. `source` and `target`
    name representations ("sparse", "rich", ...).
    """
    raise NotImplementedError("TODO: implement re-representation")
