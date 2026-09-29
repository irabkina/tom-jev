"""Experiment 08 — what the equal-length control costs.

Every belief contributes exactly two events, true or false. A false belief
is settled in view and settled again out of it; a true one is settled
twice in view, the first sighting superseded before it matters. Without
that padding each true-belief cell ran one event and each false-belief
cell two, so counting events classified the condition and a model could
have scored well on `history` without representing a belief at all.

The padding is inert by construction — the agent's last witnessed event is
still the belief the scenario states, and tests/test_world.py checks that
dropping it changes nothing entailed. Inert to the derivation is not the
same as inert to the model, and five development cells lose more than the
noise floor under `history`, all five of them padded.

This renders the padded scenarios with the superseded sightings removed
and asks Jev again, comparing each against its own stored `history` pass.
Each scenario is its own control, which is what the observational split
cannot be: padded and unpadded scenarios differ in template as well as in
padding, so a comparison between them reads composition as much as effect.

Not a new condition. The equal-length rule stays; this measures its price.

    python experiments/08_padding.py
"""

from __future__ import annotations

import json
import pathlib

from dotenv import load_dotenv

from tom_jev import analysis, jev, representation, scenarios
from tom_jev.models import Prediction, Scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"
STORED = RESULTS / "01_sparse_vs_rich.json"

#: The stored middle pass, under whichever name the run used.
MIDDLE_ALIASES = ("history", "history_symbolic")


def unpadded(scenario: Scenario) -> Scenario:
    """The same scenario with superseded sightings dropped.

    A padding event is one a witness saw and then saw overturned. Dropping
    it must leave the entailed beliefs alone — that is what made it
    padding rather than content — and `main` asserts so rather than
    trusting it.
    """
    keep = [
        event
        for index, event in enumerate(scenario.history)
        if not event.witnessed_by
        or any(analysis._current(scenario, index, who) for who in event.witnessed_by)
    ]
    return scenario.model_copy(update={"history": keep})


def is_padded(scenario: Scenario) -> bool:
    """Does this scenario carry any padding at all?"""
    return len(unpadded(scenario).history) < len(scenario.history)


def main() -> None:
    load_dotenv()
    if not STORED.exists():
        raise SystemExit(f"{STORED} not found; run experiments/01_sparse_vs_rich.py first")

    items = [s for s in scenarios.load(SCENARIOS, split="dev") if is_padded(s)]
    stored = {}
    for row in json.loads(STORED.read_text()):
        if row["condition"] in MIDDLE_ALIASES:
            stored[row["scenario_id"]] = Prediction.model_validate(row)

    trimmed = {s.id: unpadded(s) for s in items}
    for scenario in items:
        assert analysis.entailed_beliefs(trimmed[scenario.id]) == analysis.entailed_beliefs(
            scenario
        ), f"{scenario.id}: trimming changed what the history entails"

    print(f"{len(items)} padded dev scenarios, {len(items)} calls")
    print("entailment unchanged by trimming: all\n")

    predictions = {}
    with jev.client() as c:
        for scenario in items:
            state = representation.RENDERERS["history"](trimmed[scenario.id])
            prediction = jev.evaluate(
                c,
                state,
                jev.question_for(scenario),
                scenario_id=scenario.id,
                condition="history_unpadded",
            )
            predictions[scenario.id] = jev.score(prediction, scenario)

    comparisons = [
        analysis.compare(stored[s.id], predictions[s.id], s) for s in items if s.id in stored
    ]

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "08_padding.json").write_text(
        json.dumps([p.model_dump(mode="json") for p in predictions.values()], indent=2)
    )
    (RESULTS / "08_padding_comparisons.json").write_text(
        json.dumps([c.model_dump(mode="json") for c in comparisons], indent=2)
    )

    print(analysis.summarise(comparisons, ("history", "history_unpadded")))
    events = sum(len(s.history) for s in items)
    kept = sum(len(trimmed[s.id].history) for s in items)
    print(f"\nevents: {events} padded -> {kept} trimmed ({events - kept} sightings dropped)")
    print(f"wrote {len(predictions)} predictions to {RESULTS}")


if __name__ == "__main__":
    main()
