"""Comparing a sparse pass against a rich pass.

Five measures. Influence, utility and outcome run in increasing strength
over the probability mass on the correct answers; acceptable mass is the
level utility measures a change in; entropy is orthogonal to correctness
entirely:

    influence   1/2 * sum_a |P_rich(a) - P_sparse(a)|
                Total variation distance between the two distributions.
                Did re-representation move the model at all, anywhere?

    acceptable  sum over acceptable a of P(a), per pass
    mass        How much weight each pass put on answers that count as
                correct. A level, not a change. Reported for both passes
                because a utility of +0.10 means one thing rising from
                0.05 and quite another rising from 0.85.

    utility      P_rich(y*) - P_sparse(y*)
                Signed change in acceptable mass. Did that movement go the
                right way? Exactly acceptable_mass_rich minus
                acceptable_mass_sparse.

    outcome     categorical change in argmax correctness
                One of correction, regression, stable_correct,
                stable_incorrect. The strongest measure and the coarsest:
                it ignores everything below the argmax.

    entropy     Shannon entropy of each pass, in bits, and its change
                How undecided the model is, independent of correctness.
                The only measure needing no ground truth, so it is the one
                that stays meaningful where a scenario is ambiguous by
                design — a stimulus that genuinely underdetermines the
                answer should produce a spread distribution, and entropy
                is what records that rather than scoring it as failure.

Utility and outcome are defined over the *acceptable set* — every answer a
scenario counts as correct — not a single answer. For an unambiguous
scenario that set has one member and both reduce to their earlier
definitions.

Influence and utility are independent: a representation can move the model
a long way without helping — mass shifting between two incorrect options
registers full influence and zero utility. With only two options TV reduces
to `abs(utility)`, so the two coincide on binary questions and separate
only once a question offers three or more.

Outcome stays categorical rather than collapsing to "did it improve": a
regression and a scenario both passes get wrong are different failures, and
an accuracy delta hides which occurred.

Reported alongside the measures, but *not* one of them:

    relevant    annotations.belief_changes_expected_action

An a priori claim by the scenario designer that representing belief ought
to change which action is expected. It is an experimental annotation, not
an empirical finding: it records what the scenario was built to test, and
says nothing about what Jev did. Whether re-representation actually
mattered is what influence, utility and outcome measure.

Keeping it in the table lets design intent be read against measured
result — including where they disagree, which is itself informative — but
it must never be substituted for a measure.
"""

from __future__ import annotations

from collections.abc import Sequence
from enum import StrEnum
from math import log2

from pydantic import BaseModel, Field, computed_field

from .models import Prediction, Scenario


class Outcome(StrEnum):
    """Categorical change in argmax correctness between the two passes.

    The four cells of sparse-correct x rich-correct. Kept categorical
    rather than reduced to "did it improve": a regression and a scenario
    both passes get wrong are different failures, and averaging them into
    one accuracy delta hides which happened.
    """

    CORRECTION = "correction"  # sparse wrong -> rich right
    REGRESSION = "regression"  # sparse right -> rich wrong
    STABLE_CORRECT = "stable_correct"  # both right
    STABLE_INCORRECT = "stable_incorrect"  # both wrong


def _distribution(prediction: Prediction, question_type: str) -> dict[str, float]:
    """The probability distribution over options, or {} if none was returned."""
    return prediction.answers.get(question_type, {}).get("probabilities") or {}


def world_conflict(scenario: Scenario) -> bool:
    """Does any represented belief contradict the objective world state?

    Derived from the scenario's own content rather than read off an
    annotation: a conflict exists when a mental state and a world_state
    fact share a proposition — same predicate, subject, object and
    location — but disagree on its value.

    Second-order beliefs are skipped. A belief *about another agent's
    belief* makes no claim about the world — the nested belief could
    itself be wrong without anyone being mistaken about how things are —
    so there is no known conflict to detect.

    This is the in-memory reference implementation. `world.has_conflict`
    computes the same thing by querying the Neo4j graph, which is the
    source of truth; this one needs no database, so it serves as the
    cross-check that keeps the two honest (see tests/test_world.py).
    """
    facts = {
        (p.predicate, p.subject, p.object, p.location): p.value
        for p in scenario.world_state
        if p.proposition is None
    }
    for mental in scenario.mental_state:
        held = mental.proposition
        if held.proposition is not None:
            continue
        key = (held.predicate, held.subject, held.object, held.location)
        if key in facts and facts[key] != held.value:
            return True
    return False


def _argmax(prediction: Prediction, question_type: str) -> str | None:
    """The option the model selected."""
    return prediction.answers.get(question_type, {}).get("choice")


def acceptable_mass(
    prediction: Prediction, question_type: str, answers: Sequence[str]
) -> float | None:
    """Total probability the pass put on answers that count as correct.

    A level rather than a change: 0.0 means the pass placed no weight on
    any acceptable answer, 1.0 means all of it. Utility is the difference
    between the rich and sparse levels, so this is what utility is a
    change *in* — reported alongside it because a +0.10 shift means
    something very different from 0.05 than from 0.85.
    """
    p = _distribution(prediction, question_type)
    if not p:
        return None
    return sum(p.get(a, 0.0) for a in answers)


def utility(
    sparse: Prediction, rich: Prediction, question_type: str, answers: Sequence[str]
) -> float | None:
    """Signed change in probability mass on the acceptable answers.

    Positive means re-representation moved the model toward a correct
    answer, negative means away. With a single acceptable answer this is
    P_rich(y*) - P_sparse(y*); with several it is the mass on the whole
    set, so spreading probability among equally correct readings counts as
    neither gain nor loss.
    """
    before = acceptable_mass(sparse, question_type, answers)
    after = acceptable_mass(rich, question_type, answers)
    if before is None or after is None:
        return None
    return after - before


def entropy(prediction: Prediction, question_type: str) -> float | None:
    """Shannon entropy of the answer distribution, in bits.

    How undecided the model is, independent of whether it is right. 0.0 is
    certainty; log2(len(options)) is a uniform spread. Needs no ground
    truth, so it stays meaningful for scenarios that are ambiguous by
    design, where utility and outcome do not apply.
    """
    p = _distribution(prediction, question_type)
    if not p:
        return None
    return -sum(v * log2(v) for v in p.values() if v > 0)


def influence(sparse: Prediction, rich: Prediction, question_type: str) -> float | None:
    """Total variation distance between the sparse and rich distributions.

        influence = 1/2 * sum_a |P_rich(a) - P_sparse(a)|

    0.0 means re-representation moved nothing; 1.0 means the two passes put
    their mass on disjoint options. Direction-agnostic, and defined over
    every option rather than only the correct one — so probability that
    moves between two *incorrect* options still counts as influence, with
    no corresponding utility.

    With two options this reduces to `abs(utility)`; the two measures only
    come apart once a question offers three or more.
    """
    p, q = _distribution(sparse, question_type), _distribution(rich, question_type)
    if not p or not q:
        return None
    return 0.5 * sum(abs(q.get(a, 0.0) - p.get(a, 0.0)) for a in p | q)


class Comparison(BaseModel):
    """One scenario's sparse pass measured against its rich pass."""

    scenario_id: str
    scenario_set: str | None = None
    variant: str | None = None

    # A priori experimental annotation, carried for reference. Not a
    # measure, and never a substitute for one — see the module docstring.
    belief_changes_expected_action: bool | None = None

    # Computed from the scenario's own content (the Neo4j world graph),
    # not annotated.
    world_conflict: bool | None = None

    influence: float | None = None
    utility: float | None = None

    acceptable_mass_sparse: float | None = None
    acceptable_mass_rich: float | None = None

    entropy_sparse: float | None = None
    entropy_rich: float | None = None

    sparse_choice: str | None = None
    rich_choice: str | None = None
    truth: str | None = None
    acceptable: list[str] = Field(default_factory=list)

    @computed_field
    @property
    def entropy_change(self) -> float | None:
        """Signed change in entropy. Positive means rich is less decided."""
        if self.entropy_sparse is None or self.entropy_rich is None:
            return None
        return self.entropy_rich - self.entropy_sparse

    @computed_field
    @property
    def ambiguous(self) -> bool:
        """Does the scenario admit more than one correct answer by design?"""
        return len(self.acceptable) > 1

    @computed_field
    @property
    def outcome(self) -> Outcome | None:
        """Which of the four argmax-correctness cells this scenario fell in.

        Correctness means landing anywhere in the acceptable set, so a
        scenario that is ambiguous by design is not scored wrong for
        picking a different acceptable reading.
        """
        if not self.acceptable or self.sparse_choice is None or self.rich_choice is None:
            return None
        sparse_right = self.sparse_choice in self.acceptable
        rich_right = self.rich_choice in self.acceptable
        if sparse_right and rich_right:
            return Outcome.STABLE_CORRECT
        if not sparse_right and not rich_right:
            return Outcome.STABLE_INCORRECT
        return Outcome.CORRECTION if rich_right else Outcome.REGRESSION

    @property
    def correction(self) -> bool:
        """Sparse missed the truth and rich hit it."""
        return self.outcome is Outcome.CORRECTION

    @property
    def regressed(self) -> bool:
        """Sparse hit the truth and rich missed it."""
        return self.outcome is Outcome.REGRESSION


def compare(
    sparse: Prediction,
    rich: Prediction,
    scenario: Scenario,
    *,
    conflict: bool | None = None,
) -> Comparison:
    """Measure one scenario's sparse pass against its rich pass.

    `conflict` is the world/belief conflict for this scenario, normally
    supplied by `world.has_conflict` from the graph. When omitted it falls
    back to the in-memory `world_conflict` above.
    """
    question_type = scenario.question.type
    acceptable = scenario.ground_truth.answers()
    return Comparison(
        scenario_id=scenario.id,
        scenario_set=scenario.scenario_set,
        variant=scenario.variant.type if scenario.variant else None,
        belief_changes_expected_action=scenario.annotations.belief_changes_expected_action,
        world_conflict=world_conflict(scenario) if conflict is None else conflict,
        influence=influence(sparse, rich, question_type),
        utility=utility(sparse, rich, question_type, acceptable),
        acceptable_mass_sparse=acceptable_mass(sparse, question_type, acceptable),
        acceptable_mass_rich=acceptable_mass(rich, question_type, acceptable),
        entropy_sparse=entropy(sparse, question_type),
        entropy_rich=entropy(rich, question_type),
        sparse_choice=_argmax(sparse, question_type),
        rich_choice=_argmax(rich, question_type),
        truth=scenario.ground_truth.answer,
        acceptable=acceptable,
    )


def summarise(comparisons: list[Comparison]) -> str:
    """Render the three measures per scenario, with totals."""
    if not comparisons:
        return "(no comparisons)"

    # `variant` is omitted: the scenario id already ends in it.
    header = (
        f"{'scenario':24} {'relevant':>8} | {'conflict':>8} {'influence':>9} "
        f"{'utility':>8} {'acc sp':>7} {'acc ri':>7} {'H sp':>6} {'H ri':>6}  outcome"
    )
    lines = [
        f"{'':24} {'annotated':>8} | {'measured':<64}",
        header,
        "-" * 112,
    ]
    for c in comparisons:
        relevant = c.belief_changes_expected_action
        lines.append(
            f"{c.scenario_id:24} "
            f"{'' if relevant is None else str(relevant):>8} | "
            f"{'' if c.world_conflict is None else str(c.world_conflict):>8} "
            f"{'' if c.influence is None else format(c.influence, '9.2f')} "
            f"{'' if c.utility is None else format(c.utility, '+8.2f')} "
            f"{'' if c.acceptable_mass_sparse is None else format(c.acceptable_mass_sparse, '7.2f')} "
            f"{'' if c.acceptable_mass_rich is None else format(c.acceptable_mass_rich, '7.2f')} "
            f"{'' if c.entropy_sparse is None else format(c.entropy_sparse, '6.2f')} "
            f"{'' if c.entropy_rich is None else format(c.entropy_rich, '6.2f')}  "
            f"{c.outcome or ''}{' *' if c.ambiguous else ''}"
        )

    scored = [c for c in comparisons if c.influence is not None]
    if scored:
        lines.append("")
        with_entropy = [c for c in scored if c.entropy_change is not None]
        with_mass = [c for c in scored if c.acceptable_mass_sparse is not None]
        lines.append(
            f"n={len(scored)}  "
            f"mean influence {sum(c.influence for c in scored) / len(scored):.2f}  "
            f"mean utility {sum(c.utility for c in scored) / len(scored):+.2f}  "
            f"mean entropy change "
            f"{sum(c.entropy_change for c in with_entropy) / len(with_entropy):+.2f}"
        )
        if with_mass:
            lines.append(
                "mean acceptable mass "
                f"{sum(c.acceptable_mass_sparse for c in with_mass) / len(with_mass):.2f}"
                " sparse -> "
                f"{sum(c.acceptable_mass_rich for c in with_mass) / len(with_mass):.2f} rich"
            )
        counts = {o: sum(c.outcome is o for c in comparisons) for o in Outcome}
        lines.append("  ".join(f"{name} {count}" for name, count in counts.items()))
        lines.append("")
        if any(c.ambiguous for c in comparisons):
            lines.append(
                "* ambiguous by design: several answers acceptable, so outcome and utility "
                "score the set,"
            )
            lines.append("  and a spread distribution is a valid response rather than a failure.")
        lines.append(
            "relevant is the a priori annotation belief_changes_expected_action, "
            "recorded for reference;"
        )
        lines.append(
            "whether re-representation mattered is measured by influence, utility and outcome."
        )
    return "\n".join(lines)
