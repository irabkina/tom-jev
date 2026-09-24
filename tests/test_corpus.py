"""The corpus says the same thing twice, and the two must agree.

A scenario states its design in two places: the `variant.type` label, and
the propositions the label describes. Nothing stops them drifting apart —
a miscoded cell loads fine and quietly poisons every analysis grouped by
variant.

These derive the design from the content and check it against the label.
They need nothing but the corpus itself.
"""

from __future__ import annotations

import pathlib

import pytest

from tom_jev import analysis, scenarios

SCENARIOS = pathlib.Path(__file__).resolve().parents[1] / "scenarios"


@pytest.fixture(scope="session")
def corpus():
    """Every scenario, loaded once."""
    return scenarios.load(SCENARIOS)


def test_attribution_labels_match_the_propositions(corpus):
    """`<a>_attribution_<b>_belief` must match what the two conflicts say.

    The label names two independent things — whether the believer is right
    about the other agent, and whether that agent is right about the world.
    Those are exactly `attribution_conflict` and `world_conflict`, so the
    label is checkable rather than merely asserted.
    """
    items = [s for s in corpus if s.taxonomy.template == "attribution"]
    assert items, "expected an attribution set in the corpus"

    for scenario in items:
        attribution_true, _, belief_true, _ = scenario.variant.type.split("_")
        assert analysis.attribution_conflict(scenario) is (attribution_true == "false"), (
            f"{scenario.id}: label says the attribution is {attribution_true}, "
            f"propositions say conflict={analysis.attribution_conflict(scenario)}"
        )
        assert analysis.world_conflict(scenario) is (belief_true == "false"), (
            f"{scenario.id}: label says the belief is {belief_true}, "
            f"propositions say conflict={analysis.world_conflict(scenario)}"
        )


def test_belief_matches_reality_annotation_matches_the_propositions(corpus):
    """The annotation must not contradict the scenario's own content.

    Checked only where exactly one agent holds beliefs. The field says
    "does the agent's belief agree with reality" and so presumes a single
    believer; with two it is genuinely ambiguous. In the attribution set
    `false_attribution_true_belief` has Ade wrong about Juno while Juno is
    right about the world, and the annotation records the first while
    `world_conflict` measures the second. Both readings are defensible, so
    the disagreement is in the field's definition rather than in the data.

    Scenarios needing a second believer want two annotations, or a field
    that names whose belief it means.
    """
    for scenario in corpus:
        annotated = scenario.annotations.belief_matches_reality
        believers = {m.agent for m in scenario.mental_state}
        first_order = any(m.proposition.proposition is None for m in scenario.mental_state)
        if annotated is None or not first_order or len(believers) != 1:
            continue
        assert analysis.world_conflict(scenario) is not annotated, (
            f"{scenario.id}: annotated belief_matches_reality={annotated}, "
            f"propositions say world_conflict={analysis.world_conflict(scenario)}"
        )


def test_every_mentioned_entity_is_declared(corpus):
    """Nothing may reference an entity the cast omits.

    Enforced by a model validator, so this asserts the validator is
    actually reached for every file rather than re-deriving it.
    """
    for scenario in corpus:
        assert not scenario.referenced() - scenario.declared()


def test_ground_truth_is_always_selectable(corpus):
    """Every acceptable answer must be one of the offered options."""
    for scenario in corpus:
        assert set(scenario.ground_truth.answers()) <= set(scenario.question.options), (
            f"{scenario.id}: ground truth outside its options"
        )


def test_scenario_ids_are_unique(corpus):
    """Two scenarios sharing an id would collapse together in analysis."""
    ids = [s.id for s in corpus]
    assert len(ids) == len(set(ids))
