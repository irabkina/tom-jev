"""Experiment 03 — surface form.

Every number the `history_mixed` condition has produced carries an unmeasured
term, because the conditions are not written in one register. `history_mixed` is
narrated prose; `sparse`, `world_state` and the `mental_state` that `rich`
adds are symbolic. So `history_mixed` differs from `rich` in wording as well as
in explicitness, and the measured gap between two renderings of identical
events was large relative to the effects being reported. See *Unresolved:
the history's surface form moves the result* in notes/experimental_design.md.

This crosses the three richness levels with two internally consistent
arms:

                world      history    mental state
    narrative   narrative  narrative  narrative
    symbolic    symbolic   symbolic   symbolic

Within an arm every section is written the same way, so the arm is a style
and the richness level is the manipulation. Two questions follow, and they
are answered by different cuts of the same 72 predictions:

    does wording lift `rich` as much as it lifts `history_mixed`?
        if it does, the effect is about surface form generally and the
        narration is not doing anything specific to event structure
    does wording lift `sparse`, which has neither a history nor a belief?
        a baseline style effect on a representation with no mental content
        at all, and the cleanest control available

Read down a column for the style contrast at fixed richness; read across a
row for the richness ladder at fixed style.

The numbers this produced are recorded in notes/experimental_design.md,
and they were taken while `history` and `history_prose` still
carried HISTORY_PREAMBLE. Experiment 04 then showed the preamble never
helps, so it was dropped from both. Re-running this now measures the same
contrast without it; the `_preamble` variants are what these conditions
were at the time.

    python experiments/03_surface_form.py
"""

from __future__ import annotations

import json
import pathlib

from dotenv import load_dotenv

from tom_jev import analysis, jev, scenarios
from tom_jev.models import Prediction, Scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"

#: The two arms, each internally consistent, in richness order.
ARMS: dict[str, list[str]] = {
    "symbolic": ["sparse", "history", "rich"],
    "narrative": ["sparse_prose", "history_prose", "rich_prose"],
}

#: Richness levels, as the pair of conditions realising each one.
LEVELS = ["sparse", "history_mixed", "rich"]

#: Twelve scenarios over four sets, three cells each: the two where the
#: belief diverges from the world, plus one control where it agrees.
#: `report` is the direct replication anchor — the original symbolic-vs-
#: prose difference was measured on its family. The others add a second
#: mental state (`meeting`), a wrong attribution (`attribution`), and the
#: longest histories in the corpus (`mailroom`, four events).
SLATE = [
    "report_false_positive",
    "report_false_negative",
    "report_true_positive",
    "mailroom_false_true",
    "mailroom_false_false",
    "mailroom_true_true",
    "meeting_false_positive",
    "meeting_false_negative",
    "meeting_true_positive",
    "attribution_false_attribution_true_belief",
    "attribution_false_attribution_false_belief",
    "attribution_true_attribution_true_belief",
]


def mass(prediction: Prediction, scenario: Scenario) -> float | None:
    """Acceptable mass, the level the comparisons are changes in."""
    return analysis.acceptable_mass(
        prediction, scenario.question.type, scenario.ground_truth.answers()
    )


def table(rows: dict[str, dict[str, float | None]], title: str) -> str:
    """A small arm x level table of means."""
    lines = [title, f"{'':12}" + "".join(f"{level:>12}" for level in LEVELS)]
    for arm, byleveL in rows.items():
        cells = "".join(
            "         n/a" if byleveL.get(level) is None else f"{byleveL[level]:>12.2f}"
            for level in LEVELS
        )
        lines.append(f"{arm:12}{cells}")
    return "\n".join(lines)


def mean(values: list[float | None]) -> float | None:
    """Mean over the values that exist."""
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else None


def main() -> None:
    load_dotenv()
    everything = {s.id: s for s in scenarios.load(SCENARIOS, split="dev")}
    missing = [sid for sid in SLATE if sid not in everything]
    if missing:
        raise SystemExit(f"not in the corpus: {missing}")
    items = [everything[sid] for sid in SLATE]

    conditions = [c for arm in ARMS.values() for c in arm]
    print(
        f"{len(items)} scenarios x {len(conditions)} conditions = "
        f"{len(items) * len(conditions)} calls\n"
    )

    predictions: dict[str, dict[str, Prediction]] = {}
    with jev.client() as c:
        for scenario in items:
            predictions[scenario.id] = {
                condition: jev.ask(c, scenario, condition) for condition in conditions
            }

    # Down a column: the same richness level in the two arms. This is the
    # style contrast, and it is the reason the experiment exists.
    style: dict[str, list[analysis.Comparison]] = {}
    for index, level in enumerate(LEVELS):
        symbolic, narrative = ARMS["symbolic"][index], ARMS["narrative"][index]
        style[level] = [
            analysis.compare(predictions[s.id][symbolic], predictions[s.id][narrative], s)
            for s in items
        ]

    # Across a row: the richness ladder inside one arm, unconfounded by
    # style because both passes are written the same way.
    ladder: dict[str, list[analysis.Comparison]] = {}
    for arm, (base, middle, rich) in ARMS.items():
        for name, (first, second) in {
            "sparse_vs_history": (base, middle),
            "history_vs_rich": (middle, rich),
            "sparse_vs_rich": (base, rich),
        }.items():
            ladder[f"{arm}/{name}"] = [
                analysis.compare(predictions[s.id][first], predictions[s.id][second], s)
                for s in items
            ]

    RESULTS.mkdir(exist_ok=True)
    flat = [p.model_dump(mode="json") for byid in predictions.values() for p in byid.values()]
    (RESULTS / "03_surface_form.json").write_text(json.dumps(flat, indent=2))
    (RESULTS / "03_surface_form_comparisons.json").write_text(
        json.dumps(
            {
                "style": {k: [c.model_dump(mode="json") for c in v] for k, v in style.items()},
                "ladder": {k: [c.model_dump(mode="json") for c in v] for k, v in ladder.items()},
            },
            indent=2,
        )
    )

    masses = {
        arm: {
            level: mean([mass(predictions[s.id][condition], s) for s in items])
            for level, condition in zip(LEVELS, arm_conditions, strict=True)
        }
        for arm, arm_conditions in ARMS.items()
    }
    print(table(masses, "mean acceptable mass"))

    print("\n\nstyle contrast, symbolic -> narrative, at each richness level")
    for level, comparisons in style.items():
        print(f"\n=== {level}  (n={len(comparisons)})\n")
        print(analysis.summarise(comparisons, ("symbolic", "narrative")))

    print("\n\nrichness ladder within each arm")
    for name, comparisons in ladder.items():
        arm, pairing = name.split("/")
        first, second = pairing.split("_vs_")
        print(f"\n=== {arm}: {first} -> {second}  (n={len(comparisons)})\n")
        print(analysis.summarise(comparisons, (first, second)))

    print(f"\nwrote {len(flat)} predictions to {RESULTS}")


if __name__ == "__main__":
    main()
