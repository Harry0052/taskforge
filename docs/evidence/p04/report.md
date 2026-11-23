# TaskForge report

Task `facilities-work-order-routing`, profile `demo-modeled`.
Currency USD. Horizon: 12 months. Forecast volume: 10000 requests.

## Decision

Eligible recommendation: **True**.

Quality passed. Forecast volume 10000 is at or beyond the first strict saving at request 4001.

Quality gate passed: True (specialist macro-F1 0.808042, minimum per-class recall 0.600000; required macro-F1 0.7500 and recall 0.5000).

Cost outcome: `finite_crossover`. Totals are equal at 4000 requests. The first strict specialist saving is request 4001.

## Quality

Recorded on the locked evaluation ids. Support includes abstentions, timeouts, and no-results.

| Label | Support | Specialist recall | General recall |
| --- | ---: | ---: | ---: |
| custodial | 5 | 0.600000 | 0.400000 |
| electrical | 5 | 1.000000 | 0.400000 |
| hvac | 6 | 1.000000 | 0.333333 |
| plumbing | 6 | 0.666667 | 0.666667 |

Specialist macro-F1: 0.808042. Abstentions 0, timeouts 0, no-results 0.
General macro-F1: 0.577381. Abstentions 8, timeouts 1, no-results 1.
Specialist confidence cutoff 0.0 was frozen on validation (validation macro-F1 0.753175).

## Costs

Analyst-supplied. These dollars are not derived from the wall times in the next section.

Baseline fixed 0.0000 (labeling 0.0000, training 0.0000, integration 0.0000). Variable per request 0.0200.
Specialist fixed 60.0000 (labeling 40.0000, training 5.0000, integration 15.0000). Variable per request 0.0050.
Variable cost mode: `modeled`.

At 4000 requests the totals are equal: baseline 80, specialist 80.
At 4001 requests the specialist total is 80.005 and the baseline total is 80.02 (difference -0.015).

## Review-cost sensitivity

Quality figures stay at the frozen macro-F1.

- Review price 0.1000 (analyst-supplied review price; observed review rates; quality frozen): outcome `finite_crossover`, first strict saving 993, frozen macro-F1 0.808042.
- Review price 0.5000 (analyst-supplied review price; observed review rates; quality frozen): outcome `finite_crossover`, first strict saving 248, frozen macro-F1 0.808042.

## Recorded timings

General-model trace wall time 0.122 ms on Linux x86_64 3.12.3.
Specialist training 7.477 ms and evaluation scoring 0.559 ms on Linux x86_64 3.12.3.
These measurements are not prices.

## Traced example

Item `wo-evalu-hvac-condensate-leak-01` (hvac-condensate-leak) gold `hvac`.
Text: Condensate leak under the air handler by the east stair.
Specialist: scored / hvac. General model: scored / plumbing.
Find this item_id in the dataset file recorded under inputs.dataset.

## Limitations

- One four-label synthetic task. Results do not transfer to other label sets.
- The general model is the pinned lexical-generalist trace, not a hosted LLM.
- Cost dollars are analyst-supplied assumptions for the stated horizon.
- A passing quality gate is required before the specialist is marked eligible.
- The linear export is for inspection. This run retrained the specialist and did not load it.
