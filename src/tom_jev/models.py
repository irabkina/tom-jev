"""Core data models, mirroring scenarios/schema.yaml.

A scenario keeps observable fact, agent goals, and agents' mental states
apart so they can be fed to Jev independently — that split is the
experimental manipulation. `ground_truth` and `annotations` are researcher
metadata and must never reach the model; `representation.py` enforces that.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Entity(BaseModel):
    """An agent, location, or object referenced by a scenario."""

    id: str
    name: str


class Entities(BaseModel):
    """The cast of a scenario, grouped by kind."""

    agents: list[Entity] = Field(default_factory=list)
    locations: list[Entity] = Field(default_factory=list)
    objects: list[Entity] = Field(default_factory=list)

    def names(self) -> dict[str, str]:
        """Map every entity id to its display name."""
        return {
            e.id: e.name for group in (self.agents, self.locations, self.objects) for e in group
        }


class Variant(BaseModel):
    """Experimental condition within a matched scenario set.

    Pilot values: true_positive, false_positive, false_negative,
    true_negative — the 2x2 of whether the world supports the action and
    whether the agent believes it does.
    """

    type: str


class Observation(BaseModel):
    """An observable event that occurred before the target action.

    `type` names the event; which further arguments apply depends on it.
    Extra fields are allowed on purpose — event arguments are deliberately
    flexible during the pilot.
    """

    model_config = ConfigDict(extra="allow")

    type: str
    agent: str
    destination: str | None = None
    object: str | None = None
    target_agent: str | None = None

    def arguments(self) -> dict[str, Any]:
        """Every argument that is actually set, excluding `type` and `agent`."""
        named = {
            "destination": self.destination,
            "object": self.object,
            "target_agent": self.target_agent,
        }
        extra = self.model_extra or {}
        return {k: v for k, v in {**named, **extra}.items() if v is not None}


class Proposition(BaseModel):
    """A predicate applied to a subject, with optional relational arguments.

    Used both for objective world-state facts and for the content of a
    mental state — the same shape, differing only in whether it is asserted
    as true of the world or merely held by an agent.
    """

    predicate: str
    subject: str
    object: str | None = None
    location: str | None = None
    value: bool | float | str


class Goal(BaseModel):
    """A goal attributed to an agent.

    Goals are given as input rather than inferred, so that representation
    richness varies while the reasoning task stays fixed. They appear in
    both sparse and rich representations.
    """

    agent: str
    type: str
    object: str | None = None
    location: str | None = None
    target_agent: str | None = None

    def arguments(self) -> dict[str, Any]:
        """Every target argument that is actually set."""
        named = {
            "object": self.object,
            "location": self.location,
            "target_agent": self.target_agent,
        }
        return {k: v for k, v in named.items() if v is not None}


class MentalState(BaseModel):
    """A mental state held by an agent — `belief` for the pilot.

    Its proposition may conflict with objective world_state; that
    divergence is a primary experimental manipulation.
    """

    type: str
    agent: str
    proposition: Proposition


class Question(BaseModel):
    """The decision Jev is asked to make."""

    type: str = "action_prediction"
    agent: str
    options: list[str]


class GroundTruth(BaseModel):
    """The correct answer, for evaluation. Never sent to the model.

    `answer` is the single best reading. `acceptable` widens that to every
    option that should count as correct, for scenarios that are ambiguous
    by design — where the stimulus genuinely underdetermines the goal and a
    spread distribution is the right response rather than a failure.

    Omit `acceptable` and it defaults to just `answer`, which is the
    unambiguous case.
    """

    answer: str
    acceptable: list[str] = Field(default_factory=list)
    explanation: str | None = None

    def answers(self) -> list[str]:
        """Every option that counts as correct."""
        return self.acceptable or [self.answer]


class Annotations(BaseModel):
    """Researcher metadata about what a scenario tests. Never model input."""

    world_supports_action: bool | None = None
    agent_believes_action_supported: bool | None = None
    belief_matches_reality: bool | None = None
    belief_changes_expected_action: bool | None = None
    tags: list[str] = Field(default_factory=list)


class Scenario(BaseModel):
    """One scenario, as stored under scenarios/."""

    id: str
    description: str | None = None
    scenario_set: str | None = None
    variant: Variant | None = None

    entities: Entities = Field(default_factory=Entities)
    observations: list[Observation] = Field(default_factory=list)
    world_state: list[Proposition] = Field(default_factory=list)
    goals: list[Goal] = Field(default_factory=list)
    mental_state: list[MentalState] = Field(default_factory=list)

    question: Question
    ground_truth: GroundTruth
    annotations: Annotations = Field(default_factory=Annotations)

    @model_validator(mode="after")
    def _answers_must_be_options(self) -> Scenario:
        unknown = [a for a in self.ground_truth.answers() if a not in self.question.options]
        if unknown:
            raise ValueError(
                f"{self.id}: ground truth {unknown} "
                f"not among question.options {self.question.options}"
            )
        if self.ground_truth.acceptable and self.ground_truth.answer not in (
            self.ground_truth.acceptable
        ):
            raise ValueError(
                f"{self.id}: ground_truth.answer {self.ground_truth.answer!r} "
                f"is not among its own acceptable set {self.ground_truth.acceptable}"
            )
        return self


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

    variant: str | None = None
    ground_truth: str | None = None
    correct: bool | None = None

    def flat(self) -> dict[str, Any]:
        """Flatten to one row of scalars, for tabular analysis.

        Each question contributes its primary value under its own key, plus
        `<key>_confidence` where the question type reports one. `noul`
        questions report no confidence, so they contribute a value only.
        """
        row: dict[str, Any] = {"scenario": self.scenario_id, "condition": self.condition}
        if self.variant:
            row["variant"] = self.variant
        for key, answer in self.answers.items():
            kind = answer.get("type")
            row[key] = answer.get(kind) if kind else None
            if "confidence" in answer:
                row[f"{key}_confidence"] = answer["confidence"]
        if self.correct is not None:
            row["correct"] = self.correct
        return row
