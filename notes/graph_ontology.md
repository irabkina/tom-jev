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
