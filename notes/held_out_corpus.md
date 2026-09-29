# The held-out corpus

Thirty-two scenarios under `scenarios/test/`, built to test the escalation
policy fixed in *The policy to be tested, fixed in advance*. Written after
that policy and before any of it was measured, which is the only thing that
makes this a test rather than more development data.

Nothing here has been run against the model.

## What it is for

The development corpus cannot settle the escalation question, because the
strongest policy on it — *is this action prediction* — is a property of how
that corpus was built rather than of the task. Task family is entangled
there with what the richer representation actually does. This corpus takes
the two apart by crossing them:

| | discriminative | inhibitory |
|---|---|---|
| **action prediction** | `loading_gate`, `tide_gauge` | `quarry_road`, `ward_round` |
| **goal recognition** | `returns_desk`, `slipway` | `archive_desk`, `plant_room` |

Eight sets, four cells each. The function is defined by what the belief
does *where it diverges from the world*:

**Discriminative.** The belief names something else. Rasheed believes a
different gate is open; Nadia believes a different item is waiting at the
counter. Representing it should move mass onto a determinate answer.

**Inhibitory.** The belief only denies. Idris believes the haul road is
shut and says nothing about which bypass; Bijan believes the registrar is
not on the ward and does not know where they are. Representing it should
spread mass rather than move it, because nothing replaces what was removed.

## The domains are new, and so are the relations

No domain appears in both splits. More to the point, none of these is a
development set with the nouns changed. Every dev set turns on where a
thing is or who is where; these turn on which way in is open, which
instrument is serviceable, whether a road is passable, whether a person is
on the ward, what is waiting at a counter, what is out ready to use, what
is present, and what is to hand.

The formal vocabulary is the corpus's own — `located`, `available`,
`walks_to`, `obtain`, `meet` — so nothing downstream needed changing. One
predicate is new: `direct`, marking the haul road as the obvious route.

## How it was built

`scripts/make_test_corpus.py` holds the eight specs and writes the files;
`scripts/add_histories.py` then derives the histories from the stated
beliefs, as it does for the development corpus, which is what guarantees
entailment by construction. No history was written by hand. The generator
refuses to overwrite an existing scenario, so a file edited by hand
survives a rerun.

## What was checked

Two review passes. The first found four mistakes, the second found two
design problems; both are recorded below rather than quietly fixed,
because the second kind would not have shown up in any test.

### Structural — 0 problems across 32

No unreferenced entities, no contradictory world facts, nothing located in
two places at once, `acceptable` inside `options`, `answer` inside
`acceptable`, `belief_matches_reality` agreeing with the derived
`world_conflict`, history length exactly twice the belief count, belief
count constant within every set, four cells per set, no domain overlap with
dev, no duplicate ids across the hundred, no repeated option strings, no
entailment mismatches.

### Semantic — 0 problems

Ground truth follows from that cell's beliefs in all 32, and
`belief_changes_expected_action` agrees with the world-only reading in all
32. Both were checked against a simulator written from the set designs
rather than read off the files, so agreement means two independent
statements of the design match.

### Padding is inert

Dropping every unwitnessed event leaves what the history entails unchanged,
in all 32. Worth stating separately: the padding exists to stop event count
classifying the condition, and if it were not inert it would be a silent
leak rather than a control.

### Condition isolation

`sparse` never carries a belief or a history; `history` and `rich` each
differ from it by exactly one section, with every shared section
byte-identical. Checked per scenario, not assumed from the renderer.

## The two design problems, and what they cost

Neither would have failed a test. Both were found by asking what the corpus
could measure rather than whether it was well-formed.

### The chance floor was confounded with task family

The goal-recognition sets had two and three options where the
action-prediction sets had four, so a uniform guess scored:

| | action prediction | goal recognition |
|---|---|---|
| discriminative | 0.25 | **0.50** |
| inhibitory | 0.50 | **0.75** |

Acceptable mass is the pre-registered primary measure. Any comparison of
the two families on it would have been partly reading the option count.
This is the same class of error the corpus exists to remove; it had simply
moved from the stimulus design into the scoring.

### Two sets could be scored perfectly without reading anything

`archive_desk` and `plant_room` first used a nested denial ladder — deny
none, deny one, deny two, deny all. The nesting left one errand acceptable
in all four cells, so a constant answer scored 1.00 against a development
mean of 0.56. Those two sets could not have distinguished a model that read
the scenario from one that said the same thing every time.

### What the fix was

Both goal-recognition inhibitory sets moved onto the same 2x2 the
action-prediction inhibitory sets use — affirm, affirm wrongly, deny with
the world's support, deny without — over four options with one belief per
cell. `returns_desk` and `slipway` gained two distractor errands each, with
world facts but no beliefs: a cell that already licenses one goal does not
need the distractors denied, so belief count and history length are
unchanged.

The denial ladder is gone, and `deny_two` — where denial narrowed the
reading to one answer *by elimination*, without ever pointing at it — is
worth a set of its own some day. It was not worth confounding the
comparison this corpus exists for.

### After the fix

```
chance floor      disc  0.25 / 0.25      inhib  0.50 / 0.50     (AP / GR)
options           4 everywhere
acceptable sizes  disc  1x8  / 1x8       inhib  (1x4,3x4) / (1x4,3x4)
best constant     0.50 in all eight sets                        (dev 0.56)
answer position   33/25/21/21                                   (dev 45/42/11/2)
sparse collapse   disc  2+1+1 both       inhib  2+2 both
```

The last row is how the four cells fold together under `sparse`. It matches
across families within each arm, so the amount of work the cheap pass is
capable of is the same on both sides of the family comparison.

## The four mistakes the first pass found

Recorded because three of them were annotation errors of exactly the kind
that survive a test suite and poison an analysis grouped by the annotation.

1. **Twelve scenarios declared an entity no fact referenced** — `switchboard`,
   `boat_locker`, `plant_office`. All 68 development scenarios reference
   every entity they declare. Beyond untidiness this is a live hazard:
   `add_histories.py` falls back to "any other declared location" when
   padding a true belief, so a dangling location can be chosen by the
   generator.

2. **`ward_round_true_negative` was annotated as not changing the expected
   action.** It does. The world puts the registrar at the theatre desk and
   Bijan only knows they are not on the ward, so representing what he
   believes turns a determinate reading into a spread. A *true* belief that
   still costs certainty — the agent's knowledge being a strict subset of
   the world's — which is now one of the more interesting shapes in the set.

3. **`archive_desk_deny_all`** was annotated the other way round, as
   changing the expected action when the acceptable set was identical to
   the world's.

4. **`plant_room_deny_all`**, the same. Both cells are gone with the ladder.

## Where escalation can now be wrong

Seven cells have a determinate world reading and a spread belief reading,
so representing the belief replaces a confident correct answer with
uncertainty:

    archive_desk_false_negative    archive_desk_true_negative
    plant_room_false_negative      plant_room_true_negative
    quarry_road_false_negative
    ward_round_false_negative      ward_round_true_negative

The development corpus has none. `rich` never damages a scenario the
history pass got right, anywhere in its 68, which means nothing there can
penalise a policy for escalating too often and every escalation rate looks
free. These seven are the first cells that can charge for it.

Four of them are `true_negative` cells, where the belief is *true* and
still costs certainty. That was not a designed feature of the first
version; it fell out of making the goal-recognition inhibitory sets mirror
the action-prediction ones, and was only noticed because mistake 2 above
forced the question.

## Known imbalance, not fixed

Beliefs run 32 `available` to 16 `located`, and the two predicates are not
evenly spread over the cross:

| | set one | set two |
|---|---|---|
| action prediction, discriminative | `loading_gate` available | `tide_gauge` **available** |
| goal recognition, discriminative | `returns_desk` located | `slipway` available |
| action prediction, inhibitory | `quarry_road` available | `ward_round` located |
| goal recognition, inhibitory | `archive_desk` located | `plant_room` available |

Three of the four cells pair one `located` set with one `available` set.
Action-prediction discriminative is both `available`, so if the predicate
itself moves the model, that cell does not average over it as the others
do.

Left as it is deliberately. The natural `located`-based action-prediction
set — an agent needs an object and believes it is in the wrong store — is
`bakery`, which is the development corpus with the nouns changed, and a
fresh domain is worth more here than predicate symmetry. Stated so that
whoever reads the result knows which way the one remaining asymmetry runs.

## Rules for using it

From `scenarios/test/README.md`, repeated because they are easy to break:

**Do not run experiments against this split while building it.** The
experiments pass `split="dev"` for that reason. A scenario measured here
before the corpus is complete has been spent, and the honest response is to
move it to `dev` rather than quietly keep it.

**Do not tune a scenario because of how a model answered it.** The rule in
*Not tuning stimuli to results* applies with more force here, because there
is no second held-out set.

**Final acceptable mass and final accuracy are not comparable across
splits.** The chance floor is 0.38 here against 0.45 on dev. The
pre-registered primary measure — the fraction of the available
History→Rich gain recovered — is scale-free and does compare.
