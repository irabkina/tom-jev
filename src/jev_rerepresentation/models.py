"""Core data models.

Typed containers shared across the package so scenarios, graphs, and
representations all agree on shape. Kept free of logic on purpose.
"""

from __future__ import annotations

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
    """A model's answer for one scenario, with whatever it was scored on."""

    scenario_id: str
    answer: str
    rationale: str | None = None
    scores: dict[str, float] = Field(default_factory=dict)
