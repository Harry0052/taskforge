# Validation

**Date:** 2026-11-23  
**Host:** Linux 6.12.113+ x86_64, glibc 2.39, Python 3.12.3, GCC 13.3.0  
**Scope:** synthetic TaskForge fixture only. No external labeled dataset and no hosted model.

## Acceptance evidence

| Check | Tolerance | Result |
| --- | --- | --- |
| Modeled totals tie at 4,000 requests and the specialist is strictly cheaper at 4,001 | Exact `Decimal` equality. Display drops trailing zeros. | Observed. Baseline and specialist totals are 80 at 4,000. At 4,001 they are 80.020 and 80.005. |
| Specialist macro-F1 and per-class recall on the locked 22-id evaluation set before eligibility | Gate is macro-F1 ≥ 0.7500 and every class recall ≥ 0.5000. Figures are reported to 6 decimal places. | Macro-F1 0.808042. Recalls: custodial 0.600000 (support 5), electrical 1.000000 (support 5), hvac 1.000000 (support 6), plumbing 0.666667 (support 6). Eligible on the demo profile. |
| Timeouts and no-results stay in the denominator | Support equals the gold count, including non-scored rows. | General trace: 22 evaluated rows, 8 abstentions, 1 timeout, 1 no-result. Hand oracle of four rows has macro-F1 0.500000 with support 1 per label. |
| Higher variable cost and higher fixed cost | No integer volume is reported. | Unfavorable profile outcome `no_favorable_large_volume_break_even`. Quality still passes and eligibility is false. |
| Review price changes the crossover; quality stays frozen | The two sensitivity rows must differ, and both repeat the same macro-F1 string. | Review 0.1000 first saves at request 993. Review 0.5000 first saves at request 248. Frozen macro-F1 0.808042 both times. A separate hand case moves 10,000 / 10,001 to no large-volume break-even when the review price goes from 0.10 to 0.50. |
| Non-integer ratio | First strict saving is the ceiling, and the previous integer is not a strict saving. | Fixed 60 and variable saving 0.007 → request 8572. The integer check inside `solve_crossover` enforces the boundary. |
| Failed quality gate | Arithmetic remains, eligibility does not. | Gate 0.9900 still reports 4000 / 4001 and `eligible: false`. |
| Leaked template family, repeated id, mixed labels, missing general-model row | Rejected before a report, exit 2, code on stderr. | Observed for each fixture in `docs/oracle/validation.md`. |
| Decimal money | JSON numbers and more than 4 decimal places are rejected. | `float_money.json` returns `money_type`. |

These quality numbers describe the synthetic fixture and this pinned scikit-learn 1.9.1 fit. They are not a claim about a production facilities queue.

## Performance

Budget for `taskforge demo` on the shipped fixture: **15 seconds** wall time. The fixture directory is 47,953 bytes.

| Run | Wall time | Decision |
| --- | ---: | --- |
| Fresh process, `/tmp/taskforge-p05-fresh` | 0.94 s including interpreter startup; 0.025 s inside the already imported process | eligible, 4000 / 4001, macro-F1 0.808042 |
| `pytest` (35 tests, includes demo and analyze) | 0.95 s | passed |

Training time on this host for the evidence report was 7.477 ms. That number is a measurement, not a price. Another machine will differ.

## Trust boundaries

- Inputs are UTF-8 JSON objects. Files larger than 1,500,000 bytes, texts longer than 2,000 characters, and more than 5,000 rows are rejected.
- Money is a decimal string. The parser does not accept JSON numbers.
- Trace labels must be in the four-label dictionary. Schema version must be `1.0.0` for the dataset, the trace, and the cost profile. Unknown versions are rejected.
- Template families cannot appear in two splits. Evaluation ids and trace ids must match exactly.
- The specialist is retrained from the fixture. `specialist-export.json` is coefficients only. The program does not call `pickle` or `joblib.load`.
- Reports are written only as `report.json`, `report.md`, and `specialist-export.json` inside the chosen directory. A path that is already a file returns `output_path` and exit 2, and the file is left unchanged.
- No child process is started from input text. The demo does not open a network connection and does not read a secret.
- There is no native extension in this repository, so there is no address-sanitizer job.

## Dependencies

OSV (`https://api.osv.dev/v1/query`) on 2026-11-23:

| Package | Version | License | Advisories |
| --- | --- | --- | --- |
| numpy | 2.2.6 | BSD-3-Clause | 0 |
| scipy | 1.18.1 | BSD-3-Clause | 0 |
| scikit-learn | 1.9.1 | BSD-3-Clause | 0 |
| joblib | 1.6.0 | BSD-3-Clause | 0 |
| threadpoolctl | 3.8.0 | BSD-3-Clause | 0 |
| ruff | 0.14.6 | MIT | 0 |
| pytest | 9.2.0 | MIT | 0 |

pytest 8.4.2 reported GHSA-6w46-j5rx-g56g / PYSEC-2026-1845 (predictable `/tmp/pytest-of-{user}` directories, fixed in 9.0.3). The pin was moved to 9.2.0 and the query returned no remaining advisory. `pip-audit` could not build its own virtual environment because `python3-venv` is not installed; the OSV query above is the check that ran.

`python -m compileall` succeeded for `src`, `tests`, and `scripts`. `ruff check` and `ruff format --check` passed. There is no separate type-checker step.

## Residual limitations

- The general model is the pinned lexical trace, not a neural network. Its wall time is too small to represent a hosted model.
- Dollar inputs are assumptions. Editing them is how an analyst changes the crossover.
- Macro-F1 can move by small amounts if the scikit-learn pin changes. The gate, not a single bit-exact float, is the eligibility rule.
- The cost result applies only to the horizon and the prices in the selected profile.
