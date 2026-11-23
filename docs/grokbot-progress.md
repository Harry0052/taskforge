# Grokbot progress

| Phase | Status |
| --- | --- |
| P01 | PASS |
| P02 | PASS |
| P03 | PASS |
| P04 | not started |
| P05 | not started |
| P06 | not started |
| P07 | not started |

## P01 — Research overlap and confirm the MVP

**Phase and status:** P01 PASS

**Files changed:**

- `docs/overlap.md`
- `docs/project-contract.md`
- `docs/probes/p01-shared-fixture.json`
- `docs/grokbot-progress.md`

**Commands and results:**

- GitHub repository metadata and default-branch commits, 2026-11-23:
  - `lm-sys/RouteLLM` Apache-2.0, commit `0b64fdafe049e596a3f5657c219329f24af24198`, pushed 2024-08-10. PyPI `routellm` 0.2.0.
  - `stanford-futuredata/FrugalGPT` Apache-2.0, commit `2b23e6acbd4b39f71912816640dcc59e45aa4b5e`, pushed 2025-02-10. PyPI names `frugalgpt` and `FrugalGPT` returned HTTP 404.
  - `B0yko/taskdistill` Apache-2.0, commit `3e803335cc9af45f82800c863bce4bf55040305d`, package 0.1.1. `pyproject.toml` marks macOS and pins `mlx` to Apple Silicon.
- Shared fixture probe (Python 3.12.3, Linux-6.12.113+-x86_64-with-glibc2.39). TaskForge decimal arithmetic: equality 4000, first strict saving 4001, totals 80.000 / 80.000 at 4000 and 80.020 / 80.005 at 4001. taskdistill's published `ceil(exact - 1e-9)` mapping returns 4000 and does not name 4001. RouteLLM and FrugalGPT were not given API keys; their documented inputs cannot accept the fixture. Evidence classes are recorded in `docs/probes/p01-shared-fixture.json`.
- Repository search for `lunri` returned no GitHub repository. No URL invented.

**Artifact paths:**

- `docs/overlap.md`
- `docs/project-contract.md`
- `docs/probes/p01-shared-fixture.json`

**Open issues:**

- The MVP general model is a pinned local lexical generalist, not a downloaded LLM. Substituting a redistributable neural trace needs a separate license review and is not required for the acceptance case.
- Dollar costs stay analyst-supplied. Wall-clock measurements are stored beside them.

**Next phase:** P02

## P02 — Create the repository and data contracts

**Phase and status:** P02 PASS

**Files changed:**

- `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, `README.md`, `.gitignore`
- `src/taskforge/` package, validator, pinned generalist, JSON Schemas, synthetic fixtures, manifest
- `scripts/generate_fixtures.py`
- `tests/test_validate.py`
- `docs/oracle/arithmetic.md`, `docs/oracle/validation.md`

**Commands and results:**

- `python3 scripts/generate_fixtures.py` wrote 86 requests (48 train, 16 validation, 22 evaluation) and one local `lexical-generalist` 1.0.0 trace. Recorded host `Linux x86_64 3.12.3`, wall time 0.122 ms, status counts abstain 8, scored 12, timeout 1, no_result 1, scored label matches 10. Seed 17001.
- `taskforge validate --dataset src/taskforge/data/dataset.json --trace src/taskforge/data/general_trace.json --costs src/taskforge/data/costs/demo.json` exited 0 with `"status": "valid"`, 86 items, 22 trace rows, profile `demo-modeled`.
- `taskforge validate --dataset src/taskforge/data/invalid/leaked_family.json` exited 2: `template_family_leak: template_family 'hvac-shared-family' appears in splits train and evaluation.`
- The same entry point also rejected repeated ids, a mixed label dictionary, a missing general-model row, schema 9.9.9, a 2001-character text, and a JSON number used as money.
- `python3 -m pytest -q`: 13 passed. `ruff check` and `ruff format --check` passed. Installed pins: numpy 2.2.6, scipy 1.18.1, scikit-learn 1.9.1, joblib 1.6.0, threadpoolctl 3.8.0, pytest 8.4.2, ruff 0.14.6.

**Artifact paths:**

- `src/taskforge/data/dataset.json`
- `src/taskforge/data/general_trace.json`
- `src/taskforge/data/manifest.json`
- `src/taskforge/data/costs/`
- `src/taskforge/data/schemas/`
- `docs/oracle/arithmetic.md`
- `docs/oracle/validation.md`

**Open issues:**

- Scoring, training, and the 4,000 / 4,001 report are not implemented yet. The oracle states the expected totals.
- Regenerating the trace changes host wall times. Tests lock the checked-in checksums.

**Next phase:** P03

## P03 — Build the working core

**Phase and status:** P03 PASS

**Files changed:**

- `src/taskforge/score.py`, `cost.py`, `train.py`, `analyze.py`, `report.py`
- `src/taskforge/cli.py` (`analyze` command)
- `tests/test_score.py`, `tests/test_cost.py`, `tests/test_analyze.py`

**Commands and results:**

- `taskforge analyze --dataset src/taskforge/data/dataset.json --trace src/taskforge/data/general_trace.json --costs src/taskforge/data/costs/demo.json --output /tmp/taskforge-p03` exited 0. Summary: eligible true, quality gate passed, specialist macro-F1 0.808042, equality at 4000, first strict saving at 4001. Report `/tmp/taskforge-p03/report.json`.
- Per-class specialist recall on the locked 22-id set: custodial 0.600000 (support 5), electrical 1.000000 (support 5), hvac 1.000000 (support 6), plumbing 0.666667 (support 6). General trace keeps 1 timeout and 1 no-result inside the denominator.
- Unfavorable profile (variable 0.030 vs 0.020, fixed 90 vs 10) returns `no_favorable_large_volume_break_even` with eligibility false while quality still passes.
- Review prices 0.1000 and 0.5000 change the first strict-saving request and keep the same frozen macro-F1.
- A gate of macro-F1 0.9900 still reports 4000 / 4001 and withholds eligibility.
- `pytest`: 22 passed. Ruff check and format check passed.

**Artifact paths:**

- `/tmp/taskforge-p03/report.json`
- `/tmp/taskforge-p03/report.md`
- `/tmp/taskforge-p03/specialist-export.json`

**Open issues:**

- `taskforge demo` is not wired yet. `analyze` is the public path for this phase.
- Specialist training time is host-specific and is not part of the cost arithmetic.

**Next phase:** P04
