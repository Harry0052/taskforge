# TaskForge project contract

**Status:** Accepted for implementation after the P01 proceed decision in `docs/overlap.md`.  
**Access date:** 2026-11-23.

## User and task

Machine-learning engineers who own one recurring narrow text task and need an auditable answer to this question: does training a cheaper specialist beat staying on a pinned general model for a stated horizon?

The one task in this repository is **facilities work-order routing** with exactly these labels, in this order:

1. `custodial`
2. `electrical`
3. `hvac`
4. `plumbing`

The user loads synthetic requests (or a file in the same shape), trains one CPU specialist, scores it against a frozen general-model trace on the same evaluation ids, and reads a report that separates measured timings from analyst-supplied costs.

## Minimum dependencies

- Python 3.11 or newer (developed and verified on 3.12).
- NumPy and scikit-learn for the specialist.
- pytest for the automated checks.
- No paid API, no GPU, and no model download at demo time.

The general model in the MVP is a pinned local lexical generalist (`lexical-generalist` revision `1.0.0`). Its one recorded run is checked in. Hosted LLMs, general-model training, hardware purchasing, production routing, and decisions about workers or facilities staff are outside the contract.

## Measurable acceptance case

On the modeled cost fixture:

- additional specialist fixed cost = 60.00 USD
- baseline variable cost = 0.020 USD per request
- specialist variable cost = 0.005 USD per request
- quality gate passed

the report shows total-cost equality at **4,000** requests and the first strict specialist saving at **4,001**. Totals at 4,000 are 80.00 USD for both. Totals at 4,001 are 80.020 USD baseline and 80.005 USD specialist.

The same run reports specialist macro-F1 and per-class recall on the fixed evaluation set before it marks the specialist eligible. If quality fails, the arithmetic is still shown and the eligible recommendation is withheld.

Supporting checks that ship with the case:

- Reject a template family that appears in more than one split, a repeated id, a missing general-model result, and a label that is not in the four-label dictionary.
- A specialist with both a higher variable cost and a higher fixed cost has no favorable large-volume break-even.
- Changing the review price moves the crossover and leaves the already computed quality metrics unchanged.
- Timeouts and no-results remain in each label's support count.
- Money is decimal text, and the boundary is checked at the integer volumes on either side of a tie.

## Out of scope

- Training or downloading the general model during the demo.
- Cascade or router policies between several hosted models.
- Energy metering of a full AI platform (the Lunri boundary in the playbook).
- Any live facilities system, personal data, or credential.
