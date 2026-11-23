# Arithmetic oracle

Hand calculation for the modeled demo profile. These totals do not use measured wall time. Currency is USD. Amounts are decimal, not binary floats.

## Inputs

| Quantity | Baseline | Specialist |
| --- | ---: | ---: |
| Fixed cost | 0.00 | 60.00 |
| Variable cost per request | 0.020 | 0.005 |

Additional specialist fixed cost = 60.00 − 0.00 = 60.00.

Per-request saving = 0.020 − 0.005 = 0.015.

## Equality

Set the totals equal:

```
0.020 n = 60.00 + 0.005 n
0.015 n = 60.00
n = 60.00 / 0.015 = 4000
```

4000 is an integer, so the totals tie at 4,000 requests.

| Volume | Baseline total | Specialist total | Relation |
| ---: | ---: | ---: | --- |
| 4,000 | 0.020 × 4000 = 80.000 | 60.00 + 0.005 × 4000 = 80.000 | equal |
| 4,001 | 0.020 × 4001 = 80.020 | 60.00 + 0.005 × 4001 = 80.005 | specialist is 0.015 lower |

The first strict specialist saving is request **4,001**.

## No favorable large-volume break-even

Unfavorable profile, same method:

| Quantity | Baseline | Specialist |
| --- | ---: | ---: |
| Fixed cost | 10.00 | 90.00 |
| Variable cost per request | 0.020 | 0.030 |

The specialist is more expensive on every request and its fixed cost is also higher. The gap grows with volume. There is no finite volume at which the specialist becomes strictly cheaper.

## Review price moves the crossover

Frozen quality is not an input to this arithmetic. Use the same observed rates for both review prices.

| Workflow | Inference | Observed review rate |
| --- | ---: | ---: |
| Baseline | 0.015 | 0.05 |
| Specialist | 0.004 | 0.10 |

Additional fixed cost stays 60.00.

Review price 0.10:

- baseline variable = 0.015 + 0.05 × 0.10 = 0.020
- specialist variable = 0.004 + 0.10 × 0.10 = 0.014
- saving per request = 0.006
- equality at 60 / 0.006 = 10,000
- first strict saving at 10,001

Review price 0.50:

- baseline variable = 0.015 + 0.05 × 0.50 = 0.040
- specialist variable = 0.004 + 0.10 × 0.50 = 0.054

The specialist variable cost is now higher and the fixed cost was already higher, so there is no favorable large-volume break-even. The quality figures are unchanged because they are not recomputed.

## Scoring denominator

Four evaluation rows, one gold label each: hvac, plumbing, electrical, custodial.

| Gold | General-model outcome |
| --- | --- |
| hvac | scored hvac |
| plumbing | abstain |
| electrical | timeout |
| custodial | scored custodial |

Support is 1 for every label, including the abstention and the timeout. True positives are hvac and custodial only. Per-class recall is 1, 0, 0, 1. Macro-F1 is 0.5 when precision for an unused label is 0 and the two correct labels have precision 1.
