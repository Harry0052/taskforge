# Changelog

## 0.1.0

- Synthetic four-label facilities work orders, with template families kept inside one split.
- Recorded offline trace for `lexical-generalist` revision 1.0.0.
- CPU specialist (TF-IDF and logistic regression) retrained on each run. Coefficients are exported as JSON and are not loaded back.
- Macro-F1, per-class recall, and support counts that keep abstentions, timeouts, and no-results in the denominator.
- Decimal cost crossover. The modeled demo ties at 4,000 requests and first saves at 4,001 when the quality gate passes.
- `taskforge validate`, `taskforge analyze`, and `taskforge demo`.
