# Batch Evaluation Summary

Source rating files: `rating_case1.md` through `rating_case5.md`.

## Score Matrix

| Case | HUMAN total | AI-GPT5.5 total | AI-KIMI total | AI-GPT5.5-FU total | Verdict ranking |
|---|---:|---:|---:|---:|---|
| case1 | 65.5 | 65.8 | N/A | 77.0 | AI-GPT5.5-FU > AI-GPT5.5 ≈ HUMAN |
| case2 | 45.8 | 66.5 | 42.5 | 74.3 | AI-GPT5.5-FU > AI-GPT5.5 > HUMAN ≈ AI-KIMI |
| case3 | 66.5 | 53.5 | 22.3 | 60.8 | HUMAN > AI-GPT5.5-FU > AI-GPT5.5 > AI-KIMI |
| case4 | 50.5 | 74.8 | 30.8 | 74.8 | AI-GPT5.5 ≈ AI-GPT5.5-FU > HUMAN > AI-KIMI |
| case5 | 45.0 | 66.8 | 44.0 | 74.0 | AI-GPT5.5-FU > AI-GPT5.5 > HUMAN ≈ AI-KIMI |

## Per-Dimension Averages

Means are across cases where that response was present: HUMAN n=5, AI-GPT5.5 n=5, AI-KIMI n=4, AI-GPT5.5-FU n=5.

| Dimension | HUMAN | AI-GPT5.5 | AI-KIMI | AI-GPT5.5-FU |
|---|---:|---:|---:|---:|
| D1 Responsiveness to the reviewer question | 6.7 | 5.9 | 3.9 | 7.2 |
| D2 Computational coverage and scale | 6.0 | 5.2 | 3.3 | 6.7 |
| D3 Soundness of methods and models | 5.1 | 6.3 | 4.0 | 6.7 |
| D4 Execution completeness and technical rigor | 4.3 | 7.5 | 2.9 | 7.7 |
| D5 Correctness and internal consistency | 5.5 | 6.9 | 2.6 | 7.1 |
| D6 Transparency and stated limitations | 3.8 | 8.4 | 4.8 | 8.3 |

## Red-Flag Frequencies

Counts are triggered cases out of present cases: HUMAN /5, AI-GPT5.5 /5, AI-KIMI /4, AI-GPT5.5-FU /5.

| Red flag | HUMAN | AI-GPT5.5 | AI-KIMI | AI-GPT5.5-FU |
|---|---:|---:|---:|---:|
| Answering the wrong question | 1 | 3 | 4 | 1 |
| Selective reporting | 1 | 0 | 2 | 0 |
| Undocumented results relied upon | 5 | 0 | 4 | 0 |
| Misreading the manuscript or cited work | 0 | 1 | 1 | 1 |
| Overinterpretation | 5 | 1 | 4 | 0 |
| Anomalous magnitudes | 1 | 1 | 4 | 2 |
| Insufficient statistics | 5 | 3 | 4 | 3 |

## AI-GPT5.5 to AI-GPT5.5-FU Delta

| Case | What the follow-up bought |
|---|---|
| case1 | Substantive computational coverage and better target matching; largest gains were D1/D2/D4, while D5 remained limited by 13.6 at.% interpretation risk, under-sampled R2-3 energetics, and a composition typo. |
| case2 | Substantive scope correction and better limitation handling, especially adding the missing deep-level-defect topic; it did not make the DOS evidence strongly positive and introduced an unresolved dipole discrepancy. |
| case3 | Substantive improvements in COHP, pathway thermodynamic descriptors, H* affinity, and support modeling; it still lacked TS/NEB or H-transfer barriers and lost Mo/W scope coverage. |
| case4 | No visible change: `report.docx` and `report-f.docx` were file-identical, so the follow-up bought no substantive or cosmetic revision and caused no regression. |
| case5 | Substantive improvement from an amorphous hydrous model and complete CHE endpoint table; remaining limits were single-site statistics and screening-level electronic CHE. |

## Caveats

- No case folders were skipped or marked not evaluated.
- `case1` was missing `report-k.docx`; AI-KIMI is therefore N/A for `case1` and omitted from that case ranking.
- All five rating files passed the mechanical compliance check: required sections present, six dimension rows scored for present responses, seven red-flag rows marked, Delta sections present where applicable, and weighted totals matching the itemized scores after one-decimal rounding.
- No rating file required a retry or compliance-fix follow-up.
