"""Experiment 01 — sparse vs. rich representation.

Puts the same scenarios to Jev under both representations and compares the
structured answers.

    python experiments/01_sparse_vs_rich.py
"""

from __future__ import annotations

import json
import pathlib

import yaml
from dotenv import load_dotenv
from typesafe_sdk import Choice, Noul

from tom_jev import jev, representation
from tom_jev.models import Scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"

CONDITIONS = ["sparse", "rich"]

# TODO: replace with the measures under study. Noul returns a 0-1 truth
# value with no confidence; Choice and Score also return confidence and a
# probability distribution.
QUESTIONS = {
    "informed": Noul(instructions="Does every participant know the key fact?"),
    "holder": Choice(
        instructions="Who holds the true belief?",
        criteria={"first": None, "second": None, "both": None, "neither": None},
    ),
}


def load_scenarios() -> list[Scenario]:
    """Load scenarios from scenarios/*.yaml and scenarios/*.yml."""
    paths = sorted(p for pattern in ("*.yaml", "*.yml") for p in SCENARIOS.glob(pattern))
    return [Scenario.model_validate(yaml.safe_load(p.read_text())) for p in paths]


def main() -> None:
    load_dotenv()
    scenarios = load_scenarios()
    if not scenarios:
        raise SystemExit(f"no scenarios found in {SCENARIOS}")

    predictions = []
    with jev.client() as c:
        for scenario in scenarios:
            for condition in CONDITIONS:
                state = representation.render(scenario, condition)
                predictions.append(
                    jev.evaluate(
                        c,
                        state,
                        QUESTIONS,
                        scenario_id=scenario.id,
                        condition=condition,
                    )
                )

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "01_sparse_vs_rich.json"
    out.write_text(json.dumps([p.model_dump(mode="json") for p in predictions], indent=2))

    for row in (p.flat() for p in predictions):
        print(row)
    print(f"\nwrote {len(predictions)} predictions to {out}")


if __name__ == "__main__":
    main()
