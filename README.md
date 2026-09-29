# tom-jev

Jev is designed as a System One model: a model for fast, probabilistic decisions rather than extended sequential reasoning. This project investigates whether richer reasoning behavior can instead emerge from an architecture that iteratively changes the representations over which Jev makes decisions.

The project applies this idea to Theory of Mind (ToM) reasoning. It compares sparse representations containing observable actions and world state with richer representations that explicitly encode agents' beliefs and knowledge. It then tests strategies for selectively triggering re-representation when an initial decision is uncertain or conflicts with available evidence.

The approach is inspired by Rabkina & McFate's[^1] proposal that automatic and effortful Theory of Mind need not require separate reasoning mechanisms. Instead, a single reasoning process can operate over increasingly rich representations, with conflict triggering effortful re-representation.

## Representations

Three renderings of one scenario, differing in what they say about the
agent's mind and in nothing else. `representation.py` is what enforces
that, in one place, so no caller can leak an answer into the model input.

| condition | state sections | the question it answers |
|---|---|---|
| `sparse` | `observations`, `world_state`, `goals` | what does Jev predict from the limited representation? |
| `history` | + `history` | is the evidence a belief *follows from* enough on its own? |
| `rich` | + `mental_state` | what changes once the belief is stated outright? |

The middle condition splits what `sparse` lacks into two things — the
information, and the information made explicit. A history says how an
agent came to believe something instead of asserting it: they were present
when a claim was settled one way, and absent when it was settled another.
So `history` and `rich` carry the same belief and differ only in whether
it is spelled out. A corpus test holds them to that: `analysis.entailed_beliefs`
recovers the belief from the events independently and must agree with the
stated `mental_state`.

A fourth rendering, `history_symbolic`, writes the same events in the
notation the rest of the state uses. It is a robustness check rather than
a condition, and it exists because the choice of surface form turns out to
move the result — see *Unresolved: the history's surface form moves the
result* in `notes/experimental_design.md`.

## Escalation policies

The original design named four conditions: never re-represent, always,
escalate on low confidence, escalate on world conflict. The first two are
`sparse` and `rich`. The second two are not implemented, and the
measurements have since made their prospects concrete rather than
hypothetical — no signal computable from the sparse pass reliably
identifies where re-representation will help. Confidence, entropy,
objective-world conflict, the model's own answer being ruled out, and the
dependency structure of its derivation were each tested and each failed.

That is close to a consequence of the design, since the manipulation *is*
withholding the deciding information, and it leaves the policy question as
one about cost rather than detection. See *Sparse-state signals do not
reliably identify the need for re-representation*.

## Corpus

68 scenarios, all under the `dev` split. The directory path is the
taxonomy and the only source of truth for it:

    scenarios/<split>/<task_family>/<template>/<domain>/<condition>/<lexicalization>.yaml

| task family | template | domains | n |
|---|---|---|---|
| `action_prediction` | `first_order` | bakery, lighthouse, report | 12 |
| `action_prediction` | `second_order` | ferry (×2 lexicalizations), gallery, meeting | 16 |
| `action_prediction` | `attribution` | meeting_rooms, newsroom, observatory | 12 |
| `goal_recognition` | `first_order` | coffee, darkroom, greenhouse | 12 |
| `goal_recognition` | `discriminative` | clinic, mailroom, station, workshop | 16 |

`scenarios/test/` is the held-out split: 32 scenarios crossing task family
with what the richer representation does — names an alternative, or only
denies one. The escalation policy it tests was fixed before it was built.
Nothing there has been run against the model. See
`notes/held_out_corpus.md`.

See `scenarios/README.md` for the file format and `scenarios/schema.yaml`
for the fields.

## Findings

Kept in `notes/`, newest understanding first, rather than summarised here
where they would go stale.

| note | contents |
|---|---|
| `notes/experimental_design.md` | what has been measured and what it supports, with the caveats each result carries |
| `notes/representation.md` | what Jev is shown, where each part comes from, and which of those choices were measured |
| `notes/held_out_corpus.md` | the held-out split: how it was built, what was checked, and the two design faults review found |
| `notes/open_questions.md` | what is not settled — what a write-up should not claim, and what a reader would be right to ask |
| `notes/future_scenarios.md` | gaps in the corpus, and which of them are worth building |
| `notes/graph_ontology.md` | how the graph represents nested attitudes, and where episodic fact ends and background knowledge begins |

The one result measured out of sample is *The policy replicates out of
sample, and the free prior does not*: an escalation policy fixed before the
held-out corpus existed recovers 81% of the available gain on 62% of the
calls, where the heuristic that beat it in development falls from 87% to
57%. Everything else in that note was measured on the corpus it was
selected on and is labelled accordingly.

Two notes are methodological and outlive any particular number: *Not
tuning stimuli to results* records which parts of the corpus were revised
against their own measurements and are therefore not independent evidence,
and *Where the line falls* records the one time a derived fact was written
into `world_state` and reached the model.

## Layout

| Path | Contents |
|---|---|
| `src/tom_jev/` | The package — see below |
| `scenarios/` | Scenario definitions, one YAML file per cell — see `scenarios/README.md` |
| `knowledge/goals.yaml` | Background knowledge: what each goal requires. Shared across the corpus rather than repeated in it |
| `experiments/` | Runnable studies; each writes to `results/` |
| `scripts/` | Corpus maintenance — `generate_scenarios.py`, `add_histories.py`, `make_test_corpus.py` |
| `notes/` | Findings, backlog, and representational commitments |
| `results/` | Experiment output. The runs behind the notes are committed as a record, so every table can be rechecked without spending calls; new output is still ignored by default |
| `tests/` | Test suite, including the corpus invariants |

Inside the package:

| Module | Responsibility |
|---|---|
| `models` | The scenario schema as pydantic models |
| `scenarios` | Loading, and reading the taxonomy off the path |
| `representation` | The renderings, and the exclusion of researcher metadata from all of them |
| `jev` | Calling the model and parsing what comes back |
| `world` | Loading scenarios into Neo4j, and the queries only the graph can answer |
| `graph` | Structural checks over matched scenario sets |
| `analysis` | The five measures, and the comparison between two passes |

## Setup

Requires Python 3.10+.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in your key
```

Neo4j is optional. `experiments/01` queries it for world conflict,
attribution conflict and the escalation trigger; without it, the first two
fall back to in-memory equivalents and the third comes back empty.

## Running

```bash
python experiments/01_sparse_vs_rich.py    # 3 passes x 68 scenarios = 204 model calls
pytest
```

`experiments/01` writes every prediction to `results/01_sparse_vs_rich.json`
and one comparison file per pairing —
`01_{sparse_vs_rich,sparse_vs_history,history_vs_rich}_comparisons.json`.

## Status

Active research pilot. The representations, the corpus, the measures and
the graph are in place; `experiments/01` runs end to end.

What remains:

- `representation.rerepresent` — the re-representation transform itself
- `experiments/02_rerepresentation.py` — blocked on the above
- the two iterative conditions, which need a policy the measurements do
  not yet support

## License

MIT — see [LICENSE](LICENSE).

[^1]: Rabkina, I., & McFate, C. (2023). *Should Agents Have Two Systems to Track Beliefs and Belief-Like States?* In N. Gurney, S. Marathe, S. K. Bhamidipati, M. K. Dorneich, & C. Lebiere (Eds.), *Computational Theory of Mind for Human-Machine Teams* (pp. 149–157). Springer. https://doi.org/10.1007/978-3-031-21671-8_9
