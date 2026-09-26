"""Experiment 01 — sparse vs. rich representation.

Three passes over each scenario:

    sparse   what does Jev answer from the limited representation?
    history  what does Jev answer given the epistemic-access history the
             belief follows from, but not the belief itself?
    rich     what does Jev answer once the agent's belief is explicitly
             represented?

The middle pass splits what the sparse pass lacks into two things: the
information, and the information made explicit. sparse -> history asks
whether the evidence alone suffices; history -> rich asks whether stating
the belief adds anything once the evidence is already there.

Only scenarios that carry a history take the middle pass. Where there is
none, `history` renders exactly as `sparse`, so querying it would buy a
guaranteed zero.

Each scenario's own `question` fixes the task — goal recognition for the
coffee set, action prediction for the report set — so representation
richness is the only thing that varies between the passes.

The comparison is reported as five measures — influence, acceptable mass,
utility, outcome and entropy — rather than collapsed into one accuracy
figure. The `belief_changes_expected_action` annotation is shown beside
them for reference; it is an a priori design claim, not a measure. See
tom_jev/analysis.py.

World/belief conflict is computed by querying the Neo4j graph the world
state is loaded into, not read from that annotation.

    python experiments/01_sparse_vs_rich.py
"""

from __future__ import annotations

import json
import pathlib

from dotenv import load_dotenv

from tom_jev import analysis, jev, scenarios, world
from tom_jev.models import Prediction, Scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"
KNOWLEDGE = ROOT / "knowledge" / "goals.yaml"

CONDITIONS = ["sparse", "history", "rich"]


def from_graph(
    items: list[Scenario], sparse: dict[str, str]
) -> tuple[dict[str, bool], dict[str, bool | None], dict[str, str], dict[str, int]]:
    """Ask the graph the three things only it can answer.

    Conflict and attribution have in-memory equivalents and fall back to
    them; the escalation trigger does not, since it needs the background
    knowledge the graph holds, and comes back empty instead.

    `sparse` maps scenario id to the sparse pass's top answer — the trigger
    is asked of what the model actually concluded, which is the whole point
    of it: a self-monitoring policy has that and nothing else.
    """
    try:
        with world.connect() as driver:
            world.load_knowledge(driver, KNOWLEDGE)
            for scenario in items:
                world.load(driver, scenario)
            return (
                {s.id: world.has_conflict(driver, s.id) for s in items},
                {s.id: _attribution(driver, s.id) for s in items},
                {s.id: str(world.answer_anomaly(driver, s, sparse[s.id])) for s in items},
                {s.id: world.mind_dependence(driver, s) for s in items},
            )
    except Exception as error:  # noqa: BLE001 - any driver failure falls back
        print(f"! neo4j unavailable ({type(error).__name__}), falling back in memory: {error}")
        return (
            {s.id: analysis.world_conflict(s) for s in items},
            {s.id: analysis.attribution_conflict(s) for s in items},
            {},
            {},
        )


def _attribution(driver, scenario_id: str) -> bool | None:
    """Does any checkable attribution disagree with what its subject holds?"""
    rows = [r for r in world.attributions(driver, scenario_id) if r["actual"] is not None]
    return None if not rows else any(r["actual"] != r["attributed"] for r in rows)


def top_answer(prediction: Prediction, scenario: Scenario) -> str:
    """The answer the pass actually gave."""
    return prediction.answers.get(scenario.question.type, {}).get("choice", "")


def main() -> None:
    load_dotenv()
    items = scenarios.load(SCENARIOS)
    if not items:
        raise SystemExit(f"no scenarios found in {SCENARIOS}")

    predictions: dict[str, dict[str, Prediction]] = {}
    with jev.client() as c:
        for scenario in items:
            wanted = [
                condition for condition in CONDITIONS if condition != "history" or scenario.history
            ]
            predictions[scenario.id] = {
                condition: jev.ask(c, scenario, condition) for condition in wanted
            }

    # The trigger is asked of the sparse answer, so the graph is queried
    # after the model rather than before it.
    sparse = {s.id: top_answer(predictions[s.id]["sparse"], s) for s in items}
    conflict, attribution, trigger, minds = from_graph(items, sparse)

    def pair(first: str, second: str, over: list[Scenario]) -> list[analysis.Comparison]:
        return [
            analysis.compare(
                predictions[s.id][first],
                predictions[s.id][second],
                s,
                conflict=conflict[s.id],
                attribution=attribution[s.id],
                trigger=trigger.get(s.id),
                mind_dependence=minds.get(s.id),
            )
            for s in over
        ]

    with_history = [s for s in items if s.history]
    pairings = {
        "sparse_vs_rich": (("sparse", "rich"), pair("sparse", "rich", items)),
        "sparse_vs_history": (("sparse", "history"), pair("sparse", "history", with_history)),
        "history_vs_rich": (("history", "rich"), pair("history", "rich", with_history)),
    }

    RESULTS.mkdir(exist_ok=True)
    flat = [p.model_dump(mode="json") for byid in predictions.values() for p in byid.values()]
    (RESULTS / "01_sparse_vs_rich.json").write_text(json.dumps(flat, indent=2))
    for name, (_, comparisons) in pairings.items():
        (RESULTS / f"01_{name}_comparisons.json").write_text(
            json.dumps([c.model_dump(mode="json") for c in comparisons], indent=2)
        )

    for name, (labels, comparisons) in pairings.items():
        print(f"\n=== {labels[0]} -> {labels[1]}  (n={len(comparisons)})\n")
        print(analysis.summarise(comparisons, labels))

    print(f"\nwrote {len(flat)} predictions to {RESULTS}")


if __name__ == "__main__":
    main()
