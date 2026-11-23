# TaskForge

TaskForge tells a machine-learning engineer whether a small CPU classifier beats a pinned general model on one narrow task, and at which request volume the specialist's total cost becomes strictly lower.

The task is facilities work-order routing with four labels: `custodial`, `electrical`, `hvac`, and `plumbing`. The specialist is a TF-IDF logistic regression trained locally. The general model is `lexical-generalist` revision `1.0.0`. One local run is stored in the repository, so the demo does not download weights or call a paid API.

Measured wall times and analyst-supplied dollar costs are reported in separate sections. The dollar result applies only to the horizon and the prices in the selected profile.

## Supported toolchain

- CPython 3.11 or newer. Commands below were run on Linux x86_64 with CPython 3.12.3.
- Packages pinned in `requirements.txt` (runtime) and `requirements-dev.txt` (tests and formatting).
- No GPU, no paid API, and no extra hardware demo.

## Clean install

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
```

Runtime only, without pytest or ruff:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -e . --no-deps
```

`--no-deps` keeps those pins. On Windows, activate `.venv\Scripts\activate` instead of `source`.

## Demo

```bash
taskforge demo
```

The command trains the specialist, aligns predictions with the frozen trace, and writes:

| File | What it is |
| --- | --- |
| `reports/demo/report.md` | Human summary |
| `reports/demo/report.json` | Same figures, output schema 1.0.0 |
| `reports/demo/specialist-export.json` | Coefficient inspection file. The next run retrains and does not load it. |

Stdout is a JSON summary. Stderr prints the path to the human report. Exit 0 means the run finished. `eligible` can still be false when the quality gate fails or the forecast volume is before the crossover.

**Expected result** for the shipped modeled profile (extra fixed cost 60.00 USD, baseline 0.020 USD per request, specialist 0.005 USD per request, quality gate passed):

- equality at **4,000** requests (both totals 80.00 USD)
- first strict specialist saving at **4,001** (baseline 80.020 USD, specialist 80.005 USD)
- specialist macro-F1 about **0.808** and minimum per-class recall **0.60**, above the gate of 0.75 and 0.50

A copy of one such run is in `docs/evidence/p04/`. Training milliseconds in that file are from the machine that recorded it.

Your own files, in the same shapes:

```bash
taskforge demo \
  --dataset path/to/dataset.json \
  --trace path/to/trace.json \
  --costs path/to/costs.json \
  --output reports/mine
```

`taskforge analyze` is the same computation with required paths. `taskforge validate` checks a file without training.

A bad file exits 2, writes no report, and prints a code plus a fix. Example:

```bash
taskforge demo --dataset src/taskforge/data/invalid/leaked_family.json
```

`taskforge --help` and `taskforge demo --help` list the flags.

## Tests

```bash
pytest
ruff check src tests scripts
ruff format --check src tests scripts
```

## Data

Files under `src/taskforge/data/` are original synthetic requests and analyst-supplied cost profiles written for this repository (MIT). Checksums and seed `17001` are in `src/taskforge/data/manifest.json`. No third-party corpus or model weights are included. Regenerating with `python scripts/generate_fixtures.py` records a new host and new wall times.

Other cost profiles in `src/taskforge/data/costs/`:

| Profile | What it shows |
| --- | --- |
| `low_volume.json` | Same prices, forecast 500, which is before the first saving |
| `high_volume.json` | Same prices, forecast 20,000 |
| `high_review.json` | Variable cost from observed review rate times a 2.00 USD review price |
| `unfavorable.json` | Specialist is more expensive per request and has a higher fixed cost, so there is no favorable large-volume break-even |

## License and notices

MIT. See `LICENSE`. Third-party package licenses are listed in `THIRD_PARTY_NOTICES.md`. Version history is in `CHANGELOG.md`. Contribution steps are in `CONTRIBUTING.md`. Vulnerability reports use GitHub private reporting; see `SECURITY.md`.
