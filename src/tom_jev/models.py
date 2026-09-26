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
    """An agent, location, or object referenced by a scenario.

    `article` and `preposition` exist only for the narrated `history`
    representation, which has to put a name into a sentence. Most names
    take "in the" — "in the office" — but "the front desk" wants "at" and
    "platform three" wants neither article nor "in". Recording that on the
    entity beats having the renderer guess from the name.
    """

    id: str
    name: str
    article: bool = True
    preposition: str = "in"

    def phrase(self, preposition: str | None = None) -> str:
        """The name in a prepositional phrase, e.g. `at the front desk`.

        Passing `preposition` overrides the entity's own, for verbs that
        fix it themselves — you leave a place, you do not leave in it.
        """
        head = self.preposition if preposition is None else preposition
        return " ".join(part for part in (head, "the" if self.article else "", self.name) if part)


class Entities(BaseModel):
    """The cast of a scenario, grouped by kind."""

    agents: list[Entity] = Field(default_factory=list)
    locations: list[Entity] = Field(default_factory=list)
    objects: list[Entity] = Field(default_factory=list)

    def by_id(self, entity_id: str) -> Entity | None:
        """The entity with this id, or None if the cast omits it."""
        for group in (self.agents, self.locations, self.objects):
            for entity in group:
                if entity.id == entity_id:
                    return entity
        return None

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

    A proposition may take another proposition as its content instead of a
    value, which is how second-order belief is written: the outer
    proposition attributes an attitude to an agent, the inner one says what
    that agent holds.

        predicate: believes
        subject: alex
        proposition:
          predicate: located
          subject: meeting
          location: office
          value: true

    Exactly one of `value` or `proposition` must be given.
    """

    predicate: str
    subject: str
    object: str | None = None
    location: str | None = None
    value: bool | float | str | None = None
    proposition: Proposition | None = None

    @model_validator(mode="after")
    def _value_or_nested(self) -> Proposition:
        if (self.value is None) == (self.proposition is None):
            raise ValueError(
                f"proposition {self.predicate}({self.subject}) needs exactly one of "
                "`value` or a nested `proposition`"
            )
        return self

    @property
    def depth(self) -> int:
        """1 for a plain proposition, 2 for one embedding another, and so on."""
        return 1 if self.proposition is None else 1 + self.proposition.depth

    def innermost(self) -> Proposition:
        """The proposition at the bottom of the nesting — the one with a value."""
        return self if self.proposition is None else self.proposition.innermost()

    def signature(self) -> tuple:
        """What this proposition is *about*, ignoring the value it takes.

        Two propositions share a signature when they make the same claim,
        so one can supersede the other. The innermost value is excluded
        for exactly that reason — `located(report, office) = True` and
        `= False` are the same claim, settled two ways.
        """
        inner = None if self.proposition is None else self.proposition.signature()
        return (self.predicate, self.subject, self.object, self.location, inner)

    def held_value(self) -> bool | float | str | None:
        """The value at the bottom of the nesting.

        A nested proposition carries no value of its own: what
        `believes(alex)[located(meeting, office) = True]` settles is the
        True at the bottom.
        """
        return self.innermost().value

    def revalued(self, value: bool | float | str) -> Proposition:
        """A copy whose innermost proposition takes a different value.

        The counterpart to `relocated` for claims with no location to
        vary — an availability is settled by flipping it, not by moving
        it somewhere else.
        """
        if self.proposition is None:
            return self.model_copy(update={"value": value})
        return self.model_copy(update={"proposition": self.proposition.revalued(value)})

    def relocated(self, location: str) -> Proposition:
        """A copy whose innermost proposition names a different location.

        Used for locative exclusivity, which passes through nesting:
        seeing Alex come to believe the meeting is in the office is seeing
        Alex come to believe it is not in the garden.
        """
        if self.proposition is None:
            return self.model_copy(update={"location": location})
        return self.model_copy(update={"proposition": self.proposition.relocated(location)})


def _mentions(proposition: Proposition) -> set[str]:
    """Every entity id a proposition names, following any nesting."""
    ids = {proposition.subject}
    for argument in (proposition.object, proposition.location):
        if argument is not None:
            ids.add(argument)
    if proposition.proposition is not None:
        ids |= _mentions(proposition.proposition)
    return ids


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


class HistoryEvent(BaseModel):
    """A claim being settled, and who was present to see it settled.

    An epistemic-access history says how an agent came to believe what
    they believe, instead of stating the belief. Each event settles a
    proposition and names its witnesses; an agent's belief about a claim
    is whatever the last event they witnessed settled, which may be stale
    if the world moved on without them.

    The proposition may be nested, because what an agent believes about
    another agent's belief is a claim like any other. Sam can witness Alex
    come to believe the meeting is in the office in the same way Sam can
    witness coffee being stocked in the kitchen — and can then miss Alex
    changing their mind, exactly as Sam can miss the coffee running out.
    That parity is the point: an attribution is not a different level of
    representation, just a proposition with more structure.

    The history is observable — it goes to the model in the `history`
    condition — while the belief it entails stays in `mental_state` and is
    withheld until `rich`. That separates needing the information from
    needing it made explicit.

    `event` is a human-readable gloss for whoever reads the YAML. It is
    not rendered; the renderers narrate the proposition themselves.
    """

    event: str = ""
    proposition: Proposition
    witnessed_by: list[str] = Field(default_factory=list)

    def claim(self) -> tuple:
        """What this event settles, ignoring its value and its witnesses."""
        return self.proposition.signature()

    @property
    def value(self) -> bool | float | str | None:
        """The value this event settles the claim at."""
        return self.proposition.held_value()


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


class Taxonomy(BaseModel):
    """Where a scenario sits in the corpus, read off its directory path.

    Not written in the scenario file: the path is the source of truth, so
    moving a file reclassifies it and a file cannot disagree with its own
    directory. See `scenarios.taxonomy`.
    """

    task_family: str | None = None
    template: str | None = None
    domain: str | None = None
    condition: str | None = None
    lexicalization: str | None = None


class Scenario(BaseModel):
    """One scenario, as stored under scenarios/."""

    id: str
    description: str | None = None
    scenario_set: str | None = None
    variant: Variant | None = None
    taxonomy: Taxonomy = Field(default_factory=Taxonomy)

    entities: Entities = Field(default_factory=Entities)
    observations: list[Observation] = Field(default_factory=list)
    history: list[HistoryEvent] = Field(default_factory=list)
    world_state: list[Proposition] = Field(default_factory=list)
    goals: list[Goal] = Field(default_factory=list)
    mental_state: list[MentalState] = Field(default_factory=list)

    question: Question
    ground_truth: GroundTruth
    annotations: Annotations = Field(default_factory=Annotations)

    def declared(self) -> set[str]:
        """Every entity id the scenario introduces."""
        return {
            e.id
            for group in (
                self.entities.agents,
                self.entities.locations,
                self.entities.objects,
            )
            for e in group
        }

    def referenced(self) -> set[str]:
        """Every entity id the scenario's content mentions."""
        ids: set[str] = set()
        for proposition in self.world_state:
            ids |= _mentions(proposition)
        for mental in self.mental_state:
            ids.add(mental.agent)
            ids |= _mentions(mental.proposition)
        for observation in self.observations:
            ids.add(observation.agent)
            ids |= {str(v) for v in observation.arguments().values()}
        for event in self.history:
            ids |= set(event.witnessed_by)
            ids |= _mentions(event.proposition)
        for goal in self.goals:
            ids.add(goal.agent)
            ids |= {str(v) for v in goal.arguments().values()}
        return ids

    @model_validator(mode="after")
    def _entities_must_be_declared(self) -> Scenario:
        """Everything mentioned must be in the cast.

        An undeclared entity is invisible to anything that builds a
        structure from the scenario rather than reading its propositions as
        tuples — a graph, say, which has no node to attach the fact to and
        silently drops it.
        """
        undeclared = self.referenced() - self.declared()
        if undeclared:
            raise ValueError(
                f"{self.id}: mentions {sorted(undeclared)}, which entities does not declare"
            )
        return self

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
