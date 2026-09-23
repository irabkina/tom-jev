"""Experiment 01 — sparse vs. rich representation.

Runs the same scenarios under both presentations and compares JEV scores.

    python experiments/01_sparse_vs_rich.py
"""

from __future__ import annotations

import json
import pathlib

from dotenv import load_dotenv

from jev_rerepresentation import jev, representation
from jev_rerepresentation.models import Scenario

RESULTS = pathlib.Path(__file__).resolve().parents[1] / "results"
SCENARIOS = pathlib.Path(__file__).resolve().parents[1] / "scenarios"


def load_scenarios() -> list[Scenario]:
    """Load scenarios from scenarios/*.json."""
    return [Scenario.model_validate_json(p.read_text()) for p in sorted(SCENARIOS.glob("*.json"))]


def query_model(prompt: str) -> str:
    """Send a prompt to Jev and return its answer.

    TODO: wire up typesafe_sdk.TypeSafeClient. It reads TYPESAFE_API_KEY
    from the environment and defaults to the jev-latest model.
    """
    raise NotImplementedError("TODO: wire up the Jev call")


def main() -> None:
    load_dotenv()
    scenarios = load_scenarios()
    if not scenarios:
        raise SystemExit(f"no scenarios found in {SCENARIOS}")

    rows = []
    for scenario in scenarios:
        for condition, render in (("sparse", representation.sparse), ("rich", representation.rich)):
            prompt = render(scenario)
            answer = query_model(prompt)
            prediction = jev.evaluate(scenario, answer)
            rows.append({"scenario": scenario.id, "condition": condition, **prediction.scores})

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "01_sparse_vs_rich.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
