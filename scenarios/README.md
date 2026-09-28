# Scenarios

- **`schema.yaml`** — the authoritative field reference, with every field
  documented inline, including the two rules a `history` must satisfy.
- **`action_prediction/first_order/report/`** — a complete worked 2x2, and
  the set to copy from.

No example is reproduced here: it would be a further place to keep in sync,
and it silently went stale the last time the schema changed. The scenario
files are loaded by the test suite and the experiments, so they cannot drift
without something failing.

## What goes into a representation

| Section | sparse | history | rich |
|---|---|---|---|
| `observations` — observable events before the target action | yes | yes | yes |
| `world_state` — what is objectively true | yes | yes | yes |
| `goals` — goals attributed to agents, given rather than inferred | yes | yes | yes |
| `history` — how the agent came to believe what they believe | **no** | yes | **no** |
| `mental_state` — what agents believe | **no** | **no** | yes |
| `description`, `ground_truth`, `annotations` — researcher metadata | never | never | never |

`sparse` and `rich` differ by exactly `mental_state`. An agent's belief may
contradict `world_state`; that divergence is the manipulation, so never
infer `mental_state` from `world_state` when building a representation.

`history` and `mental_state` are two presentations of the same belief — the
history must *entail* what the mental state *asserts*, without asserting it.
A corpus test recovers the belief from the events and holds the two to
agreement, so the two conditions differ in explicitness and not in content.

`representation.py` is what enforces the exclusions, in one place, so no
caller can leak an answer into the model input.
`tests/test_representation.py` checks that matched variants render
identically under sparse and differently under rich.

## Where a file goes

The directory path *is* the taxonomy, and it is the only source of truth
for it:

    scenarios/<task_family>/<template>/<domain>/<condition>/<lexicalization>.yaml

| level | what it varies | values |
|---|---|---|
| `task_family` | what Jev is asked | `action_prediction`, `goal_recognition` |
| `template` | the belief structure | `first_order`, `second_order`, `attribution`, `discriminative` |
| `domain` | surface content only | `bakery`, `clinic`, `workshop`, … |
| `condition` | the cell of the template's 2x2 | see below |
| `lexicalization` | wording of the same cell | `v1`, `v2`, … |

A scenario file therefore carries only its content; the loader fills the
taxonomy in from where the file sits. Moving a file reclassifies it, and a
file cannot disagree with its own directory.

Conditions are named per template, because "F" means different things in
different 2x2s:

| template | axes | conditions |
|---|---|---|
| `first_order`, `second_order` | world supports the action × agent believes it does | `true_positive`, `false_positive`, `false_negative`, `true_negative` |
| `attribution` | Sam's attribution matches Alex's belief × Alex's belief matches the world | `true_attribution_true_belief`, … |
| `discriminative` | each of the agent's two beliefs matches the world or not | `true_true`, `true_false`, `false_true`, `false_false` |

`scenario_set` and `variant.type` remain in the file as well. They are
carried through into results and used by the tests, and must agree with the
path — the path is what the loader reads.

## File format

Named `<name>.yaml` or `<name>.yml`. A file holds either a single scenario,
or several under a top-level `scenarios:` key:

```yaml
scenarios:
  - id: first
    # ...
  - id: second
    # ...
```

The loader skips `schema.yaml` and `README.md`, and anything starting with
`_`. It rejects duplicate scenario ids across files, since two scenarios
sharing one would silently collapse together in analysis.

## Conventions

Optional arguments may be omitted rather than written as `null`.

Long free text reads better as a block scalar — `>` folds lines into one,
`|` preserves the newlines:

```yaml
description: >
  Sam wants coffee. Sam does not have a cup. Coffee and cups are
  available in the kitchen.
```

New items should prefer three options to two: with two, TV influence
reduces exactly to `abs(utility)` and the two measures carry identical
information.

Two scripts maintain the corpus rather than replacing hand-authoring:
`scripts/generate_scenarios.py` writes a domain's four cells from a compact
spec so the 2x2 cannot drift between domains, and
`scripts/add_histories.py` derives the `history` block from the stated
beliefs. Neither overwrites a file that already exists.
