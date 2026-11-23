# Contributing

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
pytest
ruff check src tests scripts
ruff format --check src tests scripts
taskforge demo --output reports/demo
```

## Scope

Changes should keep one four-label task, one CPU specialist, and the pinned general-model trace. Hosted APIs, general-model training, and decisions about workers or facilities staff stay out.

## Fixtures

Text in `src/taskforge/data/` is original synthetic copy under the MIT license. Do not add a third-party corpus, a model weight file, or a real work order. After changing the generator, run `python scripts/generate_fixtures.py` and commit the new checksums in `manifest.json`. That refreshes recorded wall times.

## Reports

Money stays decimal strings. Quality and cost stay in separate sections of the report. A failed quality gate still prints the arithmetic and does not mark the specialist eligible.

## Secrets

Do not commit credentials, access tokens, or private traces.
