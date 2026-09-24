"""Generate scenario files from compact per-domain specs.

Every item in a template shares one structure; only the surface content and
the option count vary. Writing them by hand invites two problems: the 2x2
drifts between domains, and any single item can be quietly tuned until it
behaves. Generating them from a spec fixes the structure once, so a domain
is a few lines of vocabulary and the cells are guaranteed parallel.

    python scripts/generate_scenarios.py

Writes under scenarios/<task_family>/<template>/<domain>/<condition>/v1.yaml,
never overwriting a file that already exists.

Four templates:

    first_order         an agent believes an object is somewhere; predict
                        where they go. Truth follows the belief.
    second_order        an agent believes *another* agent believes it;
                        predict where the first goes to meet the second.
    attribution         both agents' beliefs are represented and may
                        diverge independently. Truth follows the
                        attribution, so the other two are distractors.
    goal_recognition    the action is observed and held constant; infer the
                        goal. A belief that rules the primary goal out
                        leaves an ambiguous remainder.
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass, field

ROOT = pathlib.Path(__file__).resolve().parents[1] / "scenarios"

Named = tuple[str, str]  # (id, display name)


def _entity(pair: Named) -> str:
    return f"    - id: {pair[0]}\n      name: {pair[1]}"


def _entities(agents: list[Named], locations: list[Named], objects: list[Named]) -> str:
    blocks = []
    for label, group in (("agents", agents), ("locations", locations), ("objects", objects)):
        if group:
            blocks.append(f"  {label}:\n" + "\n".join(_entity(p) for p in group))
    return "entities:\n" + "\n\n".join(blocks)


def _located(subject: str, locations: list[Named], true_at: str) -> str:
    return "\n\n".join(
        f"  - predicate: located\n"
        f"    subject: {subject}\n"
        f"    location: {loc}\n"
        f"    value: {str(loc == true_at).lower()}"
        for loc, _ in locations
    )


def _wrap(text: str, indent: str = "    ", width: int = 74) -> str:
    words, lines, current = text.split(), [], indent
    for word in words:
        if len(current) + len(word) + 1 > width and current.strip():
            lines.append(current.rstrip())
            current = indent + word
        else:
            current = f"{current} {word}" if current.strip() else current + word
    lines.append(current.rstrip())
    return "\n".join(lines)


def _header(lines: list[str]) -> str:
    return "\n".join(f"# {line}".rstrip() for line in lines)


@dataclass
class Spec:
    """Vocabulary for one domain. Structure comes from the template."""

    domain: str
    blurb: str
    agent: Named
    locations: list[Named]
    objects: list[Named] = field(default_factory=list)
    other: Named | None = None  # second agent, for second_order / attribution
    subject: str = ""  # the thing whose location varies
    goal_type: str = "obtain"
    # goal_recognition only
    observation: tuple[str, str] = ("", "")  # (event type, carried object)
    resource: Named = ("", "")
    primary_goal: str = ""
    other_goals: list[str] = field(default_factory=list)
    affordances: list[Named] = field(default_factory=list)
    lex: str = "v1"

    @property
    def slug(self) -> str:
        """Scenario id prefix — distinct per lexicalization."""
        return self.domain if self.lex == "v1" else f"{self.domain}_{self.lex}"

    @property
    def options(self) -> list[str]:
        return [f"go_to_{loc}" for loc, _ in self.locations]


def _annotations(*, supports: bool, matches: bool, changes: bool, tags: list[str]) -> str:
    return (
        "annotations:\n"
        f"  world_supports_action: {str(supports).lower()}\n"
        "  agent_believes_action_supported: true\n"
        f"  belief_matches_reality: {str(matches).lower()}\n"
        f"  belief_changes_expected_action: {str(changes).lower()}\n"
        "  tags:\n" + "\n".join(f"    - {t}" for t in tags)
    )


def first_order(spec: Spec, condition: str) -> str:
    """Agent believes the object is somewhere; predict where they go."""
    target, alt = spec.locations[0][0], spec.locations[1][0]
    world, belief = {
        "true_positive": (target, target),
        "false_positive": (alt, target),
        "false_negative": (target, alt),
        "true_negative": (alt, alt),
    }[condition]
    truth = belief
    names = dict(spec.locations)
    aligned = world == belief

    head = _header(
        [
            f"{spec.domain} — first-order belief, {condition.replace('_', ' ')}",
            "",
            spec.blurb,
            "",
            f"reality        {names[world]}",
            f"belief         {names[belief]}",
            "",
            "Truth follows the belief: the agent goes where they think it is."
            if not aligned
            else "Belief and reality agree, so the world state alone suffices.",
        ]
    )
    return f"""{head}

id: {spec.slug}_{condition}
description: >
{_wrap(spec.blurb + f" They believe it is in the {names[belief]}.", "  ")}

scenario_set: {spec.domain}

variant:
  type: {condition}

{_entities([spec.agent], spec.locations, spec.objects)}

observations: []

world_state:
{_located(spec.subject, spec.locations, world)}

goals:
  - agent: {spec.agent[0]}
    type: {spec.goal_type}
    object: {spec.subject}

mental_state:
  - type: belief
    agent: {spec.agent[0]}
    proposition:
      predicate: located
      subject: {spec.subject}
      location: {belief}
      value: true

question:
  type: action_prediction
  agent: {spec.agent[0]}
  options:
{chr(10).join(f"    - {o}" for o in spec.options)}

ground_truth:
  answer: go_to_{truth}
  explanation: >
{
        _wrap(
            f"{spec.agent[1]} believes the {names.get(spec.subject, spec.subject)} "
            f"is in the {names[belief]} and should go there"
            + ("." if aligned else f", though it is actually in the {names[world]}."),
            "    ",
        )
    }

{
        _annotations(
            supports=aligned,
            matches=aligned,
            changes=not aligned,
            tags=["first_order"]
            + (
                ["belief_reality_match", "control"]
                if aligned
                else ["false_belief", "belief_reality_mismatch", "rerepresentation_target"]
            ),
        )
    }
"""


def second_order(spec: Spec, condition: str) -> str:
    """Agent believes another agent believes it; predict where the first goes."""
    target, alt = spec.locations[0][0], spec.locations[1][0]
    world, attributed = {
        "true_positive": (target, target),
        "false_positive": (alt, target),
        "false_negative": (target, alt),
        "true_negative": (alt, alt),
    }[condition]
    names = dict(spec.locations)
    aligned = world == attributed
    other = spec.other

    head = _header(
        [
            f"{spec.domain} — second-order belief, {condition.replace('_', ' ')}",
            "",
            spec.blurb,
            "",
            f"reality                    {names[world]}",
            f"{spec.agent[1]} believes {other[1]} believes  {names[attributed]}",
            "",
            f"{other[1]}'s own belief is not represented, so the attribution cannot be",
            f"wrong about {other[1]} — only about the world.",
        ]
    )
    return f"""{head}

id: {spec.slug}_{condition}
description: >
{
        _wrap(
            spec.blurb
            + f" {spec.agent[1]} believes {other[1]} expects it in the {names[attributed]}.",
            "  ",
        )
    }

scenario_set: {spec.domain}

variant:
  type: {condition}

{_entities([spec.agent, other], spec.locations, spec.objects)}

observations: []

world_state:
{_located(spec.subject, spec.locations, world)}

goals:
  - agent: {spec.agent[0]}
    type: meet
    target_agent: {other[0]}

mental_state:
  - type: belief
    agent: {spec.agent[0]}
    proposition:
      predicate: believes
      subject: {other[0]}
      proposition:
        predicate: located
        subject: {spec.subject}
        location: {attributed}
        value: true

question:
  type: action_prediction
  agent: {spec.agent[0]}
  options:
{chr(10).join(f"    - {o}" for o in spec.options)}

ground_truth:
  answer: go_to_{attributed}
  explanation: >
{
        _wrap(
            f"{spec.agent[1]} expects {other[1]} where {spec.agent[1]} believes {other[1]} thinks it is, "
            f"the {names[attributed]}"
            + ("." if aligned else f", though it is actually in the {names[world]}."),
            "    ",
        )
    }

{
        _annotations(
            supports=aligned,
            matches=aligned,
            changes=not aligned,
            tags=["nested_belief", "social_prediction"]
            + (
                ["belief_reality_match", "control"]
                if aligned
                else ["belief_reality_mismatch", "rerepresentation_target"]
            ),
        )
    }
"""


def attribution(spec: Spec, condition: str) -> str:
    """Both agents' beliefs represented; truth follows the attribution."""
    target, alt, third = (loc for loc, _ in spec.locations[:3])
    world, other_belief, attributed = {
        "true_attribution_true_belief": (target, target, target),
        "true_attribution_false_belief": (alt, third, third),
        "false_attribution_true_belief": (target, target, alt),
        "false_attribution_false_belief": (alt, third, target),
    }[condition]
    names = dict(spec.locations)
    other = spec.other
    aligned = world == attributed

    head = _header(
        [
            f"{spec.domain} — attribution, {condition.replace('_', ' ')}",
            "",
            spec.blurb,
            "",
            f"reality                    {names[world]}",
            f"{other[1]} believes             {names[other_belief]}",
            f"{spec.agent[1]} believes {other[1]} believes  {names[attributed]}",
            "",
            f"Truth follows the attribution. {other[1]}'s actual belief and the world are",
            f"both stated in the rich representation and unavailable to {spec.agent[1]};",
            "reading either as theirs is a perspective error.",
        ]
    )
    return f"""{head}

id: {spec.slug}_{condition}
description: >
{
        _wrap(
            spec.blurb
            + f" {spec.agent[1]} believes {other[1]} expects it in the {names[attributed]}, while {other[1]} actually expects the {names[other_belief]}.",
            "  ",
        )
    }

scenario_set: {spec.domain}

variant:
  type: {condition}

{_entities([spec.agent, other], spec.locations, spec.objects)}

observations: []

world_state:
{_located(spec.subject, spec.locations, world)}

goals:
  - agent: {spec.agent[0]}
    type: meet
    target_agent: {other[0]}

mental_state:
  - type: belief
    agent: {spec.agent[0]}
    proposition:
      predicate: believes
      subject: {other[0]}
      proposition:
        predicate: located
        subject: {spec.subject}
        location: {attributed}
        value: true

  - type: belief
    agent: {other[0]}
    proposition:
      predicate: located
      subject: {spec.subject}
      location: {other_belief}
      value: true

question:
  type: action_prediction
  agent: {spec.agent[0]}
  options:
{chr(10).join(f"    - {o}" for o in spec.options)}

ground_truth:
  answer: go_to_{attributed}
  explanation: >
{
        _wrap(
            f"{spec.agent[1]} goes where {spec.agent[1]} believes {other[1]} expects it, the "
            f"{names[attributed]}. {other[1]} actually expects the {names[other_belief]}, and it is "
            f"really in the {names[world]}; neither is available to {spec.agent[1]}.",
            "    ",
        )
    }

{
        _annotations(
            supports=aligned,
            matches=aligned,
            changes=not aligned,
            tags=["nested_belief", "attribution_error", "social_prediction", "perspective_taking"]
            + (["control"] if aligned else ["rerepresentation_target"]),
        )
    }
"""


def goal_recognition(spec: Spec, condition: str) -> str:
    """Observation held constant; infer the goal. Belief can rule one out."""
    available, believes = {
        "true_positive": (True, True),
        "false_positive": (False, True),
        "false_negative": (True, False),
        "true_negative": (False, False),
    }[condition]
    place, place_name = spec.locations[0]
    event, carried = spec.observation
    resource, resource_name = spec.resource
    options = [spec.primary_goal, *spec.other_goals]
    ambiguous = not believes

    head = _header(
        [
            f"{spec.domain} — goal recognition, {condition.replace('_', ' ')}",
            "",
            spec.blurb,
            "",
            "The observation is constant across all four conditions:",
            (
                f"  {spec.agent[1]} {event.replace(chr(95), chr(32))} the {place_name} "
                f"carrying the {dict(spec.objects).get(carried, carried)}."
            ),
            "",
            f"reality        {resource_name} {'available' if available else 'unavailable'}",
            f"belief         {resource_name} {'available' if believes else 'unavailable'}",
            "",
            f"With {resource_name} ruled out the remaining goals are underdetermined,"
            if ambiguous
            else f"The belief supports {spec.primary_goal}.",
            "so several answers count as correct." if ambiguous else "",
        ]
    )
    affordances = "\n\n".join(
        f"  - predicate: located\n    subject: {aid}\n    location: {place}\n    value: true"
        for aid, _ in spec.affordances
    )
    truth_block = (
        f"  answer: {spec.other_goals[0]}\n  acceptable:\n"
        + "\n".join(f"    - {g}" for g in spec.other_goals)
        if ambiguous
        else f"  answer: {spec.primary_goal}"
    )
    return f"""{head}

id: {spec.slug}_{condition}
description: >
{
        _wrap(
            spec.blurb
            + f" The {resource_name} is {'available' if available else 'unavailable'}, and they believe it is {'available' if believes else 'unavailable'}.",
            "  ",
        )
    }

scenario_set: {spec.domain}

variant:
  type: {condition}

{_entities([spec.agent], spec.locations, spec.objects + spec.affordances)}

observations:
  - type: {event}
    agent: {spec.agent[0]}
    destination: {place}

  - type: carries
    agent: {spec.agent[0]}
    object: {carried}

world_state:
  - predicate: available
    subject: {resource}
    location: {place}
    value: {str(available).lower()}

{affordances}

mental_state:
  - type: belief
    agent: {spec.agent[0]}
    proposition:
      predicate: available
      subject: {resource}
      location: {place}
      value: {str(believes).lower()}

question:
  type: goal
  agent: {spec.agent[0]}
  options:
{chr(10).join(f"    - {o}" for o in options)}

ground_truth:
{truth_block}
  explanation: >
{
        _wrap(
            (
                f"{spec.agent[1]} believes there is no {resource_name}, so the goal is not "
                f"{spec.primary_goal}. What remains is underdetermined and the observation does "
                "not distinguish it, so every remaining goal counts."
            )
            if ambiguous
            else (
                f"{spec.agent[1]} believes the {resource_name} is there and is carrying what it "
                f"takes to use it, so the goal is {spec.primary_goal}."
            ),
            "    ",
        )
    }

{
        _annotations(
            supports=available == believes,
            matches=available == believes,
            changes=not believes,
            tags=["first_order", "goal_recognition"]
            + (
                ["ambiguous_by_design", "rerepresentation_target"]
                if ambiguous
                else ["belief_reality_match", "control"]
            ),
        )
    }
"""


TEMPLATES = {
    "first_order": (
        first_order,
        "action_prediction",
        ["true_positive", "false_positive", "false_negative", "true_negative"],
    ),
    "second_order": (
        second_order,
        "action_prediction",
        ["true_positive", "false_positive", "false_negative", "true_negative"],
    ),
    "attribution": (
        attribution,
        "action_prediction",
        [
            "true_attribution_true_belief",
            "true_attribution_false_belief",
            "false_attribution_true_belief",
            "false_attribution_false_belief",
        ],
    ),
    "goal_recognition": (
        goal_recognition,
        "goal_recognition",
        ["true_positive", "false_positive", "false_negative", "true_negative"],
    ),
}


def write(template: str, spec: Spec) -> list[pathlib.Path]:
    """Emit one domain's four condition files. Never overwrites."""
    render, family, conditions = TEMPLATES[template]
    folder = "first_order" if template == "goal_recognition" else template
    written = []
    for condition in conditions:
        path = ROOT / family / folder / spec.domain / condition / f"{spec.lex}.yaml"
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(spec, condition))
        written.append(path)
    return written


# --------------------------------------------------------------------------
# Domains. Vocabulary only — every structural decision lives in the template
# above, so these cannot drift from each other. Option counts are spread from
# three to five so influence and utility have room to diverge and entropy has
# a wider range.
# --------------------------------------------------------------------------

DOMAINS: list[tuple[str, Spec]] = [
    # ---- first order: an agent seeks an object ----------------------------
    (
        "first_order",
        Spec(
            domain="lighthouse",
            blurb="The keeper needs the fog-signal crank before the weather closes in.",
            agent=("mira", "Mira"),
            subject="crank",
            locations=[
                ("lamp_room", "lamp room"),
                ("engine_shed", "engine shed"),
                ("boat_store", "boat store"),
                ("cellar", "cellar"),
            ],
            objects=[("crank", "fog-signal crank")],
        ),
    ),
    (
        "first_order",
        Spec(
            domain="bakery",
            blurb="The baker needs the proofing basket before the next batch rises.",
            agent=("osei", "Osei"),
            subject="basket",
            locations=[
                ("cold_room", "cold room"),
                ("flour_store", "flour store"),
                ("back_bench", "back bench"),
                ("delivery_van", "delivery van"),
                ("pantry", "pantry"),
            ],
            objects=[("basket", "proofing basket")],
        ),
    ),
    # ---- second order: one agent reasons about another's belief -----------
    (
        "second_order",
        Spec(
            domain="ferry",
            blurb="The deckhand wants to find the pilot before the crossing starts.",
            agent=("noor", "Noor"),
            other=("wen", "Wen"),
            subject="briefing",
            locations=[
                ("wheelhouse", "wheelhouse"),
                ("galley", "galley"),
                ("cargo_deck", "cargo deck"),
            ],
            objects=[("briefing", "crew briefing")],
        ),
    ),
    (
        "second_order",
        Spec(
            domain="gallery",
            blurb="The curator wants to catch the artist before the doors open.",
            agent=("ilse", "Ilse"),
            other=("tavo", "Tavo"),
            subject="hanging",
            locations=[
                ("atrium", "atrium"),
                ("print_room", "print room"),
                ("loading_bay", "loading bay"),
                ("mezzanine", "mezzanine"),
            ],
            objects=[("hanging", "hanging session")],
        ),
    ),
    # ---- attribution: both beliefs represented ----------------------------
    (
        "attribution",
        Spec(
            domain="newsroom",
            blurb="The editor wants to reach the stringer before the edition locks.",
            agent=("ade", "Ade"),
            other=("juno", "Juno"),
            subject="handover",
            locations=[
                ("copy_desk", "copy desk"),
                ("wire_room", "wire room"),
                ("roof_deck", "roof deck"),
                ("archive", "archive"),
            ],
            objects=[("handover", "handover")],
        ),
    ),
    (
        "attribution",
        Spec(
            domain="observatory",
            blurb="The astronomer wants to find the night assistant before the slot opens.",
            agent=("pell", "Pell"),
            other=("saoirse", "Saoirse"),
            subject="changeover",
            locations=[
                ("dome", "dome"),
                ("control_room", "control room"),
                ("spectrograph_lab", "spectrograph lab"),
                ("tape_vault", "tape vault"),
                ("dormitory", "dormitory"),
            ],
            objects=[("changeover", "shift changeover")],
        ),
    ),
    # ---- goal recognition: observation fixed, goal inferred ---------------
    (
        "goal_recognition",
        Spec(
            domain="darkroom",
            blurb="A photographer is seen heading for the darkroom with an exposed roll.",
            agent=("ruth", "Ruth"),
            locations=[("darkroom", "darkroom")],
            objects=[("roll", "exposed roll")],
            observation=("walks_to", "roll"),
            resource=("developer", "developer"),
            primary_goal="develop_film",
            other_goals=["collect_prints", "clean_trays"],
            affordances=[("drying_line", "drying line"), ("wash_sink", "wash sink")],
        ),
    ),
    (
        "goal_recognition",
        Spec(
            domain="greenhouse",
            blurb="A gardener is seen heading for the greenhouse with an empty watering can.",
            agent=("bo", "Bo"),
            locations=[("greenhouse", "greenhouse")],
            objects=[("can", "watering can")],
            observation=("walks_to", "can"),
            resource=("water", "water supply"),
            primary_goal="water_seedlings",
            other_goals=["harvest_tomatoes", "repot_cuttings", "fetch_twine"],
            affordances=[
                ("tomato_bed", "tomato bed"),
                ("potting_bench", "potting bench"),
                ("twine_box", "twine box"),
            ],
        ),
    ),
    # ---- a second lexicalization of one domain ----------------------------
    (
        "second_order",
        Spec(
            domain="ferry",
            lex="v2",
            blurb="Before the crossing, a deckhand sets out to track down the pilot.",
            agent=("noor", "Noor"),
            other=("wen", "Wen"),
            subject="briefing",
            locations=[
                ("wheelhouse", "bridge"),
                ("galley", "mess"),
                ("cargo_deck", "vehicle deck"),
            ],
            objects=[("briefing", "pre-sailing briefing")],
        ),
    ),
]


def main() -> None:
    total = 0
    for template, spec in DOMAINS:
        written = write(template, spec)
        total += len(written)
        if written:
            print(f"{template:17} {spec.domain}/{spec.lex:3} -> {len(written)} files")
    print(f"\n{total} files written")


if __name__ == "__main__":
    main()
