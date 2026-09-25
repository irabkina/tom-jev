# Scenario backlog and known gaps

## Built: contradicted second-order belief

The `attribution` set now covers this. It is a 2x2 over two independent
questions — does Sam's belief about Alex's belief match what Alex actually
believes, and does Alex's belief match the world — with both mental states
represented so the attribution can be wrong about Alex:

| variant | world | Alex believes | Sam attributes | truth |
|---|---|---|---|---|
| TT | office | office | office | office |
| TF | conference room | garden | garden | garden |
| FT | office | office | conference room | conference room |
| FF | conference room | garden | office | office |

Ground truth is always where Sam believes Alex believes the meeting is:
Sam acts on the belief Sam holds. Alex's actual belief and the world are
both stated in the rich representation and must not move the prediction —
reading either as Sam's is a perspective error, and each cell places the
distractors on different options so that error is visible.

`FT` is the sharpest cell: the world and Alex's own belief agree on the
office, and only Sam's mistaken attribution points elsewhere. A purely
social error, with nothing about the world to mislead.

Distinct from the `meeting` set, which uses the standard
(world supports action) x (agent believes supported) 2x2, has no second
mental state, and is two-option. Kept as a separate `scenario_set` so the
two axis systems do not share a naming scheme — `meeting_FP` and an
`attribution_FF` mean different things by "F".

## Detector gaps

`analysis.world_conflict` means, precisely: *a first-order belief that
directly contradicts an explicitly stated world fact*. Three things fall
outside it.

**Second-order attributions** are skipped deliberately — a belief about
another agent's belief makes no claim about the world, so there is no known
conflict. Correct as far as it goes, and documented in schema.yaml.

**Belief-vs-belief disagreement — closed.** `analysis.attribution_conflict`
and `world.attributions` now compare an attribution's inner proposition
against the attributed agent's own belief. Kept as a separate measure
rather than folded in, since one asks whether a belief matches the world
and the other whether it matches a person. Across the attribution set the
two are exactly orthogonal, which is the 2x2 that set was built on. `None`
where the other agent has no represented belief, which is 56 of 68
scenarios: an attribution can only be wrong about someone the scenario
represents.

It did not close the gap it was expected to. `world_conflict` still fails
to predict influence — 11 of the 14 second-order and attribution
corrections have no world conflict at all — and adding the second dimension
does not rescue it, because most of those cases are uncheckable rather than
non-conflicting. See *Sparse-state signals do not reliably identify the
need for re-representation* in experimental_design.md.

**Beliefs about unstated facts are invisible.** Conflict is found by exact
signature match against `world_state`, so a belief about something the
scenario never states simply misses. The `attribution` scenarios state all
three locations explicitly for this reason — drop one and Alex's false
belief stops registering. That is the right default under an open-world
reading, but if the distinction starts mattering, conflict wants three
values rather than two: contradicted, confirmed, unknown.

## Note on option count

`report` and `meeting` are two-option. With two options, TV influence
reduces exactly to `abs(utility)` and the two measures carry identical
information; they only separate at three or more. `coffee` and
`attribution` have three. Prefer three for new items where the task admits
it.

## Resolved: coffee_false_negative was not an item problem

Previously recorded here as the one failing cell. With `darkroom` and
`greenhouse` added, it is the first observed instance of a systematic
effect: belief moves action prediction substantially and goal recognition
barely at all, across three domains with no shared vocabulary. See "Belief
moves action prediction, not goal recognition" in experimental_design.md.

It stays unmodified.

## Built: separating observation from belief

The `mailroom` 2x2 under `goal_recognition/discriminative/` does this. The
world and the observation are held constant across all four cells — package
at the mailroom, Alex at the front desk, Sam walking toward the front desk
— and only Sam's beliefs vary, over whether each of the two beliefs matches
the world. Sparse is therefore *identical* in every cell, so all variation
is attributable to belief.

| cell | Sam believes | belief does | influence |
|---|---|---|---|
| true_true | pkg@mailroom, Alex@desk | confirms the sparse reading | 0.34 |
| true_false | pkg@mailroom, Alex@mailroom | removes it, offers nothing | 0.12 |
| false_true | pkg@desk, Alex@desk | adds a competing reading | 0.58 |
| false_false | pkg@desk, Alex@mailroom | replaces it outright | 0.53 |

(One run each; these move by ~0.05 between runs. The ordering is stable,
the second decimal is not.)

This is what showed that "belief does not move goal recognition" was too
coarse — see "Re-representation needs an alternative, not just a problem"
in experimental_design.md. Hand-written rather than generated: the
structure had no siblings, and generating a family of one would fix a shape
before it was known to work. Now that it does work, it is a candidate fifth
template.

## Still open: an observation compatible with several goals

The other half of the confound. Every goal-recognition item still states an
observation that on its own implies one goal more than the others — the
`mailroom` walk is neutral between its two options only because both
candidate targets are locations Sam might walk to, which is a property of
that story rather than a designed feature. An item where the observed
action genuinely carries no preference would isolate belief further.

## Still open: an observation the world cannot account for

No scenario in the corpus contains one. Asked properly — is *any* goal in
play satisfiable at the observed destination, given background requirements
and the episodic world — every observed walk is accounted for. Sam's walk
to the coffee-less kitchen is explained by washing the mug; the darkroom
walk by collecting prints.

That is why the anomaly detector never fires, and it is a gap in the corpus
rather than in the rule. An item where the observation is genuinely
unaccountable — every candidate goal blocked at that place — would be the
first real test of whether an observer can notice, from the sparse
representation alone, that something needs explaining.

Worth building precisely because the negative result above says nothing
inside the sparse inference predicts the need to re-represent. If any
sparse-side signal works, this is the shape it would have.
