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

**Belief-vs-belief disagreement is not checked at all.** Nothing compares
mental states to each other, so `attribution_FT` reports
`world_conflict: false` despite Sam and Alex plainly disagreeing about
where Alex thinks the meeting is. Detecting it needs a second relation —
compare an attribution's inner proposition against the attributed agent's
own belief — not a widening of the existing one. The two should stay
separate measures: one is about the world, the other about a person.

This gap now has a concrete cost: across the corpus, `world_conflict` does
not predict influence (the two largest influences in the `meeting` set have
no first-order conflict), while the `belief_changes_expected_action`
annotation does. A belief-vs-belief measure might close that.

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

## Open problem: coffee_false_negative

The one failing cell in the corpus, and the only place design intent and
measurement disagree. Annotated `belief_changes_expected_action: true`, it
measures influence ~0.05 where its group averages 0.80, and stays
`stable_incorrect`: the rich pass still answers `get_coffee` at ~0.92 even
though Sam's belief rules coffee out. The belief registers in entropy
(0.19 -> 0.41) without dislodging the argmax.

Worth diagnosing before more items are built on the same pattern.
