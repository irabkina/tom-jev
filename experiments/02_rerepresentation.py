"""Experiment 02 — re-representation.

Takes scenarios in one representation, re-represents them into another, and
measures whether Jev's answers shift.

    python experiments/02_rerepresentation.py
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

PAIRS = [("sparse", "rich"), ("rich", "sparse")]

# Keep in sync with experiment 01 so the two runs stay comparable.
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
            for source, target in PAIRS:
                state = representation.rerepresent(scenario, source, target)
                predictions.append(
                    jev.evaluate(
                        c,
                        state,
                        QUESTIONS,
                        scenario_id=scenario.id,
                        condition=f"{source}->{target}",
                    )
                )

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "02_rerepresentation.json"
    out.write_text(json.dumps([p.model_dump(mode="json") for p in predictions], indent=2))

    for row in (p.flat() for p in predictions):
        print(row)
    print(f"\nwrote {len(predictions)} predictions to {out}")


if __name__ == "__main__":
    main()
