# Grokbot progress

| Phase | Status |
| --- | --- |
| P01 | PASS |
| P02 | not started |
| P03 | not started |
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
