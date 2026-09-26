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

## Still open: histories are derived from the beliefs they entail

`scripts/add_histories.py` does not author a backstory. It reads the
beliefs of the agent the question is about and emits the events that make
them true: the agent witnesses a claim being settled as they are stated
to believe it, and where something disagrees — the world, for a claim
about the world; the other agent, for a claim about that agent's belief —
a further event settles it otherwise with nobody watching.

That guarantees entailment by construction, which is what the middle
condition needs — `history` and `rich` must carry the same belief, or they
are not two representations of one scenario. `analysis.entailed_beliefs`
then recovers the belief from the events independently, and a corpus test
holds the two to agreement.

The cost is that the history is a mechanical transform of the belief
rather than a plausible course of events. Consequences worth testing:

- **No irrelevant events.** A real history contains changes that bear on
  nothing at all. The padding below adds superseded sightings, but they
  are about the very claim in question, so the model still never has to
  work out *which* access matters — only which sighting is current.
- **Minimal length.** Two events per belief, four in the discriminative
  set. Belief attribution from access presumably gets harder with more
  events between the sighting and the present, and nothing here tests
  that.
- **One shape.** Always "saw it, then missed the change". Never
  "was told", "inferred", "saw a trace", "was absent the whole time".
- ~~**The false-belief cells are longer than the true-belief cells.**~~
  Fixed. Every belief now contributes exactly two events: a false one is
  settled in view and settled again out of view, a true one settled
  twice in view. Before the fix, event count alone classified the
  condition and a model could have scored well on `history` by counting
  and never representing a belief. A corpus test holds the invariant,
  and a second test checks the padding is inert — dropping it does not
  change what the history entails.

  Where a thing *is* gets superseded by moving it; availability gets
  flipped, since it is not exclusive across places and stocking the
  coffee elsewhere would not supersede a belief about the kitchen. The
  alternative location comes from `world_state` in file order, so a
  padded true cell uses the same place its matching false cell moves to.

  Two residues. **Position is still not matched**: in a true cell the
  believed claim is settled second, in a false cell first and then
  superseded out of view. Equalising that needs three events per cell.
  And the padding **adds a mention of the alternative location**, which
  may pull probability toward the distractor — symmetrically across
  cells, so the contrast should hold, but absolute numbers from before
  the padding are not comparable to numbers after it.

Hand-authoring a few histories per domain and comparing them against the
derived ones would say how much of the middle condition's behaviour is an
artefact of the derivation.

## Resolved: an attribution is a claim like any other

An earlier version of the derivation skipped second-order beliefs, on the
grounds that entailing "Sam believes Alex believes X" needs Sam to have
access to *Alex's* access, which `HistoryEvent` could not express. It then
gave the attribution set a history for Alex's own belief instead.

That was the wrong level. What Sam believes about Alex's belief sits
beside what Sam believes about the coffee machine: a claim Sam witnessed
being settled, and may since have missed being settled otherwise. Sam does
not need access to Alex's access — Sam needs access to the event of Alex
coming to think something, which is an ordinary observable event.

So `HistoryEvent` now carries a `Proposition` rather than flattened
fields, and the same derivation covers every depth:

    attribution, Sam wrong about Alex, Alex wrong about the world
      1. Alex comes to think that the meeting is in the office (seen by Sam)
      2. Alex comes to think that the meeting is in the garden (seen by nobody)

    second order, nothing stated about what Alex actually thinks
      1. Wen comes to think that the crew briefing is in the galley (seen by Noor)

The history represents the access of one agent: the one the question is
about. Alex's own access is not represented, because nothing is predicted
about Alex; Alex's actual belief reaches the history only as the event Sam
missed. Locative exclusivity passes through the nesting, so witnessing
Alex come to think the meeting is in the office is witnessing Alex come to
think it is not in the garden.

All 68 scenarios now carry a history. What still has no vocabulary is an
event whose *witnessing* is itself witnessed — third order, "Sam saw Kim
see Alex find out" — which no current scenario needs.
