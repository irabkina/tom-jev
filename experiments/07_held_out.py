"""Experiment 07 — the pre-registered escalation policy on held-out data.

Scores the policy fixed in *The policy to be tested, fixed in advance*
against its five baselines, on the 32 scenarios of the held-out split.
Makes no model calls: it reads what experiment 01 wrote with `--split test`.

    python experiments/07_held_out.py

The policy and the baselines were written down before the corpus existed,
and the corpus before either was run, so nothing here was chosen after
seeing a number. What that buys is narrow but real: the figures below are
the first in this project that were not selected on the data they describe.

Every measure is taken on the corpus a policy actually produces — `rich`
where it escalated, the history pass where it did not — because that is
what a deployed policy would hand you. Recovery is the share of the
acceptable mass lying between never escalating and always escalating that
the policy collects; it is scale-free, which matters because the held-out
chance floor is 0.38 against the development corpus's 0.45 and the raw
masses are therefore not comparable across splits.
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

MIDDLE = "history"
MIDDLE_ALIASES = (MIDDLE, "history_symbolic")

#: The policy, then its baselines, exactly as pre-registered. The primary
#: policy requires no minimum entropy increase.
POLICIES: dict[str, Callable[[dict[str, Any]], bool]] = {
    "H(history) > H(sparse)": lambda r: r["d_entropy"] > 0.0,
    "never materialize": lambda r: False,
    "always materialize": lambda r: True,
    "H(history) > 0.5": lambda r: r["h_entropy"] > 0.5,
    "TV(sparse, history) > 0.1": lambda r: r["moved"] > 0.1,
    "task family: action prediction": lambda r: r["family"] == "action_prediction",
}

PRIMARY = "H(history) > H(sparse)"


def entropy(p: dict[str, float]) -> float:
    return -sum(v * math.log2(v) for v in p.values() if v > 0)


def total_variation(p: dict[str, float], q: dict[str, float]) -> float:
    return 0.5 * sum(abs(p.get(k, 0.0) - q.get(k, 0.0)) for k in set(p) | set(q))


def distribution(prediction: dict[str, Any], question: str) -> dict[str, float]:
    return (prediction.get("answers") or {}).get(question, {}).get("probabilities") or {}


def measurements(split: str) -> list[dict[str, Any]]:
    """One row per scenario: what a policy sees, and what happened."""
    suffix = "" if split == "dev" else f"_{split}"
    predictions = RESULTS / f"01_sparse_vs_rich{suffix}.json"
    comparisons = RESULTS / f"01_history_vs_rich_comparisons{suffix}.json"
    if not predictions.exists():
        raise SystemExit(
            f"{predictions} not found; run experiments/01_sparse_vs_rich.py --split {split}"
        )

    passes: dict[str, dict[str, Any]] = {}
    for row in json.loads(predictions.read_text()):
        passes.setdefault(row["scenario_id"], {})[row["condition"]] = row
    outcomes = {c["scenario_id"]: c for c in json.loads(comparisons.read_text())}

    rows = []
    for scenario in scenarios.load(SCENARIOS, split=split):
        question = scenario.question.type
        byname = passes.get(scenario.id, {})
        sparse = byname.get("sparse")
        middle = next((byname[a] for a in MIDDLE_ALIASES if a in byname), None)
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
                "function": scenario.taxonomy.template,
                "d_entropy": entropy(after) - entropy(before),
                "h_entropy": entropy(after),
                "moved": total_variation(before, after),
                # The comparison file calls its baseline `sparse`; under
                # experiment 01 that baseline is the middle pass.
                "h_mass": outcome["acceptable_mass_sparse"] or 0.0,
                "r_mass": outcome["acceptable_mass_rich"] or 0.0,
                "h_entropy_final": outcome["entropy_sparse"] or 0.0,
                "r_entropy_final": outcome["entropy_rich"] or 0.0,
                "h_correct": outcome["sparse_choice"] in outcome["acceptable"],
                "r_correct": outcome["rich_choice"] in outcome["acceptable"],
                "corrected": outcome["outcome"] == "correction",
                "regressed": outcome["outcome"] == "regression",
                "gain": (outcome["acceptable_mass_rich"] or 0.0)
                - (outcome["acceptable_mass_sparse"] or 0.0),
            }
        )
    return rows


def materialise(rows: list[dict[str, Any]], fires: Callable[[dict[str, Any]], bool]) -> dict:
    """What the corpus looks like once the policy has run."""
    fired = [r for r in rows if fires(r)]
    available = sum(r["gain"] for r in rows)
    return {
        "fires": len(fired),
        "rate": len(fired) / len(rows),
        "mass": sum(r["r_mass"] if fires(r) else r["h_mass"] for r in rows) / len(rows),
        "entropy": sum(
            r["r_entropy_final"] if fires(r) else r["h_entropy_final"] for r in rows
        )
        / len(rows),
        "accuracy": sum(bool(r["r_correct"] if fires(r) else r["h_correct"]) for r in rows)
        / len(rows),
        "recovery": (sum(r["gain"] for r in fired) / available) if available else float("nan"),
        "corrections": sum(r["corrected"] for r in fired),
        "corrections_total": sum(r["corrected"] for r in rows),
        "regressions": sum(r["regressed"] for r in fired),
        "regressions_total": sum(r["regressed"] for r in rows),
    }


def table(rows: list[dict[str, Any]], title: str) -> None:
    print(f"{title}  (n={len(rows)})")
    print(
        f"  {'policy':32}{'esc':>6}{'mass':>7}{'ent':>6}{'acc':>6}"
        f"{'recov':>7}{'corr':>8}{'reg':>7}"
    )
    for name, fires in POLICIES.items():
        m = materialise(rows, fires)
        mark = " *" if name == PRIMARY else "  "
        corr = "{}/{}".format(m["corrections"], m["corrections_total"])
        reg = "{}/{}".format(m["regressions"], m["regressions_total"])
        print(
            f"  {name:30}{mark}{m['rate']:>6.0%}{m['mass']:>7.2f}{m['entropy']:>6.2f}"
            f"{m['accuracy']:>6.2f}{m['recovery']:>7.0%}{corr:>8}{reg:>7}"
        )
    print()


def main() -> None:
    held = measurements("test")
    dev = measurements("dev")

    table(held, "HELD OUT — the pre-registered comparison")
    table(dev, "DEVELOPMENT — the same policies, for reference")

    print("the primary comparison: escalation rate against gain recovered")
    print(f"  {'policy':32}{'held out':>20}{'development':>20}")
    for name, fires in POLICIES.items():
        h, d = materialise(held, fires), materialise(dev, fires)
        mark = " *" if name == PRIMARY else "  "
        left = "{:.0%} esc -> {:.0%}".format(h["rate"], h["recovery"])
        right = "{:.0%} esc -> {:.0%}".format(d["rate"], d["recovery"])
        print(f"  {name:30}{mark}{left:>20}{right:>20}")

    print("\ndoes the policy beat the free prior inside each cell of the cross?")
    print(f"  {'cell':40}{'n':>4}{'base':>7}{'policy':>9}{'family':>9}")
    for family in ("action_prediction", "goal_recognition"):
        for function in ("discriminative", "inhibitory"):
            sub = [r for r in held if r["family"] == family and r["function"] == function]
            if not sub:
                continue
            base = materialise(sub, POLICIES["never materialize"])
            policy = materialise(sub, POLICIES[PRIMARY])
            prior = materialise(sub, POLICIES["task family: action prediction"])
            print(
                f"  {family + ' / ' + function:40}{len(sub):>4}"
                f"{base['mass']:>7.2f}{policy['mass']:>9.2f}{prior['mass']:>9.2f}"
            )

    print("\nwhere the policy fired, by cell of the cross")
    print(f"  {'cell':40}{'fires':>7}{'of':>4}{'mean gain fired':>17}{'quiet':>8}")
    for family in ("action_prediction", "goal_recognition"):
        for function in ("discriminative", "inhibitory"):
            sub = [r for r in held if r["family"] == family and r["function"] == function]
            on = [r["gain"] for r in sub if POLICIES[PRIMARY](r)]
            off = [r["gain"] for r in sub if not POLICIES[PRIMARY](r)]
            fired = f"{sum(on) / len(on):+.2f}" if on else "  -  "
            quiet = f"{sum(off) / len(off):+.2f}" if off else "  -  "
            print(
                f"  {family + ' / ' + function:40}{len(on):>7}{len(sub):>4}{fired:>17}{quiet:>8}"
            )

    print("\nregressions available to incur")
    for label, rows in (("held out", held), ("development", dev)):
        n = sum(r["regressed"] for r in rows)
        worse = [r["id"] for r in rows if r["r_mass"] < r["h_mass"] - 0.08]
        print(f"  {label:14} {n} argmax regressions;"
              f" {len(worse)} scenarios where rich lost more than the noise floor in mass")
        for i in worse:
            print(f"                   {i}")

    print("\nfunction, pooled across task family")
    print(f"  {'function':20}{'n':>4}{'never':>8}{'always':>8}{'gain':>8}{'policy esc':>12}")
    for function in ("discriminative", "inhibitory"):
        sub = [r for r in held if r["function"] == function]
        never, always = materialise(sub, POLICIES["never materialize"]), materialise(
            sub, POLICIES["always materialize"]
        )
        policy = materialise(sub, POLICIES[PRIMARY])
        print(
            f"  {function:20}{len(sub):>4}{never['mass']:>8.2f}{always['mass']:>8.2f}"
            f"{always['mass'] - never['mass']:>+8.2f}{policy['rate']:>12.0%}"
        )


if __name__ == "__main__":
    main()
