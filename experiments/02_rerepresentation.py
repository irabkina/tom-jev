"""Experiment 02 — re-representation: beliefs worked out, not read.

In every run so far `rich` has read `mental_state` straight from the
scenario file. That is why the escalation saving stays notional: the
expensive step in a two-stage architecture is *constructing* the richer
representation, and constructing it has so far cost nothing.

Here the beliefs are derived instead, by `world.materialise`, from the
epistemic history the graph holds — which settlement each agent saw last,
and what a location being exclusive implies about the ones they did not
see. The derivation is checked against `analysis.entailed_beliefs` in
tests/test_world.py, so what reaches the model is sound; what this
measures is whether it reaches the model *differently*.

It does. The derived representation is not the stated one:

    stated    exclusivity implicit, other agents' beliefs named
    direct    exclusivity implicit, only the question's agent
    derived   exclusivity explicit, only the question's agent

Two differences at once, on the same scenarios and pulling opposite ways.
Spelling exclusivity out states the belief-world conflict in so many words
instead of leaving it to be inferred. Dropping other agents removes a
distractor the attribution set exists to test resistance to. `direct` sits
between them so each can be measured alone.

Development split only. The held-out split is spent.

    python experiments/02_rerepresentation.py

Where a rendering comes out byte-identical to the stored `rich` stimulus
the call is made anyway rather than reusing the stored answer. Those
scenarios then measure run-to-run drift between that run and this one,
on exactly the comparison being made, which is worth more than the calls
it costs.
"""

from __future__ import annotations

import hashlib
import json
import pathlib

from dotenv import load_dotenv

from tom_jev import analysis, jev, representation, scenarios, world
from tom_jev.models import Prediction, Scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"

#: The stored `rich` pass these are compared against.
STORED = RESULTS / "01_sparse_vs_rich.json"

#: This experiment's own output, and a fingerprint of what was sent to
#: produce each row. A stored answer is reused only when the rendering
#: still hashes to what it hashed to then — so a change anywhere in the
#: graph, the derivation or the renderer forces the call again, and a
#: reused answer is one nothing could have changed.
OUTPUT = RESULTS / "02_rerepresentation.json"
FINGERPRINTS = RESULTS / "02_fingerprints.json"

#: Each derived condition, and whether it spells exclusivity out.
DERIVED = {"rich_direct": False, "rich_derived": True}


def fingerprint(state: dict[str, str]) -> str:
    """What was sent, as a hash, so reuse can be justified rather than assumed."""
    return hashlib.sha256(json.dumps(state, sort_keys=True).encode()).hexdigest()[:16]


def states(driver, scenario: Scenario) -> dict[str, dict[str, str]]:
    """The two derived renderings of one scenario."""
    return {
        name: representation.rerepresent(
            scenario,
            world.materialise(
                driver, scenario, agent=scenario.question.agent, exclusivity=exclusivity
            ),
        )
        for name, exclusivity in DERIVED.items()
    }


def main() -> None:
    load_dotenv()
    items = scenarios.load(SCENARIOS, split="dev")
    if not items:
        raise SystemExit(f"no dev scenarios found in {SCENARIOS}")
    if not STORED.exists():
        raise SystemExit(f"{STORED} not found; run experiments/01_sparse_vs_rich.py first")

    stored = {
        row["scenario_id"]: Prediction.model_validate(row)
        for row in json.loads(STORED.read_text())
        if row["condition"] == "rich"
    }
    missing = [s.id for s in items if s.id not in stored]
    if missing:
        raise SystemExit(f"no stored rich pass for {len(missing)} scenarios, e.g. {missing[0]}")

    rendered: dict[str, dict[str, dict[str, str]]] = {}
    with world.connect() as driver:
        for scenario in items:
            world.load(driver, scenario)
            rendered[scenario.id] = states(driver, scenario)

    previous = {
        (row["scenario_id"], row["condition"]): Prediction.model_validate(row)
        for row in (json.loads(OUTPUT.read_text()) if OUTPUT.exists() else [])
    }
    stamped = json.loads(FINGERPRINTS.read_text()) if FINGERPRINTS.exists() else {}
    reusable = {
        key: previous[key]
        for scenario in items
        for name, state in rendered[scenario.id].items()
        if (key := (scenario.id, name)) in previous
        and stamped.get(f"{scenario.id}|{name}") == fingerprint(state)
    }
    wanted = len(items) * len(DERIVED)
    print(f"{len(items)} dev scenarios, {wanted} passes: "
          f"{len(reusable)} reused unchanged, {wanted - len(reusable)} calls\n")

    predictions: dict[str, dict[str, Prediction]] = {}
    fingerprints: dict[str, str] = {}
    with jev.client() as c:
        for scenario in items:
            predictions[scenario.id] = {}
            for name, state in rendered[scenario.id].items():
                fingerprints[f"{scenario.id}|{name}"] = fingerprint(state)
                if (scenario.id, name) in reusable:
                    predictions[scenario.id][name] = reusable[(scenario.id, name)]
                    continue
                prediction = jev.evaluate(
                    c,
                    state,
                    jev.question_for(scenario),
                    scenario_id=scenario.id,
                    condition=name,
                )
                predictions[scenario.id][name] = jev.score(prediction, scenario)

    # How many scenarios each step actually changes, so a null result can
    # be read as "no effect" rather than "no difference in the stimulus".
    unchanged = {
        "stated -> direct": sum(
            representation.rich(s) == rendered[s.id]["rich_direct"] for s in items
        ),
        "direct -> derived": sum(
            rendered[s.id]["rich_direct"] == rendered[s.id]["rich_derived"] for s in items
        ),
    }

    def pair(first: str, second: str) -> list[analysis.Comparison]:
        def prediction(name: str, scenario: Scenario) -> Prediction:
            return stored[scenario.id] if name == "stated" else predictions[scenario.id][name]

        return [
            analysis.compare(prediction(first, s), prediction(second, s), s) for s in items
        ]

    pairings = {
        "stated_vs_direct": (("stated", "rich_direct"), pair("stated", "rich_direct")),
        "direct_vs_derived": (("rich_direct", "rich_derived"), pair("rich_direct", "rich_derived")),
        "stated_vs_derived": (("stated", "rich_derived"), pair("stated", "rich_derived")),
    }

    RESULTS.mkdir(exist_ok=True)
    flat = [p.model_dump(mode="json") for byid in predictions.values() for p in byid.values()]
    OUTPUT.write_text(json.dumps(flat, indent=2))
    FINGERPRINTS.write_text(json.dumps(fingerprints, indent=2, sort_keys=True))
    for name, (_, comparisons) in pairings.items():
        (RESULTS / f"02_{name}_comparisons.json").write_text(
            json.dumps([c.model_dump(mode="json") for c in comparisons], indent=2)
        )

    for name, (labels, comparisons) in pairings.items():
        print(f"\n=== {labels[0]} -> {labels[1]}  (n={len(comparisons)})\n")
        print(analysis.summarise(comparisons, labels))

    print("\nscenarios where the stimulus did not change at all:")
    for step, n in unchanged.items():
        print(f"  {step:22}{n:>3} of {len(items)}"
              f"   — these measure run-to-run drift, not the manipulation")

    print(f"\nwrote {len(flat)} predictions to {RESULTS}")


if __name__ == "__main__":
    main()
