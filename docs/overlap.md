# Overlap: does TaskForge need its own repository?

**Access date:** 2026-11-23  
**Decision:** Proceed with a separate repository.  
**Question:** Can an ML engineer, on one four-label facilities routing task, see whether a CPU specialist beats a pinned general model on a locked evaluation set and at which integer request volume the specialist's total cost becomes strictly lower, after training and human review, with the tie called out separately?

## Capability matrix

Held constant across the probe in `docs/probes/p01-shared-fixture.json`:

| Input | Value |
| --- | --- |
| Additional specialist fixed cost | 60.00 USD |
| Baseline variable cost | 0.020 USD per request |
| Specialist variable cost | 0.005 USD per request |
| Quality gate | passed |
| Expected artifact | equality at 4,000 requests; first strict saving at 4,001 |

| Capability | RouteLLM | FrugalGPT | taskdistill | TaskForge MVP |
| --- | --- | --- | --- | --- |
| Same locked item ids for both systems | Benchmark prompts, not a user label set | Cascade test split | Teacher/student/cascade on one split | Required |
| Macro-F1 and per-class recall before eligibility | No. MT-Bench, MMLU, GSM8K | Accuracy and API cost | Accuracy, agreement, optional macro-F1 against the teacher | Required gate |
| Timeouts and no-results stay in the support denominator | Not a classification scorer | Not specified | Failed escalations are counted in serve logs, not as label support | Required |
| Template families cannot cross splits | No | Random split | Selection uses validation; no template-family leak check | Required |
| Fixed cost is labeling + training + integration | Router overhead only | API spend on the test set | Labeling ledger + training energy | Required |
| Variable cost is inference plus observed review rate times an editable review price | Strong-model call fraction | Sum of cascade API calls | Teacher escalation plus local energy | Required |
| Analytic crossover and the first strict saving after an integer tie | No volume crossover | No | `ceil(exact - 1e-9)` returns the tie when the ratio is an integer | Required, and the probe separates 4,000 from 4,001 |
| Decimal money, independent of measured timings | No | No | Float energy and API dollars | Required |
| Offline demo with no weight download and no paid API | No. Eval expects model runs or keys | No. Hosted LLM APIs | Recorded traces exist, but training expects Apple Silicon or a torch stack and model weights | Required |
| One CPU specialist, one four-label task | Routers between two LLMs | Cascade of LLM APIs | Local generative student plus cascade | Required |

## Contenders

### RouteLLM

| Field | Evidence |
| --- | --- |
| Primary URL | https://github.com/lm-sys/RouteLLM |
| Access date | 2026-11-23 |
| Commit | `0b64fdafe049e596a3f5657c219329f24af24198` (2024-08-10) |
| Package | `routellm` 0.2.0 on PyPI, uploaded 2024-07-08. No GitHub release. |
| Code license | Apache-2.0 |
| Dataset terms | Preference routers are trained on Chatbot Arena human preferences plus GPT-4 judge augmentation (paper arXiv:2406.18665). Arena data is not part of this probe and will not be shipped. Router weights are hosted on Hugging Face under `routellm` and `lmsys`. |
| What it already does | Routes each request between a strong and a weak LLM. Reports cost as the fraction of strong-model calls needed to hold a quality level (about 85% cost reduction at 95% of GPT-4 MT-Bench in the README). Matrix-factorization, BERT, causal-LLM, similarity-weighted Elo, and random routers. |
| Probe | **Documentation.** The README quickstart (`Controller`, `router-mf-<threshold>`, `routellm.evals.evaluate`) has no fields for specialist fixed cost, human review price, or a locked label dictionary. Running it would also require API keys and model downloads, which this MVP excludes. |
| Gap | Routing two general models is a different decision from paying to train and review a specialist. |

### FrugalGPT

| Field | Evidence |
| --- | --- |
| Primary URL | https://github.com/stanford-futuredata/FrugalGPT |
| Access date | 2026-11-23 |
| Commit | `2b23e6acbd4b39f71912816640dcc59e45aa4b5e` (2025-02-10) |
| Package | No `frugalgpt` or `FrugalGPT` distribution on PyPI (HTTP 404 on 2026-11-23). |
| Code license | Apache-2.0 |
| Dataset terms | The paper evaluates HEADLINES, OVERRULING, and COQA. Those datasets have their own terms and are not reused here. |
| What it already does | Learns an LLM cascade: call a cheaper model, accept when a scorer is confident, otherwise escalate. Reports test accuracy and API cost under a budget. The paper's HEADLINES cascade saves a large share of GPT-4 cost at similar accuracy. |
| Probe | **Documentation.** `src/FrugalGPT/llmcascade.py` and the example notebooks compare cascade API cost with single-model API cost. They do not take a training-and-review fixed cost or emit an integer tie versus the next request. A live cascade needs hosted model credentials. |
| Gap | A cascade and a specialist can disagree on the break-even region once review and training are priced. This repository computes that specialist region; it does not reimplement the cascade. |

### taskdistill (closest discovery result)

| Field | Evidence |
| --- | --- |
| Primary URL | https://github.com/B0yko/taskdistill |
| Access date | 2026-11-23 |
| Commit | `3e803335cc9af45f82800c863bce4bf55040305d` (2026-11-20) |
| Package | `taskdistill` 0.1.1 on PyPI, uploaded 2026-09-27. Requires Python >= 3.12. `mlx` is pinned for macOS arm64. |
| Code license | Apache-2.0. Synthetic invoices in that repository share the same license. Banking77, which the README also reports, is a third-party dataset and is out of scope here. |
| What it already does | Distills one repeated API task into a local student, cascades low-confidence requests back to the teacher, and reports a break-even volume. README figures (recorded 2026-09-27) put Banking77 break-even at 17,419 requests on recorded teacher cost. Quality choices are frozen on the validation split. |
| Probe | **Observed run of the published formula, not of the package.** `build_break_even` defines volume as `(labelling cost + training energy) / (teacher − cascade cost per request)` and stores `ceil(exact - 1e-9)`. Mapped onto the shared fixture (fixed 60, teacher 0.020, cascade 0.005) the function returns **4,000**, which is the tie, and it does not report 4,001. The package itself was not installed: its supported classifier path is Apple Silicon, and a full run downloads student weights. |
| Why not contribute the MVP there | The acceptance case also needs template-family rejection, exact evaluation ids, timeout-in-denominator recall, a quality gate that can suppress a recommendation while still printing the scenario, and analyst review dollars that move the crossover without recomputing quality. Those are a different product surface from an Apple-Silicon distillation cascade. |

### Other discovery notes

Search queries used on 2026-11-23:

- `GitHub small specialized model versus LLM training inference cost break even`
- `GitHub classification specialist versus general model quality benchmark cost analysis`
- `LLM narrow task classification total cost human review abstention economics`

Nearby work that does not meet the acceptance case:

- `ameyypawar/finetune-vs-api` compares self-hosted GPU rental with API list prices. Break-even is a monthly call volume against a always-on GPU, not human review of a four-label task.
- `IshaanAyaan/slm-agents` measures cost per successful agent task for a fine-tuned 3B model. It is an agent harness study, not label-set scoring.
- arXiv:2402.12819 studies how many labels a specialist needs to match a general model. It stops at performance break-even, not dollar crossover.
- arXiv:2610.31657 (cost-aware abstention for IT tickets) picks a threshold from triage and misroute prices. It does not amortize training.
- POFE's public note (https://pofe.ai/learn/economics/base-vs-finetuned-vs-frontier-api/, accessed 2026-11-23) writes a closed-form volume that includes failure cost. It is an article, not a runnable fixture with a locked evaluation set.

**Lunri.** The playbook names Lunri as a project that meters energy for complete AI workflows, which is a different question from lifecycle specialist-versus-baseline cost. A GitHub repository search for `lunri` on 2026-11-23 returned no repository. No URL is cited because none was verified. This boundary stays a documentation note, not a probed tool.

### Dependencies for the MVP

| Piece | Version checked 2026-11-23 | License | Role |
| --- | --- | --- | --- |
| Python | 3.12.3 on the probe host | PSF | Runtime |
| scikit-learn | 1.9.1 on PyPI (`license_expression` BSD-3-Clause) | BSD-3-Clause | CPU specialist |
| NumPy | 2.5.5 on PyPI | BSD-3-Clause | Arrays |
| pytest | to be pinned at implementation time | MIT | Tests |

Provenance path: original synthetic work orders written for this repository, plus one local run of a small pinned generalist whose trace is stored in the repo. No Arena, HEADLINES, Banking77, or model-weight files are shipped. The demo reads the trace and does not download weights or call a paid API.

## Decision

**Proceed.** The acceptance case is concrete, the shared fixture has an expected numeric artifact, and no examined tool produces that artifact with the required safeguards. Contributing it to RouteLLM or FrugalGPT would change those projects from router/cascade evaluation into specialist lifecycle accounting. taskdistill is the nearest workflow and still returns the tie volume, depends on a different training stack, and does not enforce the data-contract rejections.

Uncertainties left open on purpose:

- A future revision could swap the pinned local generalist for a redistributable model trace if the weight license and output terms are reviewed separately. The MVP does not block on that download.
- Dollar inputs stay assumptions. Measured wall time is reported beside them and is not converted to money inside the demo.
