# Experimental design

## Findings so far

Stated as they currently stand, newest understanding first. Each links to the
section that establishes it; where a later section refines an earlier one, the
later wording is the one to use.

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

**Belief moves action prediction substantially** — 0.43–0.48 mean influence
across every action-prediction template, 24 corrections and no regressions
in 68 scenarios. See *Belief moves action prediction, not goal recognition*,
whose title states the goal-recognition half too strongly; the first finding
above is the corrected form.

**Nothing computable from the sparse pass predicts whether re-representation
will help.** Neither its confidence, nor a conflict between what it knows and
the world, nor its own answer being ruled out by what is known. Where belief
matters most the sparse pass is at its most confident, because the
information that would change its mind is exactly what was withheld. A
negative result for self-monitoring accounts of escalation. See *Sparse-state
signals do not reliably identify the need for re-representation*.

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

`coffee_false_negative` is the one failing cell in the corpus: annotated as
requiring belief, it measures influence ~0.05 where its group averages 0.80,
and the rich pass still answers `get_coffee` despite Sam believing there is
none. It is left as it is, deliberately.

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
| action prediction | attribution | 12 | 0.48 | 6 |
| action prediction | first order | 12 | 0.48 | 6 |
| action prediction | second order | 16 | 0.45 | 8 |
| goal recognition | discriminative | 16 | 0.43 | 4 |
| **goal recognition** | first order | 12 | **0.00** | **0** |

Two of those figures moved after the numbers below were first recorded, and
both moves were data fixes rather than model behaviour. Attribution fell
from 0.69 because its worlds never said where the agent being met actually
was, so sparse failed those cells for an unrelated reason and rich looked
like it was correcting more than it was. Goal-recognition first-order fell
from 0.07 to nothing at all once the scenarios stated what the carried
object was for, which gave sparse more to work with. Both are recorded in
the commit log; the qualitative claims are unchanged.

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
moves 0.43–0.48 and produces 24 corrections with no regressions, the
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
| only subtracts the primary goal | `coffee`, `darkroom`, `greenhouse` | 0.00 |

In `false_false` the belief says the package is at the front desk — a
positive claim that supports a competing reading of the walk, and the model
moves to it (correction, P 0.36 -> 0.83). In `true_false` the belief says
neither the package nor Alex is at the front desk. That *undermines* the
sparse reading without supplying anything in its place, and the model did
not merely fail to switch: entropy fell from 0.94 to 0.68 and it answered
`meet_alex` more confidently — the very reading the belief rules out. The
subtractive goal-recognition domains behave the same way, and have since
fallen to 0.00 flat — once those scenarios stated what the carried object
was for, sparse had more to work with and belief moved it not at all.

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
correction. 68 scenarios, 25 corrections.

**Sparse uncertainty.** Mean sparse entropy is 0.28 where a correction
follows and 0.30 where none does — no separation, and slightly the wrong
way round. Thresholding does not help: 6 of 18 scenarios above 0.5 bits are
corrections, against 19 of 50 below it. More pointedly, 13 of the 25
corrections have sparse entropy below 0.2 — near-certainty on two or three
options — and those carry a mean influence of 0.92. The sparse pass is at
its most confident precisely where belief is about to overturn it.

**Objective-world conflict.** 11 of the 14 second-order and attribution
corrections have no world conflict at all, at mean influence 0.87. Three of
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
pass — 0.05 where a correction follows against 0.84 where none does. That is
not a trigger but a restatement of the target: it is computed from ground
truth, and predicting it is the whole problem.
