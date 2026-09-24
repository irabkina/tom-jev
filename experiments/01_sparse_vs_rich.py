"""Experiment 01 — sparse vs. rich representation.

Puts the same scenarios to Jev with and without explicit mental states, and
compares the predicted actions against ground truth.

    python experiments/01_sparse_vs_rich.py
"""

from __future__ import annotations

import json
import pathlib

from dotenv import load_dotenv

from tom_jev import jev, scenarios

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"

CONDITIONS = ["sparse", "rich"]


def main() -> None:
    load_dotenv()
    items = scenarios.load(SCENARIOS)
    if not items:
        raise SystemExit(f"no scenarios found in {SCENARIOS}")

    predictions = []
    with jev.client() as c:
        for scenario in items:
            for condition in CONDITIONS:
                predictions.append(jev.ask(c, scenario, condition))

    RESULTS.mkdir(exist_ok=True)
    out = RESULTS / "01_sparse_vs_rich.json"
    out.write_text(json.dumps([p.model_dump(mode="json") for p in predictions], indent=2))

    for p in predictions:
        print(p.flat())

    print()
    for condition in CONDITIONS:
        scored = [p for p in predictions if p.condition == condition and p.correct is not None]
        if scored:
            hits = sum(p.correct for p in scored)
            print(f"{condition:7} {hits}/{len(scored)} correct")

    # Where mental state is required, sparse should do worse than rich.
    needs_mental = {s.id for s in items if s.annotations.mental_state_required}
    if needs_mental:
        print(f"\nscenarios annotated mental_state_required ({len(needs_mental)}):")
        for condition in CONDITIONS:
            scored = [
                p
                for p in predictions
                if p.condition == condition and p.scenario_id in needs_mental
                if p.correct is not None
            ]
            if scored:
                hits = sum(p.correct for p in scored)
                print(f"  {condition:7} {hits}/{len(scored)} correct")

    print(f"\nwrote {len(predictions)} predictions to {out}")


if __name__ == "__main__":
    main()
