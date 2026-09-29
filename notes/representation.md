# How a scenario reaches the model

What Jev is shown, where each part comes from, and which of those choices
were measured rather than assumed. The findings themselves are in
`notes/experimental_design.md`; this is the design they constrain.

Jev takes a `state` mapping rather than a prompt string, so a
representation is a dict: keys name the parts of the state, values carry
the content. `ground_truth` and `annotations` are researcher metadata and
are never included. That exclusion lives in `representation.py` rather than
in each experiment, so no caller can leak an answer into the input by
accident.

## The three conditions

    sparse    observations + world_state + goals
    history   + the epistemic-access events the belief follows from
    rich      + the belief itself, stated

They differ in what they say about the agent's mind and in nothing else.
One notation throughout, no preamble anywhere, every other section
identical — which is checked per scenario rather than assumed of the
renderers, because it was not always true and the difference was worth
0.12 of acceptable mass when it was not.

`history` and `rich` are two presentations of the same belief: the history
must ENTAIL what the mental state ASSERTS, without asserting it. That is
guaranteed by construction — `scripts/add_histories.py` derives the events
from the stated beliefs — and checked both ways by the corpus tests.

## Where the belief comes from

Two sources, and they are interchangeable.

**From the file.** `rich(scenario)` renders `scenario.mental_state` as
authored. Every published number was produced this way.

**From the graph.** `world.materialise` derives the beliefs from the
epistemic history: which settlement each agent saw last, which of those a
later event re-settled or excluded, and what a functional predicate implies
about the arguments they never saw. `rerepresent(scenario, beliefs)` then
renders those instead. See *The epistemic history lives in the graph* in
`notes/graph_ontology.md`.

The second is not a convenience. In a two-stage architecture the expensive
step is *constructing* the richer representation, and reading it from a
file costs nothing — which is why the escalation saving stayed notional for
as long as that was the only path. Deriving it makes the construction real
work that something other than Jev performs, which is what Jev being a
System One model amounts to.

The two give the same answers. Measured on both corpora, 200 passes: zero
corrections, zero regressions, acceptable mass unmoved. So the graph path
is a drop-in, and *what `rich` buys is not explicitness* — see the section
of that name.

The derived rendering is not textually identical to the stated one. It
spells out what exclusivity implies, and it names only the agent the
question is about, because the history carries one agent's access by
construction. Both differences were measured separately and neither moves
anything.

## What is settled about surface form

Each of these cost an experiment, and each is a standing constraint rather
than a preference:

**Symbolic, not prose.** Prose does not help at the sparse or history
level and costs 0.08 at the rich level, all of it in nested-belief cells,
with entropy roughly tripling. Render nested attitudes symbolically.

**No preamble.** The one that explained how to read a history was measured
harmful and never helpful. No condition in use carries it.

**One notation throughout.** A history that looked different from its
surroundings scored 0.12 better than one that did not, and none of that
advantage was about epistemic access: 0.06 for standing out, 0.08 for
avoiding the preamble, 0.06 lost to contrast. A mixed rendering measures
its own formatting.

## Why there are twelve renderers and three conditions

`RENDERERS` carries the three conditions, a prose arm of three, and six
more. The six exist so the experiments that established the constraints
above stay reproducible: `history_mixed` is what `history` was before the
formatting was measured, and the rest vary one factor each. They are not
alternatives to choose between. Anything new should be a condition, not a
thirteenth renderer, and should be added only with a measurement that
needs it.

## What is not settled

**Whether any of this matters at the margin.** Explicitness does not, and
neither does the surface form of the belief once the notation is
consistent. Having the belief at all is what moves answers. Nothing has
been found that changes *how much* a belief is worth by changing how it is
written.

**Whether the corpus exercises the representation's edges.** No scenario
distinguishes a predicate that is functional in its location from one that
merely has a location argument, so that part of the derivation is correct
but untested by measurement. `notes/graph_ontology.md` records the same
gap from the graph's side.
