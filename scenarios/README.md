# Scenarios

- **`schema.yaml`** — the authoritative field reference, with every field
  documented inline.
- **`coffee_TP.yaml`, `coffee_FP.yaml`, `coffee_FN.yaml`, `coffee_TN.yaml`** —
  a complete worked scenario set, and the examples to copy from.

No example is reproduced here: it would be a fourth place to keep in sync,
and it silently went stale the last time the schema changed. The scenario
files are loaded by the test suite and the experiments, so they cannot drift
without something failing.

## What goes into a representation

| Section | sparse | rich |
|---|---|---|
| `observations` — observable events before the target action | yes | yes |
| `world_state` — what is objectively true | yes | yes |
| `goals` — goals attributed to agents, given rather than inferred | yes | yes |
| `mental_state` — what agents believe | **no** | yes |
| `description`, `ground_truth`, `annotations` — researcher metadata | never | never |

The sparse/rich difference is exactly `mental_state` and nothing else. An
agent's belief may contradict `world_state`; that divergence is the
manipulation, so never infer `mental_state` from `world_state` when
building a representation.

`representation.py` is what enforces the exclusions, in one place, so no
caller can leak an answer into the model input. `tests/test_representation.py`
checks that matched variants render identically under sparse and differently
under rich.

## Files

Named `<name>.yaml` or `<name>.yml`. A file holds either a single scenario,
or several under a top-level `scenarios:` key:

```yaml
scenarios:
  - id: first
    # ...
  - id: second
    # ...
```

The loader skips `schema.yaml` and anything starting with `_`, and rejects
duplicate scenario ids across files.

Variants of one matched set share a `scenario_set` and differ in `variant.type`
— the coffee set uses `true_positive`, `false_positive`, `false_negative`,
`true_negative`, the 2x2 of whether the world supports the action and whether
the agent believes it does.

## Conventions

Optional arguments may be omitted rather than written as `null`.

Long free text reads better as a block scalar — `>` folds lines into one,
`|` preserves the newlines:

```yaml
description: >
  Sam wants coffee. Sam does not have a cup. Coffee and cups are
  available in the kitchen.
```
