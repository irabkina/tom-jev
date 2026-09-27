"""Experiment 05 — does the preamble hurt a purely symbolic history too?

Experiment 04 decomposed the mixed history's advantage into three factors
and found the preamble the largest, at -0.08 acceptable mass. It was added
"so a superseded early event does not read as a contradiction of the
current world_state", and it does the opposite.

That was measured on narrated events, where the preamble is one prose
sentence among several. In `history_symbolic` it would be the only prose in
the state, so the effect may not transfer, and the consequence matters:
if it does, run 03's symbolic arm understated its own middle condition,
and the share of the sparse-rich gap the history closes is roughly a
quarter rather than a ninth.

Two conditions, twelve scenarios, differing in the preamble and nothing
else. When first run the baseline was reused from experiment 03, where
`history_symbolic` still carried the preamble; the preamble has since been
dropped from that condition and lives in `history_symbolic_preamble`, so
both passes are now made here.

    python experiments/05_preamble.py
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

BASELINE = "history_symbolic_preamble"
CONDITION = "history_symbolic"

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
    items = [everything[sid] for sid in SLATE]

    print(f"{len(items)} scenarios x 2 conditions = {len(items) * 2} calls\n")
    with jev.client() as c:
        before = {s.id: jev.ask(c, s, BASELINE) for s in items}
        after = {s.id: jev.ask(c, s, CONDITION) for s in items}

    comparisons = [analysis.compare(before[s.id], after[s.id], s) for s in items]

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "05_preamble.json").write_text(
        json.dumps(
            [p.model_dump(mode="json") for p in (*before.values(), *after.values())], indent=2
        )
    )
    (RESULTS / "05_preamble_comparisons.json").write_text(
        json.dumps([c.model_dump(mode="json") for c in comparisons], indent=2)
    )

    with_preamble = mean([mass(before[s.id], s) for s in items])
    without = mean([mass(after[s.id], s) for s in items])
    print(f"{BASELINE:28}{with_preamble:>8.2f}")
    print(f"{CONDITION:28}{without:>8.2f}")
    print(f"{'preamble costs':28}{with_preamble - without:>+8.2f}\n")

    print(analysis.summarise(comparisons, ("with", "without")))
    print(f"\nwrote {len(after)} predictions to {RESULTS}")


if __name__ == "__main__":
    main()
