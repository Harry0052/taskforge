# TaskForge

TaskForge compares one CPU specialist with a pinned general model on a four-label facilities work-order task. It reports macro-F1, per-class recall, and the request volume where the specialist's total cost becomes strictly lower. Measured timings stay separate from analyst-supplied costs.

The general model in this repository is `lexical-generalist` revision `1.0.0`. One local run is stored in `src/taskforge/data/general_trace.json`. The demo reads that trace and does not download weights or call a paid API.

## Setup

Python 3.11 or newer. These commands were checked on Python 3.12.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
```

`--no-deps` keeps the pins in `requirements.txt`. Runtime only:

```bash
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

## Validate the shipped fixture

```bash
taskforge validate \
  --dataset src/taskforge/data/dataset.json \
  --trace src/taskforge/data/general_trace.json \
  --costs src/taskforge/data/costs/demo.json
```

A valid bundle prints JSON with `"status": "valid"` and exits 0. Rejected inputs print `code: message` on stderr and exit 2. The expected codes are in `docs/oracle/validation.md`. The hand-calculated cost totals are in `docs/oracle/arithmetic.md`.

```bash
taskforge validate --dataset src/taskforge/data/invalid/leaked_family.json
```

## Tests

```bash
pytest
```

## Data

Fixtures under `src/taskforge/data/` are original synthetic requests written for this repository (MIT). Checksums and the generator seed are in `src/taskforge/data/manifest.json`. Regenerating the trace with `python scripts/generate_fixtures.py` records a new host and new wall times; the checked-in trace is the one the tests lock.

## License

MIT. See `LICENSE`.
