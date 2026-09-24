# tom-jev

Jev is designed as a System One model: a model for fast, probabilistic decisions rather than extended sequential reasoning. This project investigates whether richer reasoning behavior can instead emerge from an architecture that iteratively changes the representations over which Jev makes decisions.

The project applies this idea to Theory of Mind (ToM) reasoning. It compares sparse representations containing observable actions and world state with richer representations that explicitly encode agents' beliefs and knowledge. It then tests strategies for selectively triggering re-representation when an initial decision is uncertain or conflicts with available evidence.

The approach is inspired by Rabkina & McFate's[^1] proposal that automatic and effortful Theory of Mind need not require separate reasoning mechanisms. Instead, a single reasoning process can operate over increasingly rich representations, with conflict triggering effortful re-representation.

## Experimental Conditions

1. **Sparse / Never**                      
   Observable actions and world state only. No re-representation.

2. **Rich / Always**
   Explicit mental-state representations are available initially.

3. **Iterative / Uncertainty**
   Begin with a sparse representation; re-represent when decision confidence is low.

4. **Iterative / Conflict**
   Begin with a sparse representation; re-represent when an inferred outcome conflicts with the represented world state.

## Status

Early-stage research prototype.

[^1]: Rabkina, I., & McFate, C. (2023). *Should Agents Have Two Systems to Track Beliefs and Belief-Like States?* In N. Gurney, S. Marathe, S. K. Bhamidipati, M. K. Dorneich, & C. Lebiere (Eds.), *Computational Theory of Mind for Human-Machine Teams* (pp. 149–157). Springer. https://doi.org/10.1007/978-3-031-21671-8_9


## Layout

| Path | Contents |
|---|---|
| `src/tom_jev/` | The package. `models` (data), `jev` (scoring), `graph` (structure), `representation` (renderings + re-representation) |
| `scenarios/` | Scenario definitions, one JSON file each — see `scenarios/README.md` |
| `experiments/` | Runnable studies; each writes to `results/` |
| `results/` | Experiment output (gitignored except `.gitkeep`) |
| `tests/` | Test suite |

## Setup

Requires Python 3.10+.

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env   # then fill in your key
```

## Running

```bash
python experiments/01_sparse_vs_rich.py
python experiments/02_rerepresentation.py
pytest
```

## Status

Scaffolding. The pieces marked `TODO` are the real work:

- `jev.evaluate` — the JEV scoring formulation
- `representation.rerepresent` — the re-representation transform
- the model call in both experiment scripts

## License

MIT — see [LICENSE](LICENSE).
