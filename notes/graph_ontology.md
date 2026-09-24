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
