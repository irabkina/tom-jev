# Graph ontology

## Nested attitudes are flattened, not reified

`sam believes alex believes the meeting is in the office` could be stored
two ways. The graph flattens it:

```
            source YAML                          stored in the graph

  type: belief                          (:Proposition {
  agent: sam                                predicate: "located",
  proposition:                              value: true,
    predicate: believes                     perspective: "belief",
    subject: alex                           holders: ["sam", "alex"]
    proposition:                          })
      predicate: located                    -[:LOCATION]-> (:Location {id: "office"})
      subject: meeting
      location: office                  (:Entity {id:"meeting"})-[:SUBJECT_OF]->
      value: true
```

The alternative is a chain of Proposition nodes linked by a `CONTENT`
relation, one per attitude, with the innermost carrying the claim.

### Why flattened

Only the innermost proposition asserts anything about the world. Every
level above it attributes an attitude, and for the questions the corpus
asks, *who* holds it is all that matters — which is exactly what the
holders chain records.

That buys three things:

**Conflict is one comparison.** A belief and a world fact conflict when
they share a `claim` and disagree on `value`. Under a reified chain, the
belief's claim sits at the end of a variable-length path and the query
needs a traversal before it can compare anything.

**Depth is a number, not a shape.** `size(holders)` distinguishes
first-order from second-order, so "skip second-order beliefs when detecting
world conflicts" is a predicate rather than a structural case analysis.
Arbitrary depth costs nothing.

**Attribution is a join, not a recursion.** `attributions()` matches
`holders = [a.holders[1]]` to find what the attributed agent actually
believes. Against a chain, that means walking down one belief and back up
another.

### What it costs

Two things are discarded outright, and both are currently invisible because
the corpus is uniform:

- **The attitude type.** Every `mental_state` carries `type: belief`, and
  all 96 in the corpus are `belief`. The loader writes the literal
  `perspective: "belief"` and never reads that field. A scenario using
  `type: knowledge` would be stored indistinguishably from belief — which
  matters, since knowledge implies truth and belief does not.
- **The outer predicate.** All 28 nested propositions use
  `predicate: believes`; only `subject` survives, as a holder. `doubts`,
  `hopes` or `knows` would be lost the same way.

So the flattening assumes every level of every chain is the same attitude.
`world.unfold` now refuses anything else: a mental state whose `type` is not
`belief`, or a nesting predicate that is not `believes`, raises rather than
being flattened wrongly. The assumption is enforced rather than merely
documented, and a scenario that outgrows the representation fails loudly at
load.

Beyond that, an attitude is not a node, so it cannot carry properties of
its own: no confidence on a belief, no provenance, no time. Anything about
the *holding* rather than the thing held has nowhere to go.

### When to reify instead

Any of these would force the change:

- more than one attitude type in use, or mixed types within a chain
- properties on the attitude itself — confidence, source, timestamp
- querying at an intermediate level, e.g. every belief Sam holds *about
  Alex* regardless of content

The first is the likely one, and it is the guard above that will announce
it: the moment a scenario uses `knowledge`, or an attitude other than
`believes` in a chain, loading it into the graph raises. That is the signal
to reify, and it will arrive as a failure rather than as wrong numbers.

## Episodic fact and background knowledge are separated

The graph holds two kinds of thing, and they are kept apart because they
change for different reasons.

**Episodic**, from a scenario's `world_state`: what is where, right now, in
this episode. Reified as propositions, scoped by scenario id.

**Background**, from `knowledge/goals.yaml`: what goals require, as standing
facts about the domain.

```
(:Goal {name})-[:REQUIRES {kind}]->(:Concept {name})

    present     the named entity must be at the place in question
    carried     the agent must be carrying it
    co_located  the goal's own argument must be at the place
```

Move the coffee and every scenario changes; the fact that making coffee
needs a mug does not. Scoped under a reserved name no scenario can use, so
it is shared across the corpus rather than repeated in it.

The split was not cosmetic. While `requires(coffee, mug)` sat in
`world_state`, the conflict rule was written against that predicate by name,
and so appeared to be about the word `requires` rather than about goals
having requirements at all. Separating them forced the general form: a goal
is satisfiable at a place when its requirements hold there, and a place is
accounted for when some goal in play is satisfiable. Neither step names a
predicate.

Generalising it immediately falsified a result. The narrow version had
reported six observation anomalies; asked properly, there are none, because
every observed walk in the corpus is accounted for by *some* goal — Sam's
walk to the coffee-less kitchen by washing the mug. The six had been an
artifact of following a single route from the carried object.

### Where the line falls

`world_state` should hold only what could differ between two episodes of the
same domain. Anything true of the domain itself belongs in the background,
and anything derivable from something already stated belongs in neither —
it should be derived.

This line was crossed once and the crossing is worth recording, because the
mistake was easy to make and looked like a fix.

The attribution scenarios were given a `located(<other agent>, …)` fact so
that the goal's target had a position and the conflict rule could apply to
them. It was wrong on three counts, in increasing seriousness.

It was **derived, not stated** — the agent's position follows from their own
belief, which the scenario already gives, so the same fact existed twice and
could drift.

It **reached the model**. `world_state` feeds `representation.sparse()`, so
this changed the stimulus rather than only what the analysis could compute.

And the derivation **is the thing under test**. Getting from *Alex believes
the meeting is in the garden* to *Alex is in the garden* uses "agents act on
their beliefs" — the very principle the experiment measures. Doing that
inference in the data and presenting the result as objective fact hands the
model the answer to the question being asked.

The motive was the worst part: the stimulus was changed so that a
measurement tool would apply to it. Attribution influence moved 0.69 to
0.48, and reverting restored it exactly, which shows the figure was a
consequence of the injected fact rather than a better-controlled reading.

So `accounted_for` reports NOT_APPLICABLE for the attribution and
second-order sets. Their worlds genuinely say nothing about where the person
being met is, and that should surface as "cannot tell" rather than be
papered over.

If the inference should be available at all, it belongs in background
knowledge as a rule — *an agent is where they believe their goal object
is* — so the graph derives it visibly at query time and it never touches
`world_state`. That keeps it out of the model's input, which was the actual
error. An agent's position is legitimate episodic fact when nothing derives
it: the discriminative set locates Alex, who holds no belief there, and that
is primitive rather than inferred.

## The epistemic history lives in the graph, and supersession is an edge

The graph held world state, stated beliefs, goals and observations. It did
not hold the history, so the one thing the history is for — working out
what an agent believes from what they saw — was done in Python and the
graph was only ever asked about conflicts.

It holds the history now. Each event is a `Settlement` carrying the order
it happened in, linked `SETTLES` to the proposition it settles and
`WITNESSED` to each agent who was there. The holder chain rides on the
`WITNESSED` edge: Sam watching Alex come to believe something stores
`holders: [sam, alex]`, which is the same shape `unfold` produces from a
stated second-order belief. An event about an attitude is an event like
any other, which is the parity the flattening already assumed.

### Two relations, because they are two different things

`SUPERSEDES` is temporal: the same claim settled again replaces what it
said before. Nothing about the predicate enters into it.

`EXCLUDES` is semantic and symmetric: two claims that cannot both hold. A
thing is in one place, so seeing the meeting in the office is seeing it not
in the conference room. There is no time in it at all.

Neither says anything about witnesses, and that is the point. The edges
say what the world is like; whether a particular agent's belief is *stale*
is then only the question of whether they witnessed the later event —
the edge exists and no `WITNESSED` edge reaches it. False belief stops
being a special case and becomes a missing edge.

Recency is applied in the query that asks what an agent currently holds,
not baked into either relation. A sighting still stands unless something
the same chain saw *later* either settled the same claim again or is
incompatible with it.

### Which predicates are exclusive is declared, not inferred

`located` is functional in its location; `available` is not. Coffee can be
in the kitchen and the pantry at once, so stocking it in one place says
nothing about the other, and stocking it elsewhere does not supersede a
belief about the kitchen — running out there does.

That distinction lived, until recently, in whether a proposition happened
to carry a location argument. Anything with one was treated as exclusive
in it, which made the algebra of a predicate an accident of its arguments
and meant a new predicate required editing Cypher rather than data.
`knowledge/predicates.yaml` declares it instead, beside what goals
require, and both the graph and the in-memory reference read the same
declaration rather than hardcoding the same guess twice.

No scenario in the corpus distinguished the two rules — `available`
claims either carry no location or sit in single-location scenarios — so
nothing measured was wrong. The rule was, and it was wrong in the
direction that would have quietly produced false beliefs the first time
somebody wrote a scenario with coffee in two rooms.

### Why it had to be an edge rather than an inference

It was implicit before, and that turned out to be a coupling rather than
an economy. A later sighting replaced an earlier one *because* exclusivity
said seeing the meeting in the office is seeing it not in the conference
room. So supersession was carried by exclusivity, and asking for the
beliefs without exclusivity left two sightings settling different keys,
neither replacing the other, and the agent believing the meeting was in
two places at once.

That is not a less explicit representation. It is a false one, and it
looked ordinary: each belief well-formed, the rendering unremarkable. It
only surfaced because a measurement was built on top of it and produced
sixteen regressions that were really the model reacting, correctly, to
being told an agent believed something impossible.

Separating the two makes them independently variable, which is what let
the stated and derived representations be decomposed at all. It also makes
a staleness question answerable by traversal: the later event an agent
missed is a path, not a re-derivation — and now a labelled one, so the
answer distinguishes having missed a correction from having missed
something incompatible.

### Materialising

`world.materialise` returns what an agent's access entails, as
`MentalState` with the holder chain folded back into nesting, so a
renderer cannot tell a derived belief from a stated one. One query, two
branches unioned: what the chain currently holds, and what a location
being exclusive implies about everywhere else. Both start from settlements
that nothing the chain also witnessed has superseded.

Results are written back under a `derived` perspective beside the `belief`
ones the file states, never over them, so the graph can always say which
beliefs it worked out and which it was told.

Restricting to one agent is not an optimisation. The history represents
the access of exactly one agent by construction, so asking for anyone
else's beliefs should return nothing rather than somebody else's.

### What this cost the in-memory reference

`analysis.entailed_beliefs` was wrong, and making supersession explicit is
what showed it. It applied exclusivity from every sighting a witness ever
had, including ones later overturned:

    history    1. located(registrar, ward) = True  [witnessed by Bijan]
               2. located(registrar, ward) = False [witnessed by Bijan]

    was        ward = False, theatre_desk = False, mess = False
    now        ward = False

Bijan saw the registrar on the ward — so not at the theatre desk — and
then saw them leave. The old rule kept the first sighting's exclusivity,
leaving him certain of two places he has no business being certain about.
Seven of a hundred scenarios were affected, and in
`ward_round_true_negative` the surplus would have ruled out two of the
three answers its own ground truth calls acceptable.

The graph was never missing anything the reference had rightly; the
reference only ever had extra. So the reference was changed to match, and
`tests/test_world.py` now holds the two to agreement on supersession
itself as well as on what it entails.
