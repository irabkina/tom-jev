"""Experiment 01 — sparse vs. rich representation.

Two passes over each scenario:

    sparse   what action does Jev predict from the limited representation?
    rich     what action does Jev predict once the agent's belief is
             explicitly represented?

World/belief conflict is computed by querying the Neo4j graph the world
state is loaded into, not from the scenario annotations. The comparison is
reported as influence, utility and correction — see tom_jev/analysis.py.

    python experiments/01_sparse_vs_rich.py
"""

from __future__ import annotations

import json
import pathlib

from dotenv import load_dotenv

from tom_jev import analysis, jev, scenarios, world
from tom_jev.models import Scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"

CONDITIONS = ["sparse", "rich"]


def conflicts_from_graph(items: list[Scenario]) -> dict[str, bool]:
    """Load the world state into Neo4j and ask it which scenarios conflict.

    Falls back to the in-memory reference if the database is unreachable,
    saying so rather than quietly substituting a different computation.
    """
    try:
        with world.connect() as driver:
            for scenario in items:
                world.load(driver, scenario)
            return {s.id: world.has_conflict(driver, s.id) for s in items}
    except Exception as error:  # noqa: BLE001 - any driver failure falls back
        print(f"! neo4j unavailable ({type(error).__name__}), using in-memory conflicts: {error}")
        return {s.id: analysis.world_conflict(s) for s in items}


def main() -> None:
    load_dotenv()
    items = scenarios.load(SCENARIOS)
    if not items:
        raise SystemExit(f"no scenarios found in {SCENARIOS}")

    conflict = conflicts_from_graph(items)

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
            conflict=conflict[s.id],
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
