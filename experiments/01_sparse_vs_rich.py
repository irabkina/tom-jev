"""Experiment 01 — sparse vs. rich representation.

Two passes over each scenario:

    sparse   what does Jev answer from the limited representation?
    rich     what does Jev answer once the agent's belief is explicitly
             represented?

Each scenario's own `question` fixes the task — goal recognition for the
coffee set, action prediction for the report set — so representation
richness is the only thing that varies between the passes.

The comparison is reported as five measures — influence, acceptable mass,
utility, outcome and entropy — rather than collapsed into one accuracy
figure. The `belief_changes_expected_action` annotation is shown beside
them for reference; it is an a priori design claim, not a measure. See
tom_jev/analysis.py.

    python experiments/01_sparse_vs_rich.py
"""

from __future__ import annotations

import json
import pathlib

from dotenv import load_dotenv

from tom_jev import analysis, jev, scenarios

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"

CONDITIONS = ["sparse", "rich"]


def main() -> None:
    load_dotenv()
    items = scenarios.load(SCENARIOS)
    if not items:
        raise SystemExit(f"no scenarios found in {SCENARIOS}")

    predictions: dict[str, dict[str, object]] = {}
    with jev.client() as c:
        for scenario in items:
            predictions[scenario.id] = {
                condition: jev.ask(c, scenario, condition) for condition in CONDITIONS
            }

    comparisons = [
        analysis.compare(
            predictions[s.id]["sparse"],
            predictions[s.id]["rich"],
            s,
        )
        for s in items
    ]

    RESULTS.mkdir(exist_ok=True)
    flat = [p.model_dump(mode="json") for byid in predictions.values() for p in byid.values()]
    (RESULTS / "01_sparse_vs_rich.json").write_text(json.dumps(flat, indent=2))
    (RESULTS / "01_sparse_vs_rich_comparisons.json").write_text(
        json.dumps([c.model_dump(mode="json") for c in comparisons], indent=2)
    )

    print(analysis.summarise(comparisons))
    print(f"\nwrote {len(flat)} predictions and {len(comparisons)} comparisons to {RESULTS}")


if __name__ == "__main__":
    main()
