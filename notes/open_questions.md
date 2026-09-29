# What is still under question

Findings are in `notes/experimental_design.md` with the caveats each one
carries. This is the shorter list of things that are *not* settled — what a
write-up should not claim, and what a reader would be right to ask about.

Scenario-level gaps are in `notes/future_scenarios.md`; this is about
method and interpretation.

## One cell where true information reliably hurts

`coffee_true_negative` scores 0.76 under `sparse`, 0.23 under `history`,
and 0.53 once the equal-length padding is removed. Two thirds of the loss
was the control. The remaining 0.23 is not, and nothing explains it. The
answer flips to `get_coffee` — the goal the world does not support — and
it does so more confidently once the history is present.

It is the only cell in 100 where adding true information makes the answer
reliably worse by more than the noise floor. One cell is not a finding, but
it is not nothing either, and it should not be quietly dropped from a
table.

## The middle condition's value is a range, not a number

The history closes 17% of the sparse → rich gap as measured and 39% with
the equal-length control removed. Both are true statements about different
things: the first is what the corpus as it stands produces, the second is
what the evidence is worth when the control is not charged to it.

Any comparison involving `history` inherits this. Three release notes quote
the single figure, and *Evidence for a belief is worth less than the
belief* is written around it.

## A cheaper control has not been looked for

The current padding shows the agent a sighting and then overturns it, which
is about the most confusing thing it could do while staying inert to the
derivation. Padding with an event about something irrelevant would keep
event counts even without planting a superseded belief.

Whether that is cheaper is unmeasured. It is a corpus change, so it would
need the same care the last one did, and it would invalidate the stored
runs for every padded scenario.

## The task family by function cross is eight scenarios per cell

It did its job: it decoupled task family from representational function and
showed the task-family heuristic was a property of the development corpus.
As a *reported* result — that inhibitory re-representation behaves
differently from discriminative — it is underpowered, and the per-cell
figures should not be quoted as findings.

## Nothing held out remains

The test split has been measured twice and one of its scenarios was read
while debugging the belief derivation. `notes/held_out_corpus.md` records
both uses and which carries out-of-sample weight. There is no unspent
corpus, so the next claim that needs one needs a new corpus first, and the
pre-registration discipline only works if the corpus comes after the
prediction.

## The escalation saving is still notional

Mean input tokens are 381 sparse, 442 history, 412 rich, so the middle pass
is the most expensive of the three and a two-stage policy costs more calls
than escalating always. Deriving beliefs from the graph removed the
*structural* objection — constructing the rich representation is now real
work rather than a file read — but this pilot still cannot price it,
because the expensive part happens outside the model and nothing here
measures that cost.

What the held-out run establishes is that a trigger exists and generalises,
not that using it saves anything in this setup.

## Declared predicate functionality is unexercised

`knowledge/predicates.yaml` says `located` is functional in its location
and `available` is not. No scenario distinguishes the two: `available`
claims either carry no location or sit in single-location scenarios. The
rule is right and untested by measurement, and the same gap is recorded
from the graph's side in `notes/graph_ontology.md`.

## What a replication would and would not buy

The materialisation null replicated on the second corpus and the small
distributional movement did not — influence on changed stimuli came in
*below* that corpus's drift floor. Eight scenarios have a changed stimulus
there, so the non-replication is as thin as the thing it fails to
replicate. The claim both corpora support is that the answers do not
change; anything finer should wait for a corpus built to test it.
