# tom-jev

Re-representation experiments over JEV scenarios.

## Layout

| Path | Contents |
|---|---|
| `src/jev_rerepresentation/` | The package. `models` (data), `jev` (scoring), `graph` (structure), `representation` (renderings + re-representation) |
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
