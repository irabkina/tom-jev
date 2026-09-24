"""Querying Jev, TypeSafe's System One model.

Jev is a hosted model, not a local package: `typesafe-sdk` is the client.
It takes a `state` plus a mapping of typed `questions` (Noul / Choice /
Score) and returns structured answers with probabilities — there is no
prompt string and no text to parse.

The client reads TYPESAFE_API_KEY from the environment and defaults to the
`jev-latest` model; both are overridable via the TYPESAFE_* variables
documented in .env.example.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from typing import Any

from typesafe_sdk import Choice, TypeSafeClient

from . import representation
from .models import Prediction, Scenario
from .representation import State

Questions = Mapping[str, Any]

INSTRUCTIONS = {
    # Goal recognition: the action is observed, the goal is inferred.
    "goal": "Given the situation, what is {agent} trying to do?",
    # Action prediction: the goal is given, the action is inferred.
    "action_prediction": "Given the situation, what will {agent} do?",
}


@contextmanager
def client() -> Iterator[TypeSafeClient]:
    """Open a Jev client. Reads TYPESAFE_API_KEY from the environment."""
    with TypeSafeClient() as c:
        yield c


def question_for(scenario: Scenario) -> Questions:
    """Build the typed question a scenario poses.

    The scenario's own `question` block supplies the candidate options, so
    the task is fixed by the stimulus rather than by the experiment script.
    A Choice returns a probability distribution over the options, not just
    the winner.
    """
    q = scenario.question
    try:
        instructions = INSTRUCTIONS[q.type]
    except KeyError:
        raise ValueError(
            f"{scenario.id}: unsupported question type {q.type!r}; have {sorted(INSTRUCTIONS)}"
        ) from None

    return {
        q.type: Choice(
            instructions=instructions.format(agent=q.agent),
            criteria=dict.fromkeys(q.options),
        )
    }


def evaluate(
    c: TypeSafeClient,
    state: State,
    questions: Questions,
    *,
    scenario_id: str,
    condition: str,
) -> Prediction:
    """Put one state to Jev and capture its answers.

    All questions are evaluated against the state in a single call.
    """
    response = c.system_one(state=state, questions=questions)
    return Prediction(
        scenario_id=scenario_id,
        condition=condition,
        model=response.model,
        answers={key: answer.model_dump(mode="json") for key, answer in response.answers.items()},
        usage=response.usage.model_dump() if response.usage else {},
        request_id=response.request_id,
    )


def ask(c: TypeSafeClient, scenario: Scenario, condition: str) -> Prediction:
    """Render a scenario under one representation, ask Jev, and score it.

    Scoring compares Jev's choice against `ground_truth.answer`, which is
    held back from the state the model sees.
    """
    prediction = evaluate(
        c,
        representation.render(scenario, condition),
        question_for(scenario),
        scenario_id=scenario.id,
        condition=condition,
    )
    return score(prediction, scenario)


def score(prediction: Prediction, scenario: Scenario) -> Prediction:
    """Record the ground-truth answer and whether Jev's choice matched it."""
    answer = prediction.answers.get(scenario.question.type, {})
    chosen = answer.get("choice")
    prediction.variant = scenario.variant.type if scenario.variant else None
    prediction.ground_truth = scenario.ground_truth.answer
    prediction.correct = None if chosen is None else chosen == scenario.ground_truth.answer
    return prediction
