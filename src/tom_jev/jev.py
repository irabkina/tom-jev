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

from typesafe_sdk import TypeSafeClient

from .models import Prediction
from .representation import State

Questions = Mapping[str, Any]


@contextmanager
def client() -> Iterator[TypeSafeClient]:
    """Open a Jev client. Reads TYPESAFE_API_KEY from the environment."""
    with TypeSafeClient() as c:
        yield c


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
