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

One condition, twelve scenarios. The baseline is `history_symbolic` as
already run in experiment 03 over the same twelve — identical stimuli,
verified byte-identical, and a mean over twelve drifts about 0.01 between
runs. Cheap because only the one cell is new.

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

#: Where experiment 03 left the baseline pass.
BASELINE_RUN = RESULTS / "03_surface_form.json"
BASELINE = "history_symbolic"
CONDITION = "history_symbolic_bare"

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


def baseline() -> dict[str, Prediction]:
    """The `history_symbolic` pass from experiment 03, by scenario id."""
    if not BASELINE_RUN.exists():
        raise SystemExit(f"{BASELINE_RUN} not found; run experiments/03_surface_form.py first")
    rows = json.loads(BASELINE_RUN.read_text())
    return {
        row["scenario_id"]: Prediction.model_validate(row)
        for row in rows
        if row["condition"] == BASELINE
    }


def main() -> None:
    load_dotenv()
    everything = {s.id: s for s in scenarios.load(SCENARIOS)}
    items = [everything[sid] for sid in SLATE]

    before = baseline()
    missing = [s.id for s in items if s.id not in before]
    if missing:
        raise SystemExit(f"no {BASELINE} baseline for: {missing}")

    print(f"{len(items)} scenarios x 1 condition = {len(items)} calls\n")
    with jev.client() as c:
        after = {s.id: jev.ask(c, s, CONDITION) for s in items}

    comparisons = [analysis.compare(before[s.id], after[s.id], s) for s in items]

    RESULTS.mkdir(exist_ok=True)
    (RESULTS / "05_preamble.json").write_text(
        json.dumps([p.model_dump(mode="json") for p in after.values()], indent=2)
    )
    (RESULTS / "05_preamble_comparisons.json").write_text(
        json.dumps([c.model_dump(mode="json") for c in comparisons], indent=2)
    )

    with_preamble = mean([mass(before[s.id], s) for s in items])
    without = mean([mass(after[s.id], s) for s in items])
    print(f"{BASELINE:24}{with_preamble:>8.2f}   (experiment 03)")
    print(f"{CONDITION:24}{without:>8.2f}")
    print(f"{'preamble costs':24}{with_preamble - without:>+8.2f}\n")

    print(analysis.summarise(comparisons, ("with", "without")))
    print(f"\nwrote {len(after)} predictions to {RESULTS}")


if __name__ == "__main__":
    main()
