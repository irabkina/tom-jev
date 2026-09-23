"""Experiment 02 — re-representation.

Takes scenarios in one representation, re-represents them into another,
and measures whether JEV scores shift.

    python experiments/02_rerepresentation.py
"""

from __future__ import annotations

import json
import pathlib

from dotenv import load_dotenv

from jev_rerepresentation import jev, representation
from jev_rerepresentation.models import Scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"


def load_scenarios() -> list[Scenario]:
    """Load scenarios from scenarios/*.json."""
    return [Scenario.model_validate_json(p.read_text()) for p in sorted(SCENARIOS.glob("*.json"))]


def query_model(prompt: str) -> str:
    """Send a prompt to the model and return its answer.

    TODO: wire up the provider, reading ANTHROPIC_API_KEY and JEV_MODEL
    from the environment (see .env.example).
    """
    raise NotImplementedError("TODO: wire up the model call")


PAIRS = [("sparse", "rich"), ("rich", "sparse")]


def main() -> None:
    load_dotenv()
    scenarios = load_scenarios()
    if not scenarios:
        raise SystemExit("no scenarios found")

    rows = []
    for scenario in scenarios:
        for source, target in PAIRS:
            prompt = representation.rerepresent(scenario, source, target)
            answer = query_model(prompt)
            prediction = jev.evaluate(scenario, answer)
            rows.append(
                {"scenario": scenario.id, "from": source, "to": target, **prediction.scores}
            )

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "02_rerepresentation.json"
    out.write_text(json.dumps(rows, indent=2))
    print(f"wrote {len(rows)} rows to {out}")


if __name__ == "__main__":
    main()
