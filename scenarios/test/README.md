# Held-out scenarios

Thirty-two scenarios, none of them measured. The design, the verification
and the two faults found in review are in `notes/held_out_corpus.md`.

The escalation policy was fixed before this directory had contents, in *The
policy to be tested, fixed in advance* in `notes/experimental_design.md`.
That ordering is the only thing that makes what goes here a test rather
than more development data, and it survives only as long as nobody looks.

## What that means in practice

**Do not run experiments against this split while building it.** The
experiments pass `split="dev"` for that reason. A scenario measured here
before the corpus is complete has been spent, and the honest response is to
move it to `dev` rather than to quietly keep it.

**Do not tune a scenario because of how a model answered it.** The same
rule the corpus already follows — see *Not tuning stimuli to results* —
applies with more force here, because there is no second held-out set.

## What is here

Eight sets of four cells, crossing task family with **representational
function** — whether the belief names an alternative or only denies one —
so that task family is not confounded with what the richer representation
is doing. On the development corpus those two are entangled, which is why
the task-family heuristic is the strongest policy there and why it cannot
be trusted to generalise.

    action_prediction/discriminative   loading_gate, tide_gauge
    action_prediction/inhibitory       quarry_road, ward_round
    goal_recognition/discriminative    returns_desk, slipway
    goal_recognition/inhibitory        archive_desk, plant_room

Seven cells have a determinate world reading and a spread belief reading,
so representing the belief replaces a confident correct answer with
uncertainty. The development corpus has none, which is why nothing there
can penalise a policy for escalating too often.

Anything added later belongs in a surface domain that appears in neither
split. Domain novelty is part of the test.

## Layout

Same taxonomy as `dev/`, one level down from the split:

    scenarios/test/<task_family>/<template>/<domain>/<condition>/<lex>.yaml

The path is the source of truth, so moving a file between `dev/` and
`test/` reclassifies it — which is exactly the move to make if something
here gets measured by accident.
