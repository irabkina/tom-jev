"""Experiment 06 — candidate triggers for escalating from history to rich.

Reads the predictions experiment 01 already wrote and makes no model calls.
Every candidate is computable at run time from passes the policy has
already paid for, and none uses ground truth; only the *evaluation* does.

The three triggers tested in *Sparse-state signals do not reliably identify
the need for re-representation* all read the sparse output. The middle pass
allows a fourth kind — a trigger that is an intervention rather than a
classifier, running the cheap enrichment and watching what happens to the
model's own distribution.

The candidates in TRIGGERS were fixed before any was measured. With 68
scenarios and 23 positives that limits how far any one of them can be
believed, so the per-family breakdown matters more than the headline table:
a signal that only reproduces the task-family prior is not a signal. See
*A cheap pass that raises its own entropy is the first usable trigger* in
notes/experimental_design.md.

    python experiments/06_triggers.py
"""

from __future__ import annotations

import json
import math
import pathlib
from collections.abc import Callable
from typing import Any

from tom_jev import scenarios

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
SCENARIOS = ROOT / "scenarios"

PREDICTIONS = RESULTS / "01_sparse_vs_rich.json"
COMPARISONS = RESULTS / "01_history_vs_rich_comparisons.json"

#: The middle condition, as experiment 01 runs it. A stored run labels
#: each pass with the condition name in force when it was made, and this
#: one was called `history_symbolic` before the preamble was dropped and
#: the names were tidied, so both labels are accepted rather than paying
#: 204 calls again to relabel a file.
MIDDLE = "history"
MIDDLE_ALIASES = (MIDDLE, "history_symbolic")

#: Each candidate maps a scenario's measurements to whether it escalates.
#: Fixed before measurement. The last two are baselines rather than
#: candidates: a task-family prior, and escalating unconditionally.
TRIGGERS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "never": lambda r: False,
    "the cheap pass moved the answer (TV > 0.2)": lambda r: r["moved"] > 0.2,
    "the cheap pass moved the answer (TV > 0.1)": lambda r: r["moved"] > 0.1,
    "the cheap pass raised entropy": lambda r: r["d_entropy"] > 0.0,
    "raised entropy by more than 0.2 bits": lambda r: r["d_entropy"] > 0.2,
    "the history pass is still uncertain": lambda r: r["h_entropy"] > 0.5,
    "moved a lot OR is still uncertain": lambda r: r["moved"] > 0.2 or r["h_entropy"] > 0.5,
    "the task is action prediction": lambda r: r["family"] == "action_prediction",
    "always": lambda r: True,
}

#: Two earlier candidates are retired rather than kept as baselines.
#: `the sparse pass is uncertain` reads the pass before the intervention
#: and never beat the family prior; `sparse and history disagree` scored
#: below base rate on the argmax label and above it on the mass labels,
#: fires 11 times either way, and is too small to read.


#: What counts as needing rich. The argmax flip is the label the first
#: pass used; it is the strictest, and it ignores a pass that moves a lot
#: of mass the right way without crossing the top-1 boundary. The two mass
#: thresholds grade that instead. 0.10 sits just above the measured
#: single-cell noise floor of 0.08; 0.25 is clear of it.
LABELS: dict[str, Callable[[dict[str, Any]], bool]] = {
    "rich corrects the history argmax": lambda r: r["corrected"],
    "rich adds more than 0.10 acceptable mass": lambda r: r["gain"] > 0.10,
    "rich adds more than 0.25 acceptable mass": lambda r: r["gain"] > 0.25,
}


def distribution(prediction: dict[str, Any], question_type: str) -> dict[str, float]:
    """The answer distribution for the question the scenario asks."""
    return (prediction.get("answers") or {}).get(question_type, {}).get("probabilities") or {}


def choice(prediction: dict[str, Any], question_type: str) -> str | None:
    """The option the pass selected."""
    return (prediction.get("answers") or {}).get(question_type, {}).get("choice")


def mean(values: list[float]) -> float:
    """Mean, or nan for an empty set."""
    return sum(values) / len(values) if values else float("nan")


def entropy(p: dict[str, float]) -> float:
    """Shannon entropy in bits."""
    return -sum(v * math.log2(v) for v in p.values() if v > 0)


def total_variation(p: dict[str, float], q: dict[str, float]) -> float:
    """How far one distribution moved from another."""
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q))


def measurements() -> list[dict[str, Any]]:
    """One row per scenario: what a policy could see, and what happened."""
    if not PREDICTIONS.exists():
        raise SystemExit(f"{PREDICTIONS} not found; run experiments/01_sparse_vs_rich.py first")

    passes: dict[str, dict[str, Any]] = {}
    for row in json.loads(PREDICTIONS.read_text()):
        passes.setdefault(row["scenario_id"], {})[row["condition"]] = row
    outcomes = {c["scenario_id"]: c for c in json.loads(COMPARISONS.read_text())}

    rows = []
    for scenario in scenarios.load(SCENARIOS):
        question = scenario.question.type
        by_condition = passes.get(scenario.id, {})
        sparse = by_condition.get("sparse")
        middle = next((by_condition[a] for a in MIDDLE_ALIASES if a in by_condition), None)
        outcome = outcomes.get(scenario.id)
        if not (sparse and middle and outcome):
            continue
        before, after = distribution(sparse, question), distribution(middle, question)
        if not before or not after:
            continue
        rows.append(
            {
                "id": scenario.id,
                "family": scenario.taxonomy.task_family,
                "disagree": choice(sparse, question) != choice(middle, question),
                "d_entropy": entropy(after) - entropy(before),
                "moved": total_variation(before, after),
                "h_entropy": entropy(after),
                "s_entropy": entropy(before),
                # The comparison file calls its baseline `sparse`; under
                # experiment 01 that baseline is the middle pass.
                "h_mass": outcome["acceptable_mass_sparse"] or 0.0,
                "r_mass": outcome["acceptable_mass_rich"] or 0.0,
                "h_final_entropy": outcome["entropy_sparse"] or 0.0,
                "r_final_entropy": outcome["entropy_rich"] or 0.0,
                "h_correct": outcome["sparse_choice"] in outcome["acceptable"],
                "r_correct": outcome["rich_choice"] in outcome["acceptable"],
                "corrected": outcome["outcome"] == "correction",
                "regressed": outcome["outcome"] == "regression",
                "gain": (outcome["acceptable_mass_rich"] or 0.0)
                - (outcome["acceptable_mass_sparse"] or 0.0),
            }
        )
    return rows


def score(
    rows: list[dict[str, Any]],
    fires: Callable[[dict[str, Any]], bool],
    needed: Callable[[dict[str, Any]], bool],
) -> tuple[int, float, float, float]:
    """Fires, precision, recall and F1 against one definition of need."""
    fired = [r for r in rows if fires(r)]
    positives = sum(bool(needed(r)) for r in rows)
    hits = sum(bool(needed(r)) for r in fired)
    precision = hits / len(fired) if fired else 0.0
    recall = hits / positives if positives else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return len(fired), precision, recall, f1


def materialise(
    rows: list[dict[str, Any]], fires: Callable[[dict[str, Any]], bool]
) -> dict[str, float]:
    """What the corpus looks like once a policy has escalated where it fires.

    Every scenario ends up with exactly one answer: rich's where the policy
    paid for it, the history pass's where it did not. The `final` measures
    are taken on that mixture, which is what a deployed policy would
    actually produce, rather than on either condition alone.
    """
    fired = [r for r in rows if fires(r)]
    mass = [r["r_mass"] if fires(r) else r["h_mass"] for r in rows]
    entropies = [r["r_final_entropy"] if fires(r) else r["h_final_entropy"] for r in rows]
    correct = [r["r_correct"] if fires(r) else r["h_correct"] for r in rows]

    available = sum(r["gain"] for r in rows)
    recovered = sum(r["gain"] for r in fired)
    corrections = sum(r["corrected"] for r in rows)
    regressions = sum(r["regressed"] for r in rows)

    return {
        "fires": len(fired),
        "rate": len(fired) / len(rows),
        "mass": mean(mass),
        "entropy": mean(entropies),
        "accuracy": sum(correct) / len(rows),
        "recovery": recovered / available if available else float("nan"),
        "corrections": sum(r["corrected"] for r in fired),
        "corrections_total": corrections,
        "regressions": sum(r["regressed"] for r in fired),
        "regressions_total": regressions,
    }


def main() -> None:
    rows = measurements()
    entropy_rose = TRIGGERS["the cheap pass raised entropy"]

    for label, needed in LABELS.items():
        positives = sum(bool(needed(r)) for r in rows)
        print(f"NEED: {label}")
        print(f"  n={len(rows)}  positives {positives}  base rate {positives / len(rows):.2f}\n")
        print(f"  {'trigger':44}{'fires':>7}{'prec':>7}{'rec':>7}{'F1':>7}")
        for name, fires in TRIGGERS.items():
            count, precision, recall, f1 = score(rows, fires, needed)
            print(f"  {name:44}{count:>7}{precision:>7.2f}{recall:>7.2f}{f1:>7.2f}")

        print("\n  entropy rise, conditioned on task family:")
        for family in ("action_prediction", "goal_recognition"):
            subset = [r for r in rows if r["family"] == family]
            base = sum(bool(needed(r)) for r in subset) / len(subset)
            count, precision, _, _ = score(subset, entropy_rose, needed)
            print(
                f"    {family:20} n={len(subset):>3}  base {base:.2f}"
                f"   fires {count:>3} at precision {precision:.2f}"
                f"   lift {precision - base:+.2f}"
            )
        print()

    baseline = materialise(rows, TRIGGERS["never"])
    ceiling = materialise(rows, TRIGGERS["always"])
    print("what each policy is worth once it has run.")
    print(
        f"  never escalating ends at {baseline['mass']:.2f} mass,"
        f" {baseline['accuracy']:.2f} accuracy;"
        f" escalating always ends at {ceiling['mass']:.2f} and {ceiling['accuracy']:.2f}."
    )
    print(
        f"  recovery is the share of the {ceiling['mass'] - baseline['mass']:+.2f}"
        f" mass between them that the policy collects.\n"
    )

    print(
        f"  {'policy':44}{'fires':>6}{'esc':>6}"
        f"{'mass':>7}{'ent':>6}{'acc':>6}{'recov':>7}{'corr':>7}{'reg':>6}"
    )
    for name, fires in TRIGGERS.items():
        m = materialise(rows, fires)
        corrections = f"{m['corrections']:.0f}/{m['corrections_total']:.0f}"
        regressions = f"{m['regressions']:.0f}/{m['regressions_total']:.0f}"
        print(
            f"  {name:44}{m['fires']:>6.0f}{m['rate']:>6.0%}"
            f"{m['mass']:>7.2f}{m['entropy']:>6.2f}{m['accuracy']:>6.2f}"
            f"{m['recovery']:>7.0%}{corrections:>7}{regressions:>6}"
        )

    print("\n  esc    share of the corpus escalated")
    print("  mass   mean final acceptable mass          ent   mean final entropy, bits")
    print("  acc    final accuracy (argmax acceptable)  recov share of the available gain")
    print("  corr   argmax corrections materialised     reg   regressions materialised")

    print("\nentropy rise, conditioned on task family, against the argmax label:")
    for family in ("action_prediction", "goal_recognition"):
        subset = [r for r in rows if r["family"] == family]
        base = sum(r["corrected"] for r in subset) / len(subset)
        count, precision, _, _ = score(subset, entropy_rose, LABELS["rich corrects the history argmax"])
        print(
            f"  {family:20} n={len(subset):>3}  base {base:.2f}"
            f"   fires {count:>3} at precision {precision:.2f}   lift {precision - base:+.2f}"
        )


if __name__ == "__main__":
    main()
