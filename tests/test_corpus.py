"""The corpus says the same thing twice, and the two must agree.

A scenario states its design in two places: the `variant.type` label, and
the propositions the label describes. Nothing stops them drifting apart —
a miscoded cell loads fine and quietly poisons every analysis grouped by
variant.

These derive the design from the content and check it against the label.
No database needed; `tests/test_world.py` checks the same derivations
against the graph.
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


def test_history_entails_the_stated_mental_state(corpus):
    """A history must imply exactly the beliefs the scenario states.

    The history is the whole manipulation: it must carry the same belief
    the `rich` condition states outright, or the middle condition tests a
    different scenario from the other two and the three passes are no
    longer comparable. A history that entailed *less* would understate
    what evidence affords; one that entailed *more* would smuggle in a
    belief `rich` never claimed.
    """
    for scenario in corpus:
        if not scenario.history:
            continue
        mismatches = analysis.history_matches_mental_state(scenario)
        assert not mismatches, f"{scenario.id}: " + "; ".join(mismatches)


def test_history_witnesses_are_agents(corpus):
    """Only an agent can witness an event.

    A location or object in `witnessed_by` passes the declared-entity
    check but entails a belief held by something that cannot hold one.
    """
    for scenario in corpus:
        agents = {e.id for e in scenario.entities.agents}
        for event in scenario.history:
            assert set(event.witnessed_by) <= agents, (
                f"{scenario.id}: {sorted(set(event.witnessed_by) - agents)} witness an event "
                "but are not agents"
            )


def test_every_scenario_carries_a_history(corpus):
    """The middle condition must cover the whole corpus.

    A scenario without a history drops out of the three-condition
    comparison, and which scenarios drop out would not be a principled
    subset — it would be whatever the derivation happened to manage.
    """
    missing = [s.id for s in corpus if not s.history]
    assert not missing, f"no history for {missing}"


def test_only_the_question_agent_witnesses_anything(corpus):
    """A history represents one agent's access: the one being predicted.

    Giving another agent access would put evidence in `history` that
    `rich` never states as that agent's belief, so the two conditions
    would stop being the same scenario. In an attribution the second
    agent appears only as the *subject* of a claim Sam witnessed — Alex
    coming to think something — never as a witness.
    """
    for scenario in corpus:
        witnesses = {w for event in scenario.history for w in event.witnessed_by}
        assert witnesses <= {scenario.question.agent}, (
            f"{scenario.id}: {sorted(witnesses - {scenario.question.agent})} witness events "
            f"but the question is about {scenario.question.agent}"
        )


def test_attribution_is_witnessed_as_an_event(corpus):
    """A second-order belief gets a history like any other belief.

    What Sam believes about Alex's belief sits at the same level as what
    Sam believes about the coffee: a claim Sam saw settled. So the
    attribution and second-order sets carry nested history events, rather
    than being excluded for holding a belief about a belief.
    """
    items = [s for s in corpus if s.taxonomy.template in ("attribution", "second_order")]
    assert items, "expected attribution and second-order sets in the corpus"
    for scenario in items:
        nested = [e for e in scenario.history if e.proposition.proposition is not None]
        assert nested, f"{scenario.id}: no history event settles a belief about a belief"


def test_event_count_does_not_give_away_the_condition(corpus):
    """Every belief contributes exactly two events, true or false.

    A false belief is settled in view and then settled again out of view.
    A true one is settled twice in view, the first sighting superseded
    before it matters. Without that padding the true-belief cells ran one
    event and the false-belief cells two, so counting events classified
    the condition and a model could have scored well on `history` without
    representing a belief at all.
    """
    for scenario in corpus:
        held = [m for m in scenario.mental_state if m.agent == scenario.question.agent]
        assert len(scenario.history) == 2 * len(held), (
            f"{scenario.id}: {len(held)} belief(s) but {len(scenario.history)} events"
        )


def test_padding_leaves_the_entailed_belief_alone(corpus):
    """A superseded sighting must not change what the history entails.

    The padding is only legitimate if the agent's last witnessed event is
    still the belief the scenario states. `history_matches_mental_state`
    checks that for the corpus as it stands; this checks the stronger
    claim that dropping the padding would not change the answer, which is
    what makes the added events inert rather than load-bearing.
    """
    for scenario in corpus:
        full = analysis.entailed_beliefs(scenario)
        witnessed_only = scenario.model_copy(
            update={"history": [e for e in scenario.history if e.witnessed_by][-1:]}
        )
        trimmed = analysis.entailed_beliefs(witnessed_only)
        for key, value in trimmed.items():
            assert full.get(key) == value, (
                f"{scenario.id}: padding changed the entailed value of {key}"
            )
