"""Core data models.

Typed containers shared across the package so scenarios, representations,
and results all agree on shape. Kept free of logic on purpose.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class Entity(BaseModel):
    """A participant or object referenced by a scenario."""

    id: str
    name: str
    attributes: dict[str, str] = Field(default_factory=dict)


class Relation(BaseModel):
    """A directed relation between two entities."""

    source: str
    target: str
    kind: str
    attributes: dict[str, str] = Field(default_factory=dict)


class Scenario(BaseModel):
    """A single scenario: the narrative plus its structured content."""

    id: str
    text: str
    entities: list[Entity] = Field(default_factory=list)
    relations: list[Relation] = Field(default_factory=list)


class Prediction(BaseModel):
    """Jev's structured answers for one scenario under one representation.

    `answers` holds the raw per-question payloads as returned by the API —
    shape depends on the question type:

      noul   -> {"type": "noul", "noul": 0.74}
      choice -> {"type": "choice", "choice": "ana", "confidence": 0.6,
                 "probabilities": {...}}
      score  -> {"type": "score", "score": 1.99, "confidence": 0.99,
                 "legend": {...}, "probabilities": {...}}

    Nothing is discarded, so a run can be re-analysed without re-querying.
    """

    scenario_id: str
    condition: str
    model: str
    answers: dict[str, dict[str, Any]] = Field(default_factory=dict)
    usage: dict[str, int] = Field(default_factory=dict)
    request_id: str | None = None

    def flat(self) -> dict[str, Any]:
        """Flatten to one row of scalars, for tabular analysis.

        Each question contributes its primary value under its own key, plus
        `<key>_confidence` where the question type reports one. `noul`
        questions report no confidence, so they contribute a value only.
        """
        row: dict[str, Any] = {"scenario": self.scenario_id, "condition": self.condition}
        for key, answer in self.answers.items():
            kind = answer.get("type")
            row[key] = answer.get(kind) if kind else None
            if "confidence" in answer:
                row[f"{key}_confidence"] = answer["confidence"]
        return row
