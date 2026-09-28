"""Give a scenario an epistemic-access history entailing its stated beliefs.

A history says how an agent came to believe something instead of asserting
the belief: they were present when a claim was settled one way, and absent
when it was settled another. That makes the `history` condition carry the
evidence for a belief while `rich` carries the belief itself, so the two
differ in explicitness rather than in content.

The history is built from the beliefs of the agent the question is about,
at whatever depth they hold them. What Sam believes about Alex's belief
sits at the same representational level as what Sam believes about the
coffee: a claim Sam witnessed being settled, and may since have missed
being settled otherwise. So an attribution scenario's history records Sam
watching Alex come to think the meeting is in the office — not Alex's own
access to the meeting, which predicts nothing about Sam.

Every belief contributes exactly two events, whether it is true or false.
A false belief is settled in view and then settled again out of view; a
true one is settled twice in view. Without that padding each true-belief
cell ran one event and each false-belief cell two, so event count alone
classified the condition and a model could have scored well by counting.

Derived from the scenario rather than authored, which is what guarantees
the entailment; `analysis.history_matches_mental_state` then recovers the
beliefs from the events and checks them against the stated ones.

    python scripts/add_histories.py

Idempotent: scenarios that already carry a history are left alone.
"""

from __future__ import annotations

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from tom_jev import analysis, scenarios
from tom_jev.models import Proposition, Scenario

ROOT = pathlib.Path(__file__).resolve().parents[1] / "scenarios"

HEADER = """
# How the agent came to believe what they believe. The history entails the
# mental states below rather than restating them, so the `history`
# condition carries the evidence while `rich` carries the belief. Derived
# from the scenario by scripts/add_histories.py."""


def settled_elsewhere(scenario: Scenario, claim: Proposition) -> Proposition | None:
    """The proposition that actually holds, where it contradicts `claim`.

    This is the event the agent missed. For a claim about the world, the
    world settles it: `world_state` says where the report really is. For a
    claim about another agent's belief, that agent settles it: their own
    stated mental state says what they really think.

    Returns None when nothing contradicts the claim — the belief is true,
    and there was no change to miss.
    """
    if claim.proposition is None:
        # Prefer the fact that says where the thing actually is over the
        # one that says only that it is not here. Both contradict the
        # belief, but world_state lists them in no fixed order, and
        # letting that order decide made the narration differ between
        # cells of the same 2x2 — a difference in phrasing confounded
        # with the condition.
        elsewhere = [
            fact
            for fact in scenario.world_state
            if fact.predicate == claim.predicate
            and fact.subject == claim.subject
            and fact.location != claim.location
            and fact.value
            and claim.value
        ]
        if elsewhere:
            return elsewhere[0]
        for fact in scenario.world_state:
            if fact.signature() == claim.signature() and fact.value != claim.value:
                return fact
        return None

    held = claim.innermost()
    for mental in scenario.mental_state:
        if mental.agent != claim.subject:
            continue
        actual = mental.proposition
        if actual.proposition is not None or actual.subject != held.subject:
            continue
        if actual.signature() == held.signature() and actual.value == held.value:
            return None
        return Proposition(predicate=claim.predicate, subject=claim.subject, proposition=actual)
    return None


def other_location(scenario: Scenario, claim: Proposition) -> str | None:
    """A location the claim's subject is elsewhere said to occupy.

    Taken from `world_state` in file order, so the alternative a padded
    true-belief cell uses is the same one the matching false-belief cell
    moves to, rather than an arbitrary third place.
    """
    innermost = claim.innermost()
    for fact in scenario.world_state:
        if (
            fact.predicate == innermost.predicate
            and fact.subject == innermost.subject
            and fact.location is not None
            and fact.location != innermost.location
        ):
            return fact.location
    for location in scenario.entities.locations:
        if location.id != innermost.location:
            return location.id
    return None


def superseded(scenario: Scenario, claim: Proposition) -> Proposition | None:
    """What the agent saw before, and then saw corrected.

    Padding for a belief that is true, so that a true-belief cell runs to
    the same length as a false-belief one. Without it every true cell has
    one event and every false cell two, and event count alone classifies
    the condition — a model could score well by counting and never
    represent a belief at all.

    The added sighting is superseded *in view*, so the agent's last
    witnessed event is still the belief the scenario states and the
    entailment is untouched.

    Where a thing *is* gets superseded by moving it, since a location is
    exclusive and a move settles the claim both ways at once. Anything
    else gets flipped: availability is not exclusive across places, so
    stocking the coffee somewhere else would not supersede a belief about
    the kitchen — running out there does.
    """
    innermost = claim.innermost()
    if innermost.predicate == "located" and innermost.value is True:
        elsewhere = other_location(scenario, claim)
        if elsewhere is not None:
            return claim.relocated(elsewhere)
    if isinstance(innermost.value, bool):
        return claim.revalued(not innermost.value)
    return None


def block(claim: Proposition, witnesses: list[str], indent: str = "  ") -> str:
    """One history event, as YAML."""
    lines = [f"{indent}- proposition:"]
    lines.extend(render(claim, indent + "      "))
    if witnesses:
        lines.append(f"{indent}  witnessed_by:")
        lines.extend(f"{indent}    - {w}" for w in witnesses)
    else:
        lines.append(f"{indent}  witnessed_by: []")
    return "\n".join(lines)


def render(claim: Proposition, indent: str) -> list[str]:
    """A proposition as YAML lines, following any nesting."""
    lines = [f"{indent}predicate: {claim.predicate}", f"{indent}subject: {claim.subject}"]
    if claim.object:
        lines.append(f"{indent}object: {claim.object}")
    if claim.location:
        lines.append(f"{indent}location: {claim.location}")
    if claim.proposition is not None:
        lines.append(f"{indent}proposition:")
        lines.extend(render(claim.proposition, indent + "  "))
    else:
        lines.append(f"{indent}value: {str(claim.value).lower()}")
    return lines


def history_for(scenario: Scenario) -> str | None:
    """The YAML history block entailing this scenario's beliefs, or None."""
    events = []
    for mental in scenario.mental_state:
        if mental.agent != scenario.question.agent:
            continue  # nothing is predicted about this agent
        claim = mental.proposition
        missed = settled_elsewhere(scenario, claim)
        if missed is not None:
            # The belief is false: settled in view, then settled again
            # out of view.
            events.append(block(claim, [mental.agent]))
            events.append(block(missed, []))
        else:
            # The belief is true. Pad it to the same length with a
            # sighting the agent then saw corrected, so length does not
            # give the condition away.
            before = superseded(scenario, claim)
            if before is not None:
                events.append(block(before, [mental.agent]))
            events.append(block(claim, [mental.agent]))
    if not events:
        return None
    return HEADER + "\nhistory:\n" + "\n\n".join(events) + "\n"


def main() -> None:
    written = skipped = 0
    for scenario in scenarios.load(ROOT):
        if scenario.history:
            continue
        text = history_for(scenario)
        if text is None:
            skipped += 1
            continue
        path = next(
            p
            for p in ROOT.rglob("*.yaml")
            if p.stem == (scenario.taxonomy.lexicalization or "v1")
            and p.parent.name == scenario.taxonomy.condition
            and p.parent.parent.name == scenario.taxonomy.domain
        )
        path.write_text(path.read_text().replace("\nmental_state:", text + "\nmental_state:", 1))
        written += 1
    print(f"{written} histories written, {skipped} with no belief to derive from")

    problems = [
        (s.id, p) for s in scenarios.load(ROOT) for p in analysis.history_matches_mental_state(s)
    ]
    print(f"entailment mismatches: {problems or 'none'}")


if __name__ == "__main__":
    main()
