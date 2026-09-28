# Held-out scenarios

Empty on purpose. Nothing here has been measured.

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

## What belongs here

Complete matched scenario families, in surface domains that do not appear
under `dev/`. Domain novelty is part of the test: a policy that only works
on the sixteen domains it was selected on has not been shown to generalise.

The set should cross task family with **representational function** — the
distinction between a re-representation that positively supports an
alternative reading and one that only undermines the existing reading —
so that task family is not confounded with what the richer representation
is doing. On the development corpus those two are entangled, which is why
the task-family heuristic is the strongest policy there and why it cannot
be trusted to generalise.

It should also contain scenarios where the richer representation makes the
answer **worse**. The development corpus has none: `rich` never damages a
scenario the history pass got right, across all 68. While that holds,
nothing can penalise a policy for escalating too often, and every
escalation rate looks free.

## Layout

Same taxonomy as `dev/`, one level down from the split:

    scenarios/test/<task_family>/<template>/<domain>/<condition>/<lex>.yaml

The path is the source of truth, so moving a file between `dev/` and
`test/` reclassifies it — which is exactly the move to make if something
here gets measured by accident.
