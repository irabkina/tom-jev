# Experimental design

## Findings so far

Stated as they currently stand, newest understanding first. Each links to the
section that establishes it; where a later section refines an earlier one, the
later wording is the one to use.

**The mixed history's apparent advantage is entirely formatting.** Its
0.12 over the consistent arms decomposes into 0.08 from avoiding a
preamble that only hurts narrated events, 0.06 from the history standing
out against symbolic surroundings, and -0.02 from event wording. None of
it is about epistemic access, and the preamble — added to stop superseded
events reading as contradictions — never helps anywhere. See *Where the
mixed rendering's advantage comes from*.

**Writing the history in prose rather than symbols is worth almost
nothing once the whole state is written the same way, and prose actively
harms nested beliefs.** Measured over a 2x3 of style by richness: +0.03
acceptable mass at the history level, 0.00 at sparse, and **-0.08** at
rich, with the whole loss in the four nested-belief cells at -0.25 to
-0.29 and entropy roughly tripling. So the earlier prose advantage does
not survive making the registers consistent. See *Surface form: prose
does not help, and hurts nested attitudes*, which supersedes
*Unresolved: the history's surface form moves the result*.

**An epistemic-access history closes about a sixth of the sparse-rich
gap, and explicit statement closes the rest.** 0.51 -> 0.58 of a
0.51 -> 0.87 span over 68 scenarios, under a middle condition written in
one notation throughout. It closes a quarter of the gap on the attribution
and discriminative templates and under a tenth on first- and second-order
action prediction: evidence about access helps where the question is
social. An earlier figure of 0.63 came from a rendering carrying two
formatting advantages. The direction is robust across renderings; the
fraction is not, and should be quoted only with the rendering named. See
*Evidence for a belief is worth less than the belief*.

**For goal recognition, explicit mental-state re-representation strongly
changes inference when it supplies a competing explanation, but has much
weaker effects when it merely undermines the sparse explanation without
supporting an alternative.** Across four domains, influence is 0.65–0.71
where the belief licenses a different answer and 0.17–0.19 where it only
removes the sparse one. See *Re-representation needs an alternative, not just a problem* and its
*Replication across four domains*.

**Detecting a conflict is not the same as resolving it.** Where the belief
undermines the sparse reading without supplying an alternative, entropy rises
more than in any other cell and the model still answers the goal its own
belief rules out. Conflict detection may suffice to *trigger*
re-representation; succeeding needs the richer representation to contain
enough to construct the alternative. See *Consequence for the two-systems
framing*.

**Belief moves action prediction substantially** — 0.45–0.69 mean influence
across every action-prediction template, 28 corrections and no regressions
in 68 scenarios. See *Belief moves action prediction, not goal recognition*,
whose title states the goal-recognition half too strongly; the first finding
above is the corrected form.

**Nothing available to the sparse pass predicts whether re-representation
will help.** Not its confidence, not a conflict with the world, not its own
answer being ruled out, and not the dependency structure of its derivation.
Output properties fail because the sparse pass is reasoning correctly over
what it was given; structural properties fail because a dependence on some
agent's representation is constitutive of predicting an agent at all. Close
to a consequence of the design rather than a discovery, since the
manipulation is precisely the withholding of the deciding information. See
*Sparse-state signals do not reliably identify the need for
re-representation* and *Dependency structure does not give a usable
escalation signal either*.

**Prefer symmetric competing alternatives (A vs. B) to an action and its
negation.** See *Symmetric action alternatives*.

**Scenarios revised in response to their own measurements are not
independent evidence.** See *Not tuning stimuli to results*, which records
which parts of the corpus are and are not.

## Symmetric action alternatives

Early pilot scenarios framed action prediction as a binary choice between an affirmative action and its negation (e.g., `go_to_office` vs. `do_not_go_to_office`). This design produced a strong affirmative-action bias: Jev assigned very high probability to the goal-consistent affirmative action across world states. As a result, adding an explicit positive belief often had almost no effect, while explicit negative beliefs sometimes substantially reduced the probability of the affirmative action.

This asymmetry obscured the intended manipulation. In particular, scenarios annotated as requiring explicit belief representation did not reliably show greater representational influence than control scenarios.

Replacing **A vs. not-A** choices with **symmetric competing actions (A vs. B)** resolved the issue. For the report-location task, Jev chooses between two plausible destinations (e.g., `go_to_office` vs. `go_to_conference_room`). Objective world state favors one destination, while the agent's represented belief may favor the same or the alternative destination.

Under this design:

* When belief and reality agree, Sparse and Rich representations produce nearly identical distributions (TV influence 0.00–0.04).
* When belief and reality conflict, adding the explicit belief produces large distributional shifts (TV influence 0.84–0.96).
* In both conflict directions, the Rich representation corrects the Sparse prediction.
* The earlier positive-vs.-negative belief asymmetry disappears.

### Design implication

For experiments testing the effect of re-representation on Jev decisions, prefer **symmetric competing alternatives (A vs. B)** over **an action and its negation (A vs. not-A)**.

A vs. not-A can introduce a strong default toward the concrete, goal-consistent affirmative action, making representational effects difficult to interpret. A vs. B provides competing positive actions and allows belief information to shift probability mass between comparably structured alternatives.

The original A vs. not-A results should be retained as a methodological pilot rather than treated as evidence against the re-representation hypothesis.

## Not tuning stimuli to results

`coffee_false_negative` was the first failing cell found: annotated as
requiring belief, it measures influence 0.03 where its group averages 0.66,
and the rich pass still answers `get_coffee` despite Sam believing there is
none. It is left as it is, deliberately. It has since turned out to be one
of a family — see the goal-recognition result below — rather than a broken
item.

Revising a scenario until it produces the expected measurement is fitting the
stimulus to the hypothesis. The measurement stops being evidence at that
point — a corpus tuned until every cell behaves is guaranteed to behave, and
says nothing.

This matters beyond that one cell, because parts of the corpus were revised in
response to measurements:

| set | history | independent? |
|---|---|---|
| `coffee` | rebuilt three times after seeing results: A vs. not-A, then two destinations, then goal recognition with three goals and affordances | no |
| `report` | options changed from A vs. not-A to two destinations after observing the affirmative bias | no |
| `meeting` | written once, worked first run | **yes** |
| `attribution` | written once, worked first run | **yes** |

The corpus-level separation — influence 0.80 where belief is annotated
relevant against 0.03 where it is not — is therefore not all independent
evidence. `meeting` and `attribution` are, having never been revised against
their own results. `coffee` and `report` should be read as the pilot that
established the A vs. B design rule, not as confirmation of the hypothesis
they were reshaped under.

The distinction worth preserving in future work: changing a scenario because
its *construction* is wrong — a missing precondition, an option with no
affordance, an incoherent ground truth — is fixing a bug. Changing it because
the *result* is wrong is overfitting. The first is legitimate at any time; the
second invalidates the item as evidence.

## Belief moves action prediction, not goal recognition

> Refined below. The goal-recognition half of this title is too strong: what
> matters is whether the belief supplies a competing explanation, not the task
> family. See *Re-representation needs an alternative, not just a problem*.

Measured over 52 scenarios in four templates, the effect of adding an
agent's belief depends almost entirely on what Jev is asked:

| task family | template | n | mean TV influence | corrections |
|---|---|---|---|---|
| action prediction | attribution | 12 | 0.69 | 9 |
| action prediction | first order | 12 | 0.47 | 6 |
| action prediction | second order | 16 | 0.45 | 8 |
| goal recognition | discriminative | 16 | 0.43 | 4 |
| **goal recognition** | first order | 12 | **0.07** | **1** |

These figures survived a round trip worth noting. Attribution was briefly
0.48 after the scenarios were given a `located(<other agent>, …)` fact so
the conflict rule could apply to them; removing that fact restored 0.69
exactly. The fact was derived from the agent's own belief using the very
principle under test, and it reached the model through the sparse
representation. See *Where the line falls* in graph_ontology.md.

All five failing cells in the corpus are goal recognition. This is not one
bad item: it replicates across `coffee`, `darkroom` and `greenhouse`, three
domains with no shared vocabulary, two of them generated and run once with
no revision.

The mechanism is visible in the distributions. In `darkroom` and
`greenhouse`, P(primary goal) sits at 0.97–1.00 in *every* pass, sparse and
rich alike. Being seen walking to the darkroom carrying exposed film fixes
the goal inference, and neither the objective world state nor the agent's
explicit belief dislodges it. `coffee` is the only goal-recognition domain
where anything moves at all, which is why it looked like an outlier before
the other two existed.

Read alongside the action-prediction results, where the same manipulation
moves 0.45–0.69 and produces 28 corrections with no regressions, the
contrast is the finding rather than a defect:

**An observed action appears to determine goal inference strongly enough
that belief information does not change it. The same belief information
substantially changes predictions of what an agent will do next.**

This reframes `coffee_false_negative`, previously recorded as an open
problem: it is the first observed instance of a systematic effect, not a
broken stimulus. It stays unmodified.

### What would test it

The observation and the belief are confounded in the current design: every
goal-recognition item states an observation that already implies the
primary goal. Two follow-ups would separate them — an item whose observed
action is compatible with several goals equally, and one where belief and
observation point at *different* goals rather than belief merely
subtracting one. Neither exists yet.

### A caution

`influence` and `|utility|` are identical to three decimals at every option
count, including five. Probability never moved between two incorrect
options anywhere in the corpus: answers either move to the correct one or
do not move. The two measures were meant to separate at three or more
options. They have not, and until they do, TV distance is carrying no
information that the signed change does not.

## Re-representation needs an alternative, not just a problem

The goal-recognition result above — belief barely moves goal inference —
turns out to be too coarse. The `mailroom` 2x2 holds the world and the
observation fixed across all four cells and varies only what Sam believes,
so sparse is *identical* in every cell and all variation is attributable to
belief. It separates two things the earlier sets confounded.

| what the belief does | cells | influence |
|---|---|---|
| licenses a *different* answer | `mailroom` false_false, false_true | 0.47, 0.60 |
| only removes the sparse answer | `mailroom` true_false | 0.18 |
| only subtracts the primary goal | `coffee`, `darkroom`, `greenhouse` | 0.07 |

In `false_false` the belief says the package is at the front desk — a
positive claim that supports a competing reading of the walk, and the model
moves to it (correction, P 0.36 -> 0.83). In `true_false` the belief says
neither the package nor Alex is at the front desk. That *undermines* the
sparse reading without supplying anything in its place, and the model did
not merely fail to switch: entropy fell from 0.94 to 0.68 and it answered
`meet_alex` more confidently — the very reading the belief rules out. The
subtractive goal-recognition domains behave the same way, at 0.07 — near
enough nothing across twelve scenarios and three unrelated domains.

**Re-representation is most effective when the richer representation
supports a competing inference, rather than merely revealing a problem with
the sparse inference.**

### Consequence for the two-systems framing

This bears directly on the motivating idea, and sharpens it. Detecting that
the System 1 answer conflicts with something may well be enough to *trigger*
re-representation — the conflict is locally detectable, and the sparse
answer does not need an alternative in hand to be recognised as suspect.

But triggering is not succeeding. Re-representation only pays when the
richer representation contains enough to construct and support an
alternative. A representation that is rich enough to expose the problem can
still be too poor to solve it, and `true_false` is that case: the belief is
present, it is used well enough to contradict the sparse reading, and the
model still has nowhere to go.

So the effortful second pass has two distinct failure modes, and they want
separating in any policy:

- **not triggered** — the conflict was never detected, and the sparse
  answer stands unexamined
- **triggered but unresolved** — the conflict was detected and the richer
  representation had no alternative to offer

A re-representation policy that decides *when to escalate* is addressing
only the first. The second is a question about what the richer
representation must contain, which is a design question about the
representation rather than about the policy.

### Caveat: the control cell is not inert

`mailroom` true_true has belief and world agreeing, so re-representation
should change nothing. It measured influence 0.27, with entropy falling
0.94 -> 0.44. The belief acted as confirmation, not just redirection. Some
part of the influence in every cell is therefore this effect rather than
the manipulation, and the control gives a rough floor to subtract — around
0.27 on this domain. Reported influences should be read against it, not
against zero.

### Replication across four domains

`clinic`, `station` and `workshop` were generated from the same template and
each written once and run once, with no revision. They reproduce the
`mailroom` pattern exactly.

| cell | belief does | mean influence (n=3) | mean entropy change |
|---|---|---|---|
| true_true | confirms the sparse reading | 0.15 | +0.27 |
| true_false | removes it, offers nothing | 0.20 | +0.37 |
| false_true | adds a competing reading | **0.76** | −0.09 |
| false_false | replaces it outright | **0.72** | +0.02 |

The split is the same in every domain: where the belief puts something at
the observed destination, influence is 0.65–0.76; where it does not, 0.12–
0.34. Nothing about a particular story is carrying the effect.

The new domains sharpen the claim in a way `mailroom` alone did not.
`true_false` — belief undermines the sparse reading and supplies nothing —
has the **largest entropy rise of any cell** (+0.37), and in all three
domains the model still answered the goal its own belief rules out. So the
conflict *is* detected: the model becomes visibly less certain. It simply
has nowhere to go.

That is close to a direct measurement of the distinction above. Detection is
cheap and happens on its own. Constructing the alternative is the part that
requires the richer representation to actually contain one, and entropy
without a correction is what "triggered but unresolved" looks like in the
data.

`mailroom` is the exception worth noting: its `true_false` entropy *fell*,
which read as the belief being ignored. Across four domains that is a
minority behaviour, and the replication is the better guide.

### Caveats on these numbers

`true_true` is not inert in any domain — 0.15 mean, up to 0.29 on
`workshop`, with entropy rising +0.27. A belief that merely agrees with the
world still perturbs the distribution, so the floor to read influence
against is roughly 0.15 here, not zero.

Three domains per cell, one run each. The direction is consistent across
every domain; the magnitudes are not stable enough to quote to two figures.

## Sparse-state signals do not reliably identify the need for re-representation

Across the current corpus, cases in which re-representation substantially
improves inference are not reliably identifiable from the sparse inference
alone. In particular, sparse confidence and entropy do not provide a
sufficient escalation signal: the sparse system is often highly confident in
an inference that is reasonable given the information represented, even when
adding mental-state information subsequently produces a large correction.
Objective-world conflict is also insufficient, because useful
re-representation occurs in second-order and attribution cases where the
relevant mental-state proposition does not contradict the objective world.

These failures reflect representational incompleteness rather than
necessarily defective inference over the sparse representation. In many
cases, the information that makes the rich inference preferable is precisely
the information omitted from the sparse representation. Consequently, the
sparse inference need not contain an internal indication that its conclusion
would change under re-representation.

This provides a negative result for simple self-monitoring accounts of
escalation: uncertainty and detected world conflict are not sufficient
triggers for re-representation on this corpus. A successful escalation
mechanism therefore requires either additional information outside the
sparse inference itself or a policy that sometimes constructs richer
representations in the absence of an internally detectable error.

### What was measured

Three candidate triggers, each computable from the sparse representation
without any belief, against whether the rich pass actually produced a
correction. 68 scenarios, 28 corrections.

**Sparse uncertainty.** Mean sparse entropy is 0.40 where a correction
follows and 0.34 where none does — a difference far too small to threshold
on, and in any case the two ranges overlap almost entirely. Thresholding
does not help: 12 of 25 scenarios above 0.5 bits are corrections, against
16 of 43 below it. More pointedly, 11 of the 28 corrections have sparse
entropy below 0.2 — near-certainty on two or three options — and those
carry a mean influence of 0.94. The sparse pass is at
its most confident precisely where belief is about to overturn it.

**Objective-world conflict.** 11 of the 17 second-order and attribution
corrections have no world conflict at all, at mean influence 0.85. Three of
those do have an *attribution* conflict — the believer is wrong about a
person rather than about the world — and the rest are uncheckable because
the other agent's belief is not represented. So the mental state doing the
work contradicts nobody's facts.

**The model's own answer contradicting what is known.** Take the sparse
answer and ask whether background knowledge and the episodic world rule it
out. It fires four times, with precision 0.00 and recall 0.00. Where it
fires — darkroom and greenhouse, false_positive and true_negative — the rich
pass gives the same answer, so escalating buys nothing. And it cannot fire
where it would matter: an action-prediction answer is derived from the
world, so it does not contradict it.

The one quantity that does separate cleanly is acceptable mass on the sparse
pass — 0.06 where a correction follows against 0.83 where none does. That is
not a trigger but a restatement of the target: it is computed from ground
truth, and predicting it is the whole problem.

## Dependency structure does not give a usable escalation signal either

An earlier version of this section claimed it did. That was wrong, and the
way it was wrong is worth keeping.

The idea was sound: rather than asking whether the sparse output looks
wrong, ask what it *rests on*, and whether any of those supports is the
kind of thing only a mind settles.

    1. sparse inference          "Sam will go to the office."
    2. dependency analysis       this rests on where Alex will be
    3. epistemic relevance       but Alex's position is settled by Alex's
                                 representation, not by the world
    4. construct                 query what Sam thinks Alex thinks
    5. rerun

Steps 2 and 3 are computable without any belief — `world.dependencies`
reads a goal's requirements from background knowledge and resolves them
against the cast. The problem is what they compute.

### Mind-dependence is constitutive, not discriminative

The first implementation counted only *other* agents' minds, excluding the
acting agent's own. That produced a signal firing on 44 of 68 with precision
0.48 and recall 0.75, which looked usable.

It was an artifact of the exclusion. Sam going where Sam *believes* the
report is depends on Sam's mind exactly as much as Sam going where Sam
believes *Alex believes* the meeting is. The actor's own representation was
dropped because counting it fires everywhere — selectivity manufactured by
deforming the concept. It also cost the seven largest effects in the corpus,
all first-order cells at influence 0.81–0.97.

Counted honestly, every prediction about an agent has a mind in its
dependency chain. The structural signal says *escalate always*: precision
0.41, recall 1.00. That is not a defect in the detector. Depending on an
agent's representation is constitutive of predicting an agent at all, so
nothing structural can distinguish the cases.

### The graded version measures the corpus, not the phenomenon

Depth of nesting does vary — the actor alone, or the actor plus another
agent whose own mind settles a requirement — and it appeared to rank
benefit: base rate 0.48 at depth 2 against 0.29 at depth 1, mean influence
0.51 against 0.28.

It does not. Sparse performs identically at both depths, and rich is
*better* on the deeper one:

| depth | sparse acc. mass | rich acc. mass | rich correct |
|---|---|---|---|
| 1 (actor alone) | 0.50 | 0.77 | 19/24 |
| 2 (actor + another mind) | 0.52 | **0.93** | **44/44** |

Jev solves every second-order case once given the belief, and fails five
first-order ones. So second-order is not harder here in any sense, and the
depth gradient was composition: the depth-2 sets are balanced 2x2s where
half the cells have belief diverging, while depth-1 includes the twelve
subtractive goal-recognition scenarios where belief does nothing, dragging
its base rate down.

Two implementation bugs surfaced on the way and are fixed: `through`
recorded only one mediating mind per requirement, losing the actor on
`meet` goals, and `mind_dependence` excluded the actor by design.

### What is left of the escalation question

One line, and it subsumes the section above:

**Nothing available to the sparse pass predicts whether re-representation
will help.** Output properties fail because the sparse pass is reasoning
correctly over what it was given. Structural properties fail because the
dependence on a mind is always present. This is close to a consequence of
the design — the manipulation *is* withholding the information that would
change the answer — so it should be read as confirming that framing rather
than as a discovery.

What that leaves for a policy is cost, not detection. Escalating everywhere
catches everything; the only measured saving is that goal recognition from
an observation is nearly barren on this corpus (base rate 0.08), and that
is an empirical fact about Jev rather than something derivable from the
dependency graph.

The finding that does not reduce to this, or to "deeper theory of mind is
harder", is *Re-representation needs an alternative, not just a problem* —
a claim about what the richer representation must contain rather than about
how deep the nesting goes.

## Unresolved: the history's surface form moves the result

> Superseded. The confound this section identifies is real and the
> reasoning about why it matters still stands. The *measurement* in it
> does not: both renderings here sat in a state that was symbolic
> everywhere else, and once each arm is made internally consistent the
> prose advantage almost vanishes. The speculation below about narration
> marking events as events is not supported. See *Surface form: prose
> does not help, and hurts nested attitudes*.

The `history` condition was rendered two ways, over identical events
entailing identical beliefs. The only difference is wording:

    narrated   1. report is put in the office (seen by Sam)
               2. report is taken from the office (seen by nobody)

    symbolic   1. located(report, at office) = True  [witnessed by Sam]
               2. located(report, at office) = False [witnessed by nobody]

Acceptable mass on the 24 first-order scenarios, same model, same run:

| scenario | symbolic | narrated |
|---|---|---|
| bakery_false_negative | 0.00 | 0.47 |
| bakery_false_positive | 0.01 | 0.51 |
| lighthouse_false_positive | 0.12 | 0.44 |
| report_false_positive | 0.04 | 0.25 |
| *all 24, mean* | *0.52* | *0.60* |

The whole effect sits in the false-belief cells. The true-belief cells are
identical to two decimal places, which is what makes this more than noise:
the wording matters exactly where the agent's belief has to come apart
from the world.

A plausible reading is that `= True` followed by `= False` about the same
claim reads as two contradictory facts, while "is put in / is taken from,
seen by nobody" reads as an event someone missed. If so, the narration is
not decoration — it is what marks the events as *events*, and the symbolic
form quietly deletes the temporal structure the condition depends on.

### Why this is a problem and not a preference

The three-condition design claims to vary one thing. It does not:

- `sparse`, `world_state` and the `mental_state` that `rich` adds are all
  symbolic. A narrated history is the only prose in the corpus, so
  `history_mixed` differs from `rich` in style as well as in explicitness.
- A symbolic history holds style constant but demonstrably handicaps the
  middle condition, so it understates what evidence affords.

Either choice biases the `history` -> `rich` comparison, in opposite
directions, and neither is the neutral option. The measured gap between
the two renderings (0.52 to 0.60 mean, up to +0.50 in a cell) is large
relative to the effects being reported, so this is not a detail that can
be noted and set aside.

### Options, none of them yet taken

1. **Render every condition in prose**, including `mental_state`, so style
   is constant and symbolic-vs-prose stops being confounded with
   sparse-vs-rich. Costs a rewrite of all the renderers and makes the
   state less machine-checkable.
2. **Run both renderings as conditions** and report the range rather than
   a point estimate. Doubles the middle condition's cost and leaves the
   `rich` style still unmatched.
3. **Render `mental_state` symbolically and `history` both ways**, then
   check whether prose helps `rich` too. If it does, the effect is about
   surface form generally and not about histories; if it does not, the
   narration is doing something specific to event structure.

Option 3 answers the question most cheaply and should probably come
first. Until one of these is done, any number from the `history`
condition carries an unmeasured surface-form term.


## Evidence for a belief is worth less than the belief

Three conditions over all 68 scenarios: `sparse`, then the
epistemic-access events a belief follows from without the belief, then
`rich`, which states it. The middle condition is `history` —
every section in one notation, no preamble — because the mixed rendering
this was first run with turned out to carry two formatting advantages
worth most of its effect. See *Where the mixed rendering's advantage comes
from*.

| pairing | n | influence | utility | acceptable mass | corrections | regressions |
|---|---|---|---|---|---|---|
| sparse -> rich | 68 | 0.43 | +0.36 | 0.51 -> 0.87 | 28 | 0 |
| sparse -> history | 68 | 0.15 | +0.06 | 0.51 -> 0.58 | 6 | 1 |
| history -> rich | 68 | 0.33 | +0.30 | 0.58 -> 0.87 | 23 | 0 |

**Evidence from which a belief follows closes about a sixth of the gap;
stating the belief closes the rest.** On the motivating framing: the
belief has to be *represented*, not merely *derivable*, and the margin is
wider than it first looked — four to one rather than two to one.

`sparse -> rich` is unchanged from the run made with the mixed middle
condition, to every figure in the row, because neither of its passes
moved. That is a 68-scenario replication of two conditions across two
runs, and it is the strongest evidence yet that the aggregates are stable
and that what moved in the middle row is the rendering rather than noise.

| template | sparse | history | rich | n | share of the gap |
|---|---|---|---|---|---|
| attribution | 0.26 | 0.44 | 0.94 | 12 | 26% |
| discriminative | 0.75 | 0.79 | 0.90 | 16 | 27% |
| second_order | 0.49 | 0.54 | 0.95 | 16 | 10% |
| first_order | 0.50 | 0.52 | 0.77 | 24 | 9% |
| **all** | **0.51** | **0.58** | **0.87** | **68** | **17%** |

Attribution is still the striking row: the history lifts it 0.26 -> 0.44,
and stating the belief takes it to 0.94. Watching one agent come to think
something does move what a second agent is predicted to do. That row only
measures anything because the history represents the access of the agent
the question is *about* — an earlier version gave the attribution set a
history for the other agent's belief instead, which is the wrong level.
See *Resolved: an attribution is a claim like any other* in
future_scenarios.md.

The split across templates is worth more than the aggregate. Where the
history closes a quarter of the gap it does so in the two templates whose
scenarios turn on *who was where* — an attribution, or a discriminative
pair of beliefs. In first- and second-order action prediction it closes
under a tenth. Evidence about access helps where the question is social;
where the question is about a single agent and a single fact, stating the
belief is very nearly the only thing that works.

### The history can make things worse

Three cells lose mass under the history, one of them badly enough to flip
the answer:

| scenario | mass | note |
|---|---|---|
| `coffee_true_negative` | 0.76 -> 0.23 | `get_food` -> `get_coffee`, truth `wash_mug` — the one outcome regression |
| `clinic_true_true` | 0.83 -> 0.56 | answer stays correct, confidence in it does not |
| `workshop_true_true` | 0.82 -> 0.58 | same |

All three are cells whose padding added a superseded sighting where there
had been one event, and `coffee_true_negative` moving to `get_coffee` is
what the padding's distractor risk looks like: the added event mentions
the coffee being stocked before it ran out, and the answer moved toward
the mention. The same three cells misbehaved under the mixed rendering, so
this is not a property of the notation. Read as suspicious rather than as
a finding until rerun without the padding.

### Escalation, with the rendering corrected

`history -> rich` gives 23 corrections against 68 scenarios. Escalating on
"the answer is contradicted by what is known" fires four times at
precision 0.00; escalating whenever the task is action prediction fires 40
times at precision 0.50 and recall 0.87; escalating always fires 68 at
precision 0.34. The ordering is the same as before and so is the reading —
see *Nothing available to the sparse pass predicts whether
re-representation will help*.

### What the earlier figure was

Recorded because the difference is the whole point of the three
experiments that follow. The same script with the mixed middle condition
gave `sparse -> history` as 0.51 -> 0.63, influence 0.20, 9 corrections,
and put the history's share of the gap at a third. Roughly half of that
extra 0.05 was the history looking different from its surroundings and the
rest a preamble that only helps by being absent. On a matched 12 the
rendering moves the share from 42% to 11%.

*Evidence is worth less than the belief* holds under every rendering and
is the finding. *How much* less is not quotable without naming the
rendering, and the number to quote now is the consistent one.

## Surface form: prose does not help, and hurts nested attitudes

Supersedes *Unresolved: the history's surface form moves the result*,
which measured two renderings of the history inside a state that was
symbolic everywhere else — so neither arm was internally consistent and
the comparison confounded register with contrast against the surroundings.

This crosses the three richness levels with two arms that are each
consistent throughout, `world_state`, `history` and `mental_state` alike.
12 scenarios over four sets — `report`, `mailroom`, `meeting`,
`attribution` — three cells each: the two where the belief diverges from
the world, plus one agreement control.

| richness | symbolic | narrative | difference | influence |
|---|---|---|---|---|
| sparse | 0.42 | 0.42 | 0.00 | 0.06 |
| history | 0.48 | 0.51 | +0.03 | 0.15 |
| rich | 0.95 | 0.87 | **-0.08** | 0.11 |

**Prose does nothing for `sparse`.** A representation with no mental
content is indifferent to how it is written, which is the control this
question needed and never had.

**Prose is worth +0.03 at the history level.** Real against the noise
floor below, and trivial. Nothing like the 0.52 -> 0.60 the superseded
section reports, so the story offered there — that narration is what
marks events as *events*, and the symbolic form deletes the temporal
structure — is not supported. Whatever the earlier effect was, it was not
prose.

**Prose costs 0.08 at the rich level, entirely in nested beliefs.**

| cell | symbolic | narrative | entropy |
|---|---|---|---|
| `meeting_false_positive` | 0.93 | 0.68 | 0.37 -> 0.90 |
| `meeting_false_negative` | 0.96 | 0.67 | 0.24 -> 0.91 |
| `attribution_false_attribution_true_belief` | 0.96 | 0.71 | 0.24 -> 0.87 |
| `attribution_false_attribution_false_belief` | 0.94 | 0.65 | 0.33 -> 1.04 |
| the four first-order divergent cells | 0.84-1.00 | 0.83-1.00 | no loss |

    symbolic   believes(Sam)[believes(Alex)[located(meeting, at office) = True]]
    narrative  Sam believes that Alex believes that the meeting is in the office.

Bracket nesting says unambiguously who holds what; a doubled *believes
that* is a garden path, and entropy roughly tripling says the model is
losing track rather than disagreeing. The loss appears only where the
belief diverges from the world — the nested control cells sit at 0.99 and
1.00 in both arms, with nothing to lose.

**Design implication, the reverse of what the superseded section
suggests: render nested attitudes symbolically.** Prose buys nothing
anywhere and costs a quarter of the acceptable mass on exactly the cells
the second-order and attribution templates exist to test.

### The noise floor

Two runs over identical stimuli, 24 condition-scenario pairs (`sparse` and
`rich`, symbolic, on the 12): mean absolute difference 0.010, maximum
0.08. So a *mean over twelve* is stable to about 0.01 and the table above
is interpretable; a *single cell* is not interpretable below about 0.08.
That is the first direct measurement of run-to-run variation in the
project, and it supports the ~0.05 per-cell figure quoted in
future_scenarios.md while showing that aggregates are far tighter than
that implies.

## Where the mixed rendering's advantage comes from

The mixed rendering — prose events inside a symbolic state, which is what
the middle condition had always been — scores 0.62 at the history
level, above *both* internally consistent arms (0.48 symbolic, 0.50
prose). It differs from `history_prose` in three ways at once, so a chain
was run that varies one at a time. Twelve scenarios, four conditions, one
batch.

| condition | surroundings | events | preamble | mass | delta | factor |
|---|---|---|---|---|---|---|
| `history_mixed` | symbolic | listed | no | 0.62 | | |
| `history_mixed_preamble` | symbolic | listed | yes | 0.54 | **-0.08** | the preamble |
| `history_narrated_preamble` | symbolic | sentences | yes | 0.56 | +0.02 | event wording |
| `history_prose_preamble` | prose | sentences | yes | 0.50 | **-0.06** | the surroundings |

The endpoints replicate across runs to 0.01 — `history_mixed` 0.62 against
0.63 in the 68-item run, the prose end 0.50 against 0.51 in the run above —
so the deltas are readable against the noise floor.

**None of the 0.12 is about epistemic access.** It is a preamble that
should not be there and a contrast effect that has nothing to do with
minds. The corpus's middle condition has been carrying both since it was
built.

### The preamble never helps, and sometimes hurts a lot

`HISTORY_PREAMBLE` was added "so a superseded early event does not read as
a contradiction of the current world_state". It costs 0.08 where the events
are narrated, with two regressions on that link alone — one of them
`attribution_false_attribution_false_belief` collapsing 0.67 -> 0.08 from
those two sentences and nothing else.

It does not transfer to a symbolic history, where it was expected to matter
most, being the only prose in the state:

| condition | mass |
|---|---|
| `history_preamble` (with preamble) | 0.48 |
| `history` (without) | 0.49 |

So it is an interaction with the event rendering rather than a main effect:
redundant where the narration already carries sequence, inert where the
notation cannot carry it at all. Either way it never earns its place, and
the reading to take is **drop it**.

A prediction failed here and the failure is worth keeping. Since the
preamble cost 0.08 on narrated events, the symbolic arm was expected to be
understated by about as much, which would have moved the share of the
sparse-rich gap the history closes from a ninth to roughly a quarter. It
does not: 0.48 and 0.49 are the same number, the ladder stays
0.42 -> 0.48 -> 0.95, and the 11% figure stands as first reported.

### Contrast against the surroundings is worth 0.06

Same events, same preamble, only the surrounding sections turning from
symbolic to prose, and 0.06 of acceptable mass goes with them. Part of the
history's advantage is that it *looks different from everything around it*.
Its two regressions on that link are `meeting_false_positive`
(0.53 -> 0.22) and `attribution_false_attribution_true_belief`
(0.56 -> 0.26) — nested and attribution cells, as with the preamble, and as
with the prose penalty at the rich level. Formatting does its damage in the
same place every time.

A real effect on the corpus and an uninteresting one about the phenomenon.
It belongs in the design as a nuisance parameter to hold constant, not as
something the middle condition is entitled to.

### Event wording is a wash

+0.02 for past-tense sentences with the witness folded into them, against a
numbered present-tense list with `(seen by Sam)`. One correction, no
regressions. The hypothesis that the sentence rendering was simply worse is
dead, which is the only outcome here that would have required rework.

### What a defensible middle condition looks like

Nothing measured is both internally consistent and preamble-free except
`history` itself, at 0.49. The untested cell is narrated sentences
in a symbolic state with no preamble, which the deltas put at around 0.64 —
near the mixed condition, and for the same reasons, since that is very
nearly what the mixed condition is.

The choice is not which scores highest. A rendering that scores well by
standing out is measuring salience. Either hold the contrast constant
across every condition, which would mean giving `sparse` and `rich` a
differently formatted section too and is absurd, or take a consistent arm
and report the smaller number. The second is the honest option, and it puts
the history's contribution at a sixth of the sparse-rich gap corpus-wide
rather than the third the mixed rendering suggested.

One asymmetry survives all of this and is now moot. `HISTORY_PREAMBLE`
ended with "world_state is the situation now", glossing a section every
condition carries while only the history conditions were told it. Since the
preamble should go, the asymmetry goes with it.
