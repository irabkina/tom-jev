"""Experiment 04 — why the mixed history outscores the consistent arms.

Experiment 03 found that writing the history in prose is worth +0.03 once
the whole state is written the same way. But the *mixed* rendering — prose
events inside a state that is symbolic everywhere else, which is what the
`history` condition has always been — scored 0.63 against 0.48 and 0.51
for the two consistent arms. It differs from `history_prose` in three ways
at once, so that 0.12 was attributable to nothing.

Three candidates, and a chain that varies one at a time:

    history            symbolic ctx  listed events     no preamble
        |  the preamble, alone
    history_listed     symbolic ctx  listed events     preamble
        |  the event wording, alone
    history_narrated   symbolic ctx  sentence events   preamble
        |  the surroundings, alone
    history_prose      prose ctx     sentence events   preamble

Every link holds two factors fixed, so the three differences apportion the
whole gap between the endpoints and must sum to it. The last link is the
one that matters most: `history_narrated` puts narrated sentences inside a
symbolic state, so contrast against the surroundings is present, while
`history_prose` has the same sentences with nothing to contrast against.
If the history's advantage is salience rather than anything about
epistemic access, that link carries it.

What each outcome would mean is in notes/experimental_design.md, under
*Where the mixed rendering's advantage comes from*.

The chain names the `_preamble` variants because the preamble was dropped
from the conditions in use once this run showed it never helps. Those
variants exist so this experiment stays reproducible, and for nothing
else — `history_prose_preamble` is what `history_prose` was when these
numbers were taken.

    python experiments/04_history_decomposition.py
"""

from __future__ import annotations

import itertools
import json
import pathlib

from dotenv import load_dotenv

from tom_jev import analysis, jev, scenarios
from tom_jev.models import Prediction, Scenario

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"

#: The chain, in order. Consecutive entries differ in exactly one factor.
CHAIN = [
    "history",
    "history_listed_preamble",
    "history_narrated_preamble",
    "history_prose_preamble",
]

#: What the step onto each condition changes from the one before it.
FACTOR = {
    "history_listed_preamble": "the preamble",
    "history_narrated_preamble": "the event wording",
    "history_prose_preamble": "the surroundings",
}

#: The same twelve as experiment 03, so the endpoints can be read against
#: that run's `sparse` and `rich` levels.
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
    """Acceptable mass for one pass."""
    return analysis.acceptable_mass(
        prediction, scenario.question.type, scenario.ground_truth.answers()
    )


def mean(values: list[float | None]) -> float | None:
    """Mean over the values that exist."""
    present = [v for v in values if v is not None]
    return sum(present) / len(present) if present else None


def main() -> None:
    load_dotenv()
    everything = {s.id: s for s in scenarios.load(SCENARIOS)}
    missing = [sid for sid in SLATE if sid not in everything]
    if missing:
        raise SystemExit(f"not in the corpus: {missing}")
    items = [everything[sid] for sid in SLATE]

    print(f"{len(items)} scenarios x {len(CHAIN)} conditions = {len(items) * len(CHAIN)} calls\n")

    predictions: dict[str, dict[str, Prediction]] = {}
    with jev.client() as c:
        for scenario in items:
            predictions[scenario.id] = {
                condition: jev.ask(c, scenario, condition) for condition in CHAIN
            }

    levels = {
        condition: mean([mass(predictions[s.id][condition], s) for s in items])
        for condition in CHAIN
    }

    links = {
        second: [
            analysis.compare(predictions[s.id][first], predictions[s.id][second], s) for s in items
        ]
        for first, second in itertools.pairwise(CHAIN)
    }

    RESULTS.mkdir(exist_ok=True)
    flat = [p.model_dump(mode="json") for byid in predictions.values() for p in byid.values()]
    (RESULTS / "04_history_decomposition.json").write_text(json.dumps(flat, indent=2))
    (RESULTS / "04_history_decomposition_comparisons.json").write_text(
        json.dumps(
            {k: [c.model_dump(mode="json") for c in v] for k, v in links.items()},
            indent=2,
        )
    )

    print(f"{'condition':20}{'mass':>8}{'delta':>8}   changed")
    previous = None
    for condition in CHAIN:
        level = levels[condition]
        delta = "" if previous is None else f"{level - previous:+8.2f}"
        print(f"{condition:20}{level:>8.2f}{delta:>8}   {FACTOR.get(condition, '-')}")
        previous = level

    total = levels[CHAIN[-1]] - levels[CHAIN[0]]
    print(f"\n{'total':20}{total:>16.2f}   {CHAIN[0]} -> {CHAIN[-1]}")
    print(
        "\nEach delta is a mean over 12; run-to-run drift on such a mean is about\n"
        "0.01, and about 0.08 on a single cell. See the noise floor in\n"
        "notes/experimental_design.md."
    )

    for condition, comparisons in links.items():
        print(f"\n\n=== {FACTOR[condition]}  (n={len(comparisons)})\n")
        first = CHAIN[CHAIN.index(condition) - 1]
        print(analysis.summarise(comparisons, (first, condition)))

    print(f"\nwrote {len(flat)} predictions to {RESULTS}")


if __name__ == "__main__":
    main()
