"""JEV: the core evaluation routine.

TODO: fill in the actual JEV formulation. This module owns the scoring
itself; `representation.py` owns what gets fed into it.
"""

from __future__ import annotations

from .models import Prediction, Scenario


def evaluate(scenario: Scenario, answer: str) -> Prediction:
    """Score a single answer against a scenario."""
    raise NotImplementedError("TODO: implement JEV scoring")


def evaluate_all(scenarios: list[Scenario], answers: dict[str, str]) -> list[Prediction]:
    """Score answers for many scenarios, keyed by scenario id."""
    return [evaluate(s, answers[s.id]) for s in scenarios if s.id in answers]
