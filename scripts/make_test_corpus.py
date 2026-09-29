"""Build the held-out corpus under scenarios/test/.

Eight sets of four cells, crossing task family with the *function* the
richer representation performs:

    discriminative   the belief points somewhere else. Where it diverges
                     from the world it designates a different answer, so
                     representing it should move mass onto that answer.

    inhibitory       the belief only denies. Where it diverges it removes
                     the reading the world supports without supplying a
                     replacement, so representing it should spread mass
                     rather than move it.

That cross is the point of the set. On the development corpus the two are
entangled with task family, which is why the task-family heuristic is the
strongest escalation policy there and why it cannot be trusted off it. See
*The policy to be tested, fixed in advance* in notes/experimental_design.md.

Every domain is new. The formal vocabulary is the corpus's own — `located`,
`available`, `walks_to`, `obtain`, `meet` — but the relations are not a
rename of the development sets: belief about which way in is open, about
which instrument is serviceable, about whether a road is passable, about
whether a person is on the ward, about what is waiting at a counter.

Histories are NOT written here. Run scripts/add_histories.py afterwards,
which derives them from the stated beliefs and so guarantees entailment by
construction.

    python scripts/make_test_corpus.py
    python scripts/add_histories.py

Refuses to overwrite: a scenario that already exists is left alone, so a
file edited by hand survives a rerun.
"""

from __future__ import annotations

import dataclasses
import pathlib
import textwrap

ROOT = pathlib.Path(__file__).resolve().parents[1] / "scenarios" / "test"

#: A claim: predicate, subject, location (or None), value.
Claim = tuple[str, str, str | None, bool]


@dataclasses.dataclass
class Cell:
    """One cell of a set's four."""

    condition: str
    world: list[Claim]
    beliefs: list[Claim]
    answer: str
    acceptable: list[str] | None
    explanation: str
    supports: bool
    believes: bool
    changes: bool
    note: str = ""


@dataclasses.dataclass
class SetSpec:
    """One matched set of four scenarios."""

    domain: str
    family: str
    function: str
    headline: str
    constant: str
    agents: list[tuple[str, str]]
    locations: list[tuple[str, str]]
    objects: list[tuple[str, str]]
    asker: str
    options: list[str]
    cells: list[Cell]
    goal: dict[str, str] | None = None
    observation: dict[str, str] | None = None
    tags: list[str] = dataclasses.field(default_factory=list)

    @property
    def question_type(self) -> str:
        return "action_prediction" if self.family == "action_prediction" else "goal"


def conflicts(cell: Cell) -> bool:
    """Does any belief contradict a world fact about the same claim?

    The same rule `analysis.world_conflict` applies, computed here so the
    `belief_matches_reality` annotation is derived rather than typed — the
    corpus tests check the two against each other.
    """
    facts = {(p, s, loc): v for p, s, loc, v in cell.world}
    return any(facts.get((p, s, loc)) not in (None, v) for p, s, loc, v in cell.beliefs)


def claim_block(claim: Claim, indent: str) -> str:
    """A proposition, as the corpus writes one."""
    predicate, subject, location, value = claim
    lines = [f"{indent}predicate: {predicate}", f"{indent}subject: {subject}"]
    if location is not None:
        lines.append(f"{indent}location: {location}")
    lines.append(f"{indent}value: {str(value).lower()}")
    return "\n".join(lines)


def wrap(text: str, indent: str) -> str:
    """A description, folded the way the corpus folds them."""
    return textwrap.fill(
        " ".join(text.split()), width=72, initial_indent=indent, subsequent_indent=indent
    )


def render(spec: SetSpec, cell: Cell) -> str:
    """One scenario file, without a history."""
    readable = cell.condition.replace("_", " ")
    out = [
        f"# {spec.domain} — {spec.function} {spec.family.replace('_', ' ')}, {readable}",
        "#",
        wrap(spec.headline, "# ").replace("# ", "# ", 1),
        "#",
        wrap(spec.constant, "# "),
    ]
    if cell.note:
        out += ["#", wrap(cell.note, "# ")]
    out += [
        "",
        f"id: {spec.domain}_{cell.condition}",
        "description: >",
        wrap(cell.explanation, "  "),
        "",
        f"scenario_set: {spec.domain}",
        "",
        "variant:",
        f"  type: {cell.condition}",
        "",
        "entities:",
        "  agents:",
    ]
    for agent, name in spec.agents:
        out += [f"    - id: {agent}", f"      name: {name}"]
    out += ["", "  locations:"]
    for location, name in spec.locations:
        out += [f"    - id: {location}", f"      name: {name}"]
    if spec.objects:
        out += ["", "  objects:"]
        for obj, name in spec.objects:
            out += [f"    - id: {obj}", f"      name: {name}"]

    out.append("")
    if spec.observation:
        out.append("observations:")
        out.append(f"  - type: {spec.observation['type']}")
        out.append(f"    agent: {spec.observation['agent']}")
        out.append(f"    destination: {spec.observation['destination']}")
    else:
        out.append("observations: []")

    out += ["", "world_state:"]
    for claim in cell.world:
        out.append(claim_block(claim, "    ").replace("    predicate", "  - predicate", 1))
        out.append("")
    out.pop()

    if spec.goal:
        out += ["", "goals:", f"  - agent: {spec.goal['agent']}", f"    type: {spec.goal['type']}"]
        for field in ("object", "target_agent", "location"):
            if field in spec.goal:
                out.append(f"    {field}: {spec.goal[field]}")

    out += ["", "mental_state:"]
    for claim in cell.beliefs:
        out += ["  - type: belief", f"    agent: {spec.asker}", "    proposition:"]
        out.append(claim_block(claim, "      "))
        out.append("")
    out.pop()

    out += ["", "question:", f"  type: {spec.question_type}", f"  agent: {spec.asker}", "  options:"]
    out += [f"    - {option}" for option in spec.options]

    out += ["", "ground_truth:", f"  answer: {cell.answer}"]
    if cell.acceptable:
        out.append("  acceptable:")
        out += [f"    - {option}" for option in cell.acceptable]
    out += ["  explanation: >", wrap(cell.explanation, "    ")]

    out += [
        "",
        "annotations:",
        f"  world_supports_action: {str(cell.supports).lower()}",
        f"  agent_believes_action_supported: {str(cell.believes).lower()}",
        f"  belief_matches_reality: {str(not conflicts(cell)).lower()}",
        f"  belief_changes_expected_action: {str(cell.changes).lower()}",
        "  tags:",
    ]
    out += [f"    - {tag}" for tag in [spec.family, spec.function, *spec.tags]]
    return "\n".join(out) + "\n"


def write(spec: SetSpec) -> list[pathlib.Path]:
    """Write a set's four files, skipping any that already exist."""
    written = []
    for cell in spec.cells:
        path = ROOT / spec.family / spec.function / spec.domain / cell.condition / "v1.yaml"
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render(spec, cell))
        written.append(path)
    return written


# ---------------------------------------------------------------------------
# ACTION PREDICTION, DISCRIMINATIVE
# ---------------------------------------------------------------------------
# The belief says which way in works, or which instrument works. Where it
# departs from the world it names a different one, so representing it
# should move mass onto that answer rather than spread it.

GATES = ["north_gate", "south_gate", "canal_gate", "yard_gate"]


def gate_world(open_gate: str) -> list[Claim]:
    """Exactly one gate open, and the consignment always at the dock."""
    return [("available", gate, None, gate == open_gate) for gate in GATES] + [
        ("located", "consignment", "dock", True)
    ]


LOADING_GATE = SetSpec(
    domain="loading_gate",
    family="action_prediction",
    function="discriminative",
    headline=(
        "Rasheed has to bring the consignment in from the dock, and the yard is walled. "
        "What varies is not where the consignment is — that is at the dock in every cell "
        "and he knows it — but which way in he takes."
    ),
    constant=(
        "Exactly one gate is open. Rasheed holds two beliefs in every cell, one about the "
        "north gate and one about the canal gate, so belief count and history length cannot "
        "separate the cells. The target action throughout is entering by the north gate: "
        "world_supports_action says whether that gate is really open, and "
        "agent_believes_action_supported says whether he thinks so."
    ),
    agents=[("rasheed", "Rasheed")],
    locations=[
        ("north_gate", "north gate"),
        ("south_gate", "south gate"),
        ("canal_gate", "canal gate"),
        ("yard_gate", "yard gate"),
        ("dock", "dock"),
    ],
    objects=[("consignment", "consignment")],
    asker="rasheed",
    options=[f"enter_by_{gate}" for gate in GATES],
    goal={"agent": "rasheed", "type": "obtain", "object": "consignment"},
    tags=["access_belief", "rerepresentation_target"],
    cells=[
        Cell(
            condition="true_positive",
            world=gate_world("north_gate"),
            beliefs=[("available", "north_gate", None, True), ("available", "canal_gate", None, False)],
            answer="enter_by_north_gate",
            acceptable=None,
            explanation=(
                "The north gate is open and Rasheed believes it is, so he goes that way. "
                "Belief and world agree and representing the belief changes nothing."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="false_positive",
            world=gate_world("south_gate"),
            beliefs=[("available", "north_gate", None, True), ("available", "canal_gate", None, False)],
            answer="enter_by_north_gate",
            acceptable=None,
            explanation=(
                "Rasheed believes the north gate is open and goes there, though it is the "
                "south gate that is open. The belief names the gate, so representing it "
                "should concentrate on a different answer rather than unsettle the reading."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
        Cell(
            condition="false_negative",
            world=gate_world("north_gate"),
            beliefs=[("available", "north_gate", None, False), ("available", "canal_gate", None, True)],
            answer="enter_by_canal_gate",
            acceptable=None,
            explanation=(
                "The north gate is open, but Rasheed believes it is shut and the canal gate "
                "open, so he goes the long way round. The second belief supplies the "
                "alternative; without it the denial would leave three gates open to him."
            ),
            supports=True,
            believes=False,
            changes=True,
        ),
        Cell(
            condition="true_negative",
            world=gate_world("canal_gate"),
            beliefs=[("available", "north_gate", None, False), ("available", "canal_gate", None, True)],
            answer="enter_by_canal_gate",
            acceptable=None,
            explanation=(
                "The canal gate is the open one and Rasheed believes so. He goes there, "
                "which is also what the world alone would predict."
            ),
            supports=False,
            believes=False,
            changes=False,
        ),
    ],
)

INSTRUMENTS = ["float_gauge", "pressure_sensor", "staff_board", "radar_head"]


def gauge_world(working: str) -> list[Claim]:
    """Exactly one instrument serviceable."""
    return [("available", item, "gauge_hut", item == working) for item in INSTRUMENTS]


TIDE_GAUGE = SetSpec(
    domain="tide_gauge",
    family="action_prediction",
    function="discriminative",
    headline=(
        "Marta has to log the tide before the turn, and the hut holds four instruments. "
        "Nothing is mislaid and nothing is hidden: what varies is which instrument she "
        "takes to be serviceable."
    ),
    constant=(
        "Exactly one instrument works. Marta holds two beliefs in every cell, one about the "
        "float gauge and one about the radar head. The target action throughout is using "
        "the float gauge."
    ),
    agents=[("marta", "Marta")],
    locations=[("gauge_hut", "gauge hut")],
    objects=[
        ("float_gauge", "float gauge"),
        ("pressure_sensor", "pressure sensor"),
        ("staff_board", "staff board"),
        ("radar_head", "radar head"),
        ("reading", "reading"),
    ],
    asker="marta",
    options=[f"use_the_{item}" for item in INSTRUMENTS],
    goal={"agent": "marta", "type": "obtain", "object": "reading"},
    tags=["fitness_belief", "rerepresentation_target"],
    cells=[
        Cell(
            condition="true_positive",
            world=gauge_world("float_gauge"),
            beliefs=[
                ("available", "float_gauge", "gauge_hut", True),
                ("available", "radar_head", "gauge_hut", False),
            ],
            answer="use_the_float_gauge",
            acceptable=None,
            explanation=(
                "The float gauge works and Marta believes it does, so she uses it. Belief "
                "and world agree."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="false_positive",
            world=gauge_world("pressure_sensor"),
            beliefs=[
                ("available", "float_gauge", "gauge_hut", True),
                ("available", "radar_head", "gauge_hut", False),
            ],
            answer="use_the_float_gauge",
            acceptable=None,
            explanation=(
                "Marta believes the float gauge is serviceable and reaches for it, though "
                "it is the pressure sensor that works. The belief names an instrument, so "
                "it designates rather than merely rules out."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
        Cell(
            condition="false_negative",
            world=gauge_world("float_gauge"),
            beliefs=[
                ("available", "float_gauge", "gauge_hut", False),
                ("available", "radar_head", "gauge_hut", True),
            ],
            answer="use_the_radar_head",
            acceptable=None,
            explanation=(
                "The float gauge is in fact working, but Marta believes it is down and the "
                "radar head good, so she uses the radar head."
            ),
            supports=True,
            believes=False,
            changes=True,
        ),
        Cell(
            condition="true_negative",
            world=gauge_world("radar_head"),
            beliefs=[
                ("available", "float_gauge", "gauge_hut", False),
                ("available", "radar_head", "gauge_hut", True),
            ],
            answer="use_the_radar_head",
            acceptable=None,
            explanation=(
                "The radar head is the working instrument and Marta believes so. She uses "
                "it, which is what the world alone would predict."
            ),
            supports=False,
            believes=False,
            changes=False,
        ),
    ],
)


# ---------------------------------------------------------------------------
# ACTION PREDICTION, INHIBITORY
# ---------------------------------------------------------------------------
# The belief only denies. Where it departs from the world it removes the
# obvious action and names no replacement, so representing it should raise
# entropy rather than move mass. These are the cells that can punish a
# policy for escalating: a pass that was confidently right can be talked
# into a spread.

BYPASSES = ["west_bypass", "river_track", "ridge_cut"]


def road_world(haul_open: bool) -> list[Claim]:
    """The bypasses are always passable; only the haul road varies."""
    return [
        ("available", "haul_road", None, haul_open),
        *[("available", road, None, True) for road in BYPASSES],
        ("direct", "haul_road", None, True),
        ("located", "load", "crusher", True),
    ]


QUARRY_ROAD = SetSpec(
    domain="quarry_road",
    family="action_prediction",
    function="inhibitory",
    headline=(
        "Idris has to fetch the load from the crusher. The haul road is the direct way and "
        "three bypasses all reach the same place. What varies is whether he takes the haul "
        "road to be passable."
    ),
    constant=(
        "All three bypasses are passable in every cell and nothing distinguishes them, so a "
        "denial of the haul road licenses all three equally and no answer is determined. "
        "Idris holds exactly one belief in every cell. Where that belief denies, the "
        "acceptable set is the three bypasses and entropy is the measure that carries "
        "information; `outcome` cannot fail."
    ),
    agents=[("idris", "Idris")],
    locations=[
        ("haul_road", "haul road"),
        ("west_bypass", "west bypass"),
        ("river_track", "river track"),
        ("ridge_cut", "ridge cut"),
        ("crusher", "crusher"),
    ],
    objects=[("load", "load")],
    asker="idris",
    options=["take_the_haul_road", *[f"take_the_{road}" for road in BYPASSES]],
    goal={"agent": "idris", "type": "obtain", "object": "load"},
    tags=["access_belief", "denial_only", "ambiguous_by_design"],
    cells=[
        Cell(
            condition="true_positive",
            world=road_world(True),
            beliefs=[("available", "haul_road", None, True)],
            answer="take_the_haul_road",
            acceptable=None,
            explanation=(
                "The haul road is passable and Idris believes it is, so he takes the direct "
                "way. Belief and world agree."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="false_positive",
            world=road_world(False),
            beliefs=[("available", "haul_road", None, True)],
            answer="take_the_haul_road",
            acceptable=None,
            explanation=(
                "The haul road is shut, but Idris believes it open and sets off down it. "
                "Here the belief still determines an answer, because believing a way is "
                "open names that way."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
        Cell(
            condition="false_negative",
            world=road_world(True),
            beliefs=[("available", "haul_road", None, False)],
            answer="take_the_west_bypass",
            acceptable=[f"take_the_{road}" for road in BYPASSES],
            explanation=(
                "The haul road is open, but Idris believes it shut. The belief rules out "
                "the direct way and says nothing about which bypass to use, so all three "
                "are acceptable and none is licensed over the others. What matters is "
                "whether the richer representation registers that by becoming less certain "
                "rather than by picking."
            ),
            supports=True,
            believes=False,
            changes=True,
            note=(
                "The inhibitory cell that can punish escalation: the world alone gives a "
                "confident and reasonable answer, and representing the belief takes it away "
                "without offering a replacement."
            ),
        ),
        Cell(
            condition="true_negative",
            world=road_world(False),
            beliefs=[("available", "haul_road", None, False)],
            answer="take_the_west_bypass",
            acceptable=[f"take_the_{road}" for road in BYPASSES],
            explanation=(
                "The haul road is shut and Idris believes so. He takes a bypass, but "
                "nothing in the world or in what he believes says which, so all three are "
                "acceptable. The world alone already rules out the haul road, so the belief "
                "adds nothing."
            ),
            supports=False,
            believes=False,
            changes=False,
        ),
    ],
)

ELSEWHERE = ["theatre_desk", "mess"]


def ward_world(on_ward: bool) -> list[Claim]:
    """The registrar is on the ward, or else at the theatre desk."""
    return [
        ("located", "registrar", "ward", on_ward),
        ("located", "registrar", "theatre_desk", not on_ward),
        ("located", "registrar", "mess", False),
        ("located", "chart", "ward", True),
    ]


WARD_ROUND = SetSpec(
    domain="ward_round",
    family="action_prediction",
    function="inhibitory",
    headline=(
        "Bijan has to hand the chart to the duty registrar before the round. He can look on "
        "the ward, at the theatre desk or in the mess, or have the registrar paged. What "
        "varies is whether he takes the registrar to be on the ward."
    ),
    constant=(
        "Bijan holds exactly one belief in every cell, and it concerns only the ward. "
        "Denying it leaves three ways of finding the registrar and picks out none of them, "
        "so the acceptable set is those three and entropy is the measure. Unlike the "
        "quarry, the denial here is about where a person is rather than whether a way is "
        "open."
    ),
    agents=[("bijan", "Bijan"), ("registrar", "the duty registrar")],
    locations=[
        ("ward", "ward"),
        ("theatre_desk", "theatre desk"),
        ("mess", "mess"),
    ],
    objects=[("chart", "chart")],
    asker="bijan",
    options=["go_to_the_ward", "go_to_the_theatre_desk", "go_to_the_mess", "page_the_switchboard"],
    goal={"agent": "bijan", "type": "meet", "target_agent": "registrar"},
    tags=["presence_belief", "denial_only", "ambiguous_by_design"],
    cells=[
        Cell(
            condition="true_positive",
            world=ward_world(True),
            beliefs=[("located", "registrar", "ward", True)],
            answer="go_to_the_ward",
            acceptable=None,
            explanation=(
                "The registrar is on the ward and Bijan believes so, so he goes there. "
                "Belief and world agree."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="false_positive",
            world=ward_world(False),
            beliefs=[("located", "registrar", "ward", True)],
            answer="go_to_the_ward",
            acceptable=None,
            explanation=(
                "The registrar is at the theatre desk, but Bijan believes the ward and goes "
                "there. Believing someone is somewhere names a place, so this cell has a "
                "determinate answer even though the set is otherwise inhibitory."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
        Cell(
            condition="false_negative",
            world=ward_world(True),
            beliefs=[("located", "registrar", "ward", False)],
            answer="go_to_the_theatre_desk",
            acceptable=["go_to_the_theatre_desk", "go_to_the_mess", "page_the_switchboard"],
            explanation=(
                "The registrar is on the ward, but Bijan believes they are not. The belief "
                "removes the one place the world supports and names nowhere else, so the "
                "three remaining courses are equally acceptable."
            ),
            supports=True,
            believes=False,
            changes=True,
            note=(
                "The second cell that can punish escalation: the world says the ward, and "
                "representing the belief replaces a right answer with a spread."
            ),
        ),
        Cell(
            condition="true_negative",
            world=ward_world(False),
            beliefs=[("located", "registrar", "ward", False)],
            answer="go_to_the_theatre_desk",
            acceptable=["go_to_the_theatre_desk", "go_to_the_mess", "page_the_switchboard"],
            explanation=(
                "The registrar is not on the ward and Bijan believes so. He has no belief "
                "about where they are instead, so the three remaining courses are equally "
                "acceptable. The world alone would say the theatre desk; Bijan cannot, "
                "because he only knows where the registrar is not."
            ),
            supports=False,
            believes=False,
            changes=True,
            note=(
                "A true belief that still costs certainty. The world pins the registrar "
                "down and Bijan's beliefs do not, so representing what he knows turns a "
                "determinate reading into a spread. The quarry has no cell like this, "
                "because a shut road leaves the bypasses undetermined for the world too."
            ),
        ),
    ],
)


# ---------------------------------------------------------------------------
# GOAL RECOGNITION, DISCRIMINATIVE
# ---------------------------------------------------------------------------
# The walk is constant; the belief says which of two things is waiting at
# the destination, and so which goal the walk serves. In every cell exactly
# one thing is believed to be there, so the belief always designates.


def counter_world(handset_at_counter: bool, parcel_at_counter: bool) -> list[Claim]:
    return [
        ("located", "handset", "returns_counter", handset_at_counter),
        ("located", "handset", "storeroom", not handset_at_counter),
        ("located", "parcel", "returns_counter", parcel_at_counter),
        ("located", "parcel", "storeroom", not parcel_at_counter),
        ("located", "repair_slip", "returns_counter", False),
        ("located", "repair_slip", "storeroom", True),
        ("located", "replacement_unit", "returns_counter", False),
        ("located", "replacement_unit", "storeroom", True),
    ]


def counter_beliefs(handset: bool) -> list[Claim]:
    return [
        ("located", "handset", "returns_counter", handset),
        ("located", "parcel", "returns_counter", not handset),
    ]


RETURNS_DESK = SetSpec(
    domain="returns_desk",
    family="goal_recognition",
    function="discriminative",
    headline=(
        "Nadia is seen walking to the returns counter. She may be there to hand back the "
        "faulty handset or to collect the parcel being held for her."
    ),
    constant=(
        "The walk is the same in every cell. Nadia holds two beliefs throughout, one about "
        "each item, and believes exactly one of them to be at the counter — so the belief "
        "always names a goal rather than merely ruling one out. What varies is which item "
        "she believes is there and whether she is right. The repair slip and the "
        "replacement unit are in the storeroom in every cell and she believes nothing "
        "about them; they are there so that a uniform guess scores what it scores in the "
        "action-prediction sets rather than twice as much."
    ),
    agents=[("nadia", "Nadia")],
    locations=[("returns_counter", "returns counter"), ("storeroom", "storeroom")],
    objects=[
        ("handset", "handset"),
        ("parcel", "parcel"),
        ("repair_slip", "repair slip"),
        ("replacement_unit", "replacement unit"),
    ],
    asker="nadia",
    options=[
        "hand_back_the_handset",
        "collect_the_parcel",
        "collect_the_repair_slip",
        "swap_the_replacement_unit",
    ],
    observation={"type": "walks_to", "agent": "nadia", "destination": "returns_counter"},
    tags=["presence_belief", "designates_a_goal"],
    cells=[
        Cell(
            condition="handset_true",
            world=counter_world(True, False),
            beliefs=counter_beliefs(True),
            answer="hand_back_the_handset",
            acceptable=None,
            explanation=(
                "Nadia believes the handset is at the counter and the parcel in the "
                "storeroom, and she is right on both. The walk is to hand the handset back."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="handset_false",
            world=counter_world(False, False),
            beliefs=counter_beliefs(True),
            answer="hand_back_the_handset",
            acceptable=None,
            explanation=(
                "Nadia believes the handset is at the counter, though both items are in "
                "fact in the storeroom. She is walking there to hand the handset back; the "
                "belief names the goal the world does not support."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
        Cell(
            condition="parcel_true",
            world=counter_world(False, True),
            beliefs=counter_beliefs(False),
            answer="collect_the_parcel",
            acceptable=None,
            explanation=(
                "Nadia believes the parcel is at the counter and the handset in the "
                "storeroom, and she is right on both. The walk is to collect the parcel."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="parcel_false",
            world=counter_world(False, False),
            beliefs=counter_beliefs(False),
            answer="collect_the_parcel",
            acceptable=None,
            explanation=(
                "Nadia believes the parcel is at the counter, though both items are in fact "
                "in the storeroom. She is walking there to collect it."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
    ],
)


def slipway_world(oars: bool, book: bool) -> list[Claim]:
    return [
        ("available", "oars", "slipway", oars),
        ("available", "launch_book", "slipway", book),
        ("available", "bailer", "slipway", False),
        ("available", "tide_board", "slipway", False),
    ]


def slipway_beliefs(oars: bool) -> list[Claim]:
    return [
        ("available", "oars", "slipway", oars),
        ("available", "launch_book", "slipway", not oars),
    ]


SLIPWAY = SetSpec(
    domain="slipway",
    family="goal_recognition",
    function="discriminative",
    headline=(
        "Tomas is seen walking down to the slipway. He may be going for the oars, or to "
        "sign the launch book before taking a boat out."
    ),
    constant=(
        "The walk is the same in every cell, and Tomas believes exactly one of the two "
        "things to be out at the slipway rather than locked away. The relation is whether "
        "a thing is there to be used, not where it is kept, which is what distinguishes "
        "this set from the returns desk. The bailer and the tide board are never out and "
        "Tomas believes nothing about them; they are there to hold the option count at "
        "four, as in every other set."
    ),
    agents=[("tomas", "Tomas")],
    locations=[("slipway", "slipway")],
    objects=[
        ("oars", "oars"),
        ("launch_book", "launch book"),
        ("bailer", "bailer"),
        ("tide_board", "tide board"),
    ],
    asker="tomas",
    options=[
        "collect_the_oars",
        "sign_the_launch_book",
        "fetch_the_bailer",
        "check_the_tide_board",
    ],
    observation={"type": "walks_to", "agent": "tomas", "destination": "slipway"},
    tags=["fitness_belief", "designates_a_goal"],
    cells=[
        Cell(
            condition="oars_true",
            world=slipway_world(True, False),
            beliefs=slipway_beliefs(True),
            answer="collect_the_oars",
            acceptable=None,
            explanation=(
                "Tomas believes the oars are out at the slipway and the launch book is not, "
                "and he is right. The walk is for the oars."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="oars_false",
            world=slipway_world(False, False),
            beliefs=slipway_beliefs(True),
            answer="collect_the_oars",
            acceptable=None,
            explanation=(
                "Tomas believes the oars are out at the slipway, though neither the oars "
                "nor the book are. He is going for the oars all the same."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
        Cell(
            condition="book_true",
            world=slipway_world(False, True),
            beliefs=slipway_beliefs(False),
            answer="sign_the_launch_book",
            acceptable=None,
            explanation=(
                "Tomas believes the launch book is out at the slipway and the oars are not, "
                "and he is right. The walk is to sign the book."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="book_false",
            world=slipway_world(False, False),
            beliefs=slipway_beliefs(False),
            answer="sign_the_launch_book",
            acceptable=None,
            explanation=(
                "Tomas believes the launch book is out at the slipway, though neither it "
                "nor the oars are. He is going to sign it all the same."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
    ],
)


# ---------------------------------------------------------------------------
# GOAL RECOGNITION, INHIBITORY
# ---------------------------------------------------------------------------
# The same 2x2 as the inhibitory action-prediction sets, so that task
# family is not confounded with how much a uniform guess scores: four
# options throughout, one belief per cell, and an acceptable set of one
# where the belief affirms and three where it denies.
#
# An earlier version varied how many of three errands the agent denied.
# It read better and measured worse: the nested denials left one errand
# acceptable in all four cells, so a constant answer scored perfectly, and
# three options against the action sets' four put the chance floor at 0.75
# against 0.50. Narrowing-by-elimination is worth a set of its own one
# day; it is not worth confounding the comparison this corpus exists for.

ARCHIVE_ELSE = ["meet_the_archivist", "return_the_plates", "collect_the_transfer_list"]


def archive_world(ledger_there: bool) -> list[Claim]:
    """The ledger is in the reading room, or else the archivist is.

    The world always licenses some errand, so a reading that fails is the
    belief's doing rather than an empty room's.
    """
    return [
        ("located", "ledger", "reading_room", ledger_there),
        ("located", "ledger", "stack", not ledger_there),
        ("located", "archivist", "reading_room", not ledger_there),
        ("located", "archivist", "stack", ledger_there),
        ("located", "plates", "reading_room", False),
        ("located", "plates", "stack", True),
        ("located", "transfer_list", "reading_room", False),
        ("located", "transfer_list", "stack", True),
    ]


ARCHIVE_DESK = SetSpec(
    domain="archive_desk",
    family="goal_recognition",
    function="inhibitory",
    headline=(
        "Perrin is seen walking into the reading room. He may be after the ledger, or the "
        "archivist, or returning the plates, or collecting the transfer list."
    ),
    constant=(
        "Perrin holds exactly one belief in every cell, about the ledger. Affirming it "
        "names an errand; denying it removes one and names no other, leaving three that "
        "nothing he believes chooses between. He never learns where anything else is, so a "
        "denial costs the reading whatever the world happens to know."
    ),
    agents=[("perrin", "Perrin"), ("archivist", "the archivist")],
    locations=[("reading_room", "reading room"), ("stack", "stack")],
    objects=[("ledger", "ledger"), ("plates", "plates"), ("transfer_list", "transfer list")],
    asker="perrin",
    options=["fetch_the_ledger", *ARCHIVE_ELSE],
    observation={"type": "walks_to", "agent": "perrin", "destination": "reading_room"},
    tags=["presence_belief", "denial_only", "ambiguous_by_design"],
    cells=[
        Cell(
            condition="true_positive",
            world=archive_world(True),
            beliefs=[("located", "ledger", "reading_room", True)],
            answer="fetch_the_ledger",
            acceptable=None,
            explanation=(
                "The ledger is in the reading room and Perrin believes it is, so the walk "
                "is for the ledger. Belief and world agree."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="false_positive",
            world=archive_world(False),
            beliefs=[("located", "ledger", "reading_room", True)],
            answer="fetch_the_ledger",
            acceptable=None,
            explanation=(
                "The ledger is in the stack and the archivist is in the reading room, but "
                "Perrin believes the ledger is there and is walking in for it. Believing a "
                "thing is somewhere names an errand, so this cell has a determinate answer "
                "even though the set is otherwise inhibitory."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
        Cell(
            condition="false_negative",
            world=archive_world(True),
            beliefs=[("located", "ledger", "reading_room", False)],
            answer="meet_the_archivist",
            acceptable=ARCHIVE_ELSE,
            explanation=(
                "The ledger is in the reading room, but Perrin believes it is not. That "
                "removes the errand the world supports and names no other, so the "
                "remaining three are equally acceptable."
            ),
            supports=True,
            believes=False,
            changes=True,
            note=(
                "The cell that can punish escalation: the world gives a confident and "
                "correct reading, and representing the belief takes it away without "
                "offering a replacement."
            ),
        ),
        Cell(
            condition="true_negative",
            world=archive_world(False),
            beliefs=[("located", "ledger", "reading_room", False)],
            answer="meet_the_archivist",
            acceptable=ARCHIVE_ELSE,
            explanation=(
                "The ledger really is in the stack and Perrin believes so. The world would "
                "say the archivist, who is in the reading room; Perrin cannot, because he "
                "only knows where the ledger is not, so the remaining three stay equally "
                "acceptable."
            ),
            supports=False,
            believes=False,
            changes=True,
            note=(
                "A true belief that still costs certainty, as in the ward round. What the "
                "agent knows is a strict subset of what the world does, and representing "
                "the smaller thing turns a determinate reading into a spread."
            ),
        ),
    ],
)

PLANT_ELSE = ["meet_the_duty_fitter", "collect_the_spares", "sign_the_permit"]


def plant_world(meter_ready: bool) -> list[Claim]:
    """The meter is readable, or else the duty fitter is there instead."""
    return [
        ("available", "meter", "pump_bay", meter_ready),
        ("available", "fitter", "pump_bay", not meter_ready),
        ("available", "spares", "pump_bay", False),
        ("available", "permit", "pump_bay", False),
    ]


PLANT_ROOM = SetSpec(
    domain="plant_room",
    family="goal_recognition",
    function="inhibitory",
    headline=(
        "Halima is seen walking through to the pump bay. She may be there to log the "
        "meter, to catch the duty fitter, to collect spares, or to sign the permit."
    ),
    constant=(
        "Halima holds exactly one belief in every cell, about the meter. The relation is "
        "whether a thing is to hand rather than where it is, which is what distinguishes "
        "this set from the archive. Denying the meter leaves three errands and picks out "
        "none of them."
    ),
    agents=[("halima", "Halima"), ("fitter", "the duty fitter")],
    locations=[("pump_bay", "pump bay")],
    objects=[("meter", "meter"), ("spares", "spares"), ("permit", "permit")],
    asker="halima",
    options=["log_the_meter", *PLANT_ELSE],
    observation={"type": "walks_to", "agent": "halima", "destination": "pump_bay"},
    tags=["fitness_belief", "denial_only", "ambiguous_by_design"],
    cells=[
        Cell(
            condition="true_positive",
            world=plant_world(True),
            beliefs=[("available", "meter", "pump_bay", True)],
            answer="log_the_meter",
            acceptable=None,
            explanation=(
                "The meter is readable and Halima believes it is, so the walk is to log "
                "it. Belief and world agree."
            ),
            supports=True,
            believes=True,
            changes=False,
        ),
        Cell(
            condition="false_positive",
            world=plant_world(False),
            beliefs=[("available", "meter", "pump_bay", True)],
            answer="log_the_meter",
            acceptable=None,
            explanation=(
                "The meter is down and the duty fitter is on the bay instead, but Halima "
                "believes the meter is readable and is walking through to log it."
            ),
            supports=False,
            believes=True,
            changes=True,
        ),
        Cell(
            condition="false_negative",
            world=plant_world(True),
            beliefs=[("available", "meter", "pump_bay", False)],
            answer="meet_the_duty_fitter",
            acceptable=PLANT_ELSE,
            explanation=(
                "The meter is readable, but Halima believes it is down. That removes the "
                "errand the world supports and names no other, so the remaining three are "
                "equally acceptable."
            ),
            supports=True,
            believes=False,
            changes=True,
            note=(
                "The second goal-recognition cell that can punish escalation, and the one "
                "where the denial is about fitness rather than presence."
            ),
        ),
        Cell(
            condition="true_negative",
            world=plant_world(False),
            beliefs=[("available", "meter", "pump_bay", False)],
            answer="meet_the_duty_fitter",
            acceptable=PLANT_ELSE,
            explanation=(
                "The meter really is down and Halima believes so. The world would say the "
                "duty fitter, who is on the bay; Halima only knows the meter is no use, so "
                "the remaining three stay equally acceptable."
            ),
            supports=False,
            believes=False,
            changes=True,
        ),
    ],
)

SETS = [
    LOADING_GATE,
    TIDE_GAUGE,
    QUARRY_ROAD,
    WARD_ROUND,
    RETURNS_DESK,
    SLIPWAY,
    ARCHIVE_DESK,
    PLANT_ROOM,
]


def main() -> None:
    written = [path for spec in SETS for path in write(spec)]
    for path in written:
        print(path.relative_to(ROOT.parents[1]))
    skipped = 4 * len(SETS) - len(written)
    print(f"\n{len(written)} written, {skipped} already present")
    print("now run: python scripts/add_histories.py")


if __name__ == "__main__":
    main()
