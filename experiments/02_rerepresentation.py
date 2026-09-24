"""Experiment 02 — re-representation.

Takes scenarios in one representation, re-represents them into another, and
measures whether Jev's predicted actions shift.

    python experiments/02_rerepresentation.py
"""

from __future__ import annotations

import json
import pathlib

from dotenv import load_dotenv

from tom_jev import jev, representation, scenarios

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"

PAIRS = [("sparse", "rich"), ("rich", "sparse")]


def main() -> None:
    load_dotenv()
    items = scenarios.load(SCENARIOS)
    if not items:
        raise SystemExit(f"no scenarios found in {SCENARIOS}")

    predictions = []
    with jev.client() as c:
        for scenario in items:
            for source, target in PAIRS:
                state = representation.rerepresent(scenario, source, target)
                prediction = jev.evaluate(
                    c,
                    state,
                    jev.question_for(scenario),
                    scenario_id=scenario.id,
                    condition=f"{source}->{target}",
                )
                predictions.append(jev.score(prediction, scenario))

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "02_rerepresentation.json"
    out.write_text(json.dumps([p.model_dump(mode="json") for p in predictions], indent=2))

    for p in predictions:
        print(p.flat())
    print(f"\nwrote {len(predictions)} predictions to {out}")


if __name__ == "__main__":
    main()
