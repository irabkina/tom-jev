"""Comparing a sparse pass against a rich pass.

Three measures over the probability mass on the correct answer, in
increasing strength:

    influence   1/2 * sum_a |P_rich(a) - P_sparse(a)|
                Total variation distance between the two distributions.
                Did re-representation move the model at all, anywhere?

    utility      P_rich(y*) - P_sparse(y*)
                Signed change in mass on the correct answer. Did that
                movement go the right way?

    correction   sparse argmax != y* and rich argmax == y*
                The strongest discrete outcome, and the coarsest: it
                ignores everything below the argmax.

Influence and utility are independent: a representation can move the model
a long way without helping — mass shifting between two incorrect options
registers full influence and zero utility. With only two options TV reduces
to `abs(utility)`, so the two coincide on binary questions and separate
only once a question offers three or more.

`regressed` is the mirror of `correction` and is reported alongside it, so
that escalation which makes things worse stays visible rather than being
buried in a mean.
"""

from __future__ import annotations

from pydantic import BaseModel

from .models import Prediction, Scenario


def _distribution(prediction: Prediction, question_type: str) -> dict[str, float]:
    """The probability distribution over options, or {} if none was returned."""
    return prediction.answers.get(question_type, {}).get("probabilities") or {}


def world_conflict(scenario: Scenario) -> bool:
    """Does any represented belief contradict the objective world state?

    Derived from the scenario's own content rather than read off an
    annotation: a conflict exists when a mental state and a world_state
    fact share a proposition — same predicate, subject, object and
    location — but disagree on its value.

    This is the divergence the sparse/rich manipulation turns on, so it is
    computed where it can be checked against the data.
    """
    facts = {(p.predicate, p.subject, p.object, p.location): p.value for p in scenario.world_state}
    return any(
        facts.get(
            (
                m.proposition.predicate,
                m.proposition.subject,
                m.proposition.object,
                m.proposition.location,
            ),
            m.proposition.value,
        )
        != m.proposition.value
        for m in scenario.mental_state
    )


def _argmax(prediction: Prediction, question_type: str) -> str | None:
    """The option the model selected."""
    return prediction.answers.get(question_type, {}).get("choice")


def utility(sparse: Prediction, rich: Prediction, question_type: str, answer: str) -> float | None:
    """Signed change in probability mass on the correct answer.

    Positive means re-representation moved the model toward the correct
    answer, negative means away from it.
    """
    p, q = _distribution(sparse, question_type), _distribution(rich, question_type)
    if not p or not q:
        return None
    return q.get(answer, 0.0) - p.get(answer, 0.0)


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
    world_conflict: bool | None = None

    influence: float | None = None
    utility: float | None = None

    sparse_choice: str | None = None
    rich_choice: str | None = None
    truth: str | None = None

    @property
    def correction(self) -> bool:
        """Sparse missed the truth and rich hit it."""
        return self.sparse_choice != self.truth and self.rich_choice == self.truth

    @property
    def regressed(self) -> bool:
        """Sparse hit the truth and rich missed it."""
        return self.sparse_choice == self.truth and self.rich_choice != self.truth


def compare(sparse: Prediction, rich: Prediction, scenario: Scenario) -> Comparison:
    """Measure one scenario's sparse pass against its rich pass."""
    question_type = scenario.question.type
    answer = scenario.ground_truth.answer
    return Comparison(
        scenario_id=scenario.id,
        scenario_set=scenario.scenario_set,
        variant=scenario.variant.type if scenario.variant else None,
        world_conflict=world_conflict(scenario),
        influence=influence(sparse, rich, question_type),
        utility=utility(sparse, rich, question_type, answer),
        sparse_choice=_argmax(sparse, question_type),
        rich_choice=_argmax(rich, question_type),
        truth=answer,
    )


def summarise(comparisons: list[Comparison]) -> str:
    """Render the three measures per scenario, with totals."""
    if not comparisons:
        return "(no comparisons)"

    lines = [
        f"{'scenario':24} {'variant':16} {'conflict':>8} {'influence':>9} {'utility':>8}  outcome",
        "-" * 83,
    ]
    for c in comparisons:
        if c.correction:
            outcome = "correction"
        elif c.regressed:
            outcome = "regressed"
        elif c.truth is None:
            outcome = ""
        else:
            outcome = "both right" if c.sparse_choice == c.truth else "both wrong"
        lines.append(
            f"{c.scenario_id:24} {c.variant or '':16} "
            f"{'' if c.world_conflict is None else str(c.world_conflict):>8} "
            f"{'' if c.influence is None else format(c.influence, '9.2f')} "
            f"{'' if c.utility is None else format(c.utility, '+8.2f')}  {outcome}"
        )

    scored = [c for c in comparisons if c.influence is not None]
    if scored:
        lines.append("")
        lines.append(
            f"n={len(scored)}  "
            f"mean influence {sum(c.influence for c in scored) / len(scored):.2f}  "
            f"mean utility {sum(c.utility for c in scored) / len(scored):+.2f}  "
            f"corrections {sum(c.correction for c in comparisons)}  "
            f"regressions {sum(c.regressed for c in comparisons)}"
        )
    return "\n".join(lines)
