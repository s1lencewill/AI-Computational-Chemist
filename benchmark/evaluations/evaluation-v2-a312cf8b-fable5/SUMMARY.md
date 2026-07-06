# SUMMARY — four-way evaluation run (`evaluations-2/`)

Run date: 2026-07-05. Cases evaluated: case1–case5 (all case folders present in `benchmark/cases/`; none skipped). One subagent per case; all scores below are transcribed from the per-case rating files (`rating_case<C>.md`) — no scores were adjusted by the orchestrator. Weighted totals were recomputed from the itemized scores and match in all five files.

## 1. Score matrix

Weighted totals out of 100. Pairs within 5 points are ties (≈).

| Case | HUMAN | AI-GPT5.5 | AI-KIMI | AI-GPT5.5-FU | Verdict (present responses only) |
|---|---|---|---|---|---|
| case1 | 82.0 | 54.8 | N/A (missing) | 65.8 | HUMAN > AI-GPT5.5-FU > AI-GPT5.5 |
| case2 | 70.0 | 79.5 | 61.3 | 81.5 | AI-GPT5.5-FU ≈ AI-GPT5.5 > HUMAN > AI-KIMI |
| case3 | 82.0 | 58.5 | 29.8 | 68.5 | HUMAN > AI-GPT5.5-FU > AI-GPT5.5 > AI-KIMI |
| case4 | 65.0 | 67.3 | 42.3 | 67.3 | AI-GPT5.5 ≈ AI-GPT5.5-FU ≈ HUMAN > AI-KIMI |
| case5 | 63.8 | 64.0 | 57.8 | 65.8 | AI-GPT5.5-FU ≈ AI-GPT5.5 ≈ HUMAN > AI-KIMI |
| **Mean** | **72.6** (n=5) | **64.8** (n=5) | **47.8** (n=4) | **69.8** (n=5) | |

Case topics (from the rating files): case1 — Pt single-atom dispersion in liquid Ga (MLP/DPMD MD); case2 — IDMP double-end anchoring on a perovskite surface (periodic DFT); case3 — Pt₁Ni SAA mechanism & NiAl₂O₄ support role in lignin RCF (periodic DFT); case4 — dynamic Pt oxidation state at Pt/TiO₂ (DFT + Bader); case5 — h-RuOx vs anh-RuO₂ stability in acidic OER (DFT + AIMD).

## 2. Per-dimension averages

Mean dimension scores (0–10) across the cases where each response was present (HUMAN / AI-GPT5.5 / AI-GPT5.5-FU: 5 cases; AI-KIMI: 4 cases).

| Dimension | HUMAN | AI-GPT5.5 | AI-KIMI | AI-GPT5.5-FU |
|---|---|---|---|---|
| D1 Responsiveness (25%) | 8.1 | 5.5 | 4.8 | 6.5 |
| D2 Coverage and scale (15%) | 7.4 | 5.5 | 4.4 | 6.8 |
| D3 Methods and models (15%) | 6.6 | 6.1 | 5.3 | 6.6 |
| D4 Execution completeness (15%) | 6.8 | 7.5 | 4.1 | 7.6 |
| D5 Correctness / consistency (20%) | 7.6 | 7.0 | 4.3 | 6.7 |
| D6 Transparency / limitations (10%) | 5.9 | 8.4 | 6.8 | 8.6 |

## 3. Red-flag frequency

Number of cases in which each flag was marked "found" (any variant: found / found (partial) / found (minor) / found (mild) / found (disclosed)). Denominators: HUMAN, AI-GPT5.5, AI-GPT5.5-FU = 5 cases; AI-KIMI = 4 cases.

| Red flag | HUMAN | AI-GPT5.5 | AI-KIMI | AI-GPT5.5-FU |
|---|---|---|---|---|
| 1. Answering the wrong question | 0 | 4 | 2 | 3 |
| 2. Selective reporting | 0 | 1 | 2 | 0 |
| 3. Undocumented results relied upon | 0 | 0 | 2 | 0 |
| 4. Misreading the manuscript / cited work | 0 | 0 | 1 | 0 |
| 5. Overinterpretation | 3 | 0 | 4 | 2 |
| 6. Anomalous magnitudes | 0 | 0 | 3 (+1 "not assessable", case3) | 4 |
| 7. Insufficient statistics | 2 | 3 | 3 | 3 |
| **Total flags found** | **5** | **8** | **14** | **12** |

## 4. AI-GPT5.5 → AI-GPT5.5-FU (per-case delta, from the rating files' Delta sections)

- **case1** (54.8 → 65.8, +11.0): Substantive — concentration-matched cells including the 43-Pt large cell at the experimental 0.2 at%, 10× longer trajectories (1 ns), Warren-Cowley short-range-order analysis with random baselines and initial-condition independence; minor regression in signal quality from two construction-artifact numbers (96 eV formation contrast, 6.66 eV drag barrier), transparently caveated.
- **case2** (79.5 → 81.5, +2.0): Substantive but marginal — the core R1.2 evidence is unchanged; adds an honestly inconclusive DOS (R1.4), molecular dipole/ESP/ELF, and a heavily caveated total-Bader metric; transparency gains, no regressions.
- **case3** (58.5 → 68.5, +10.0): Substantive — corrects the alumina phase (α→γ, multi-site vacancies, now matching HUMAN's ~1.4 eV gap), adds SG pathway ΔE/ΔG at 413 K with implicit solvent, C–O COHP, and ΔG_H* descriptors; one new overclaim ("substantial" COHP weakening inconsistent with its own bond lengths) and an explicit scope removal of TS/barrier work.
- **case4** (67.3 → 67.3, 0.0): Null — `report-f.docx` is byte-for-byte identical to `report.docx` (same MD5); the follow-up changed nothing; FU scored identically to AI-GPT5.5.
- **case5** (64.0 → 65.8, +1.8): Mixed substantive — the only response to deliver both a real AIMD amorphous h-RuOx model and the explicitly requested four-step OER free-energy profile, plus transparency gains; but the profile's 1.89 V overpotential is physically unreasonable and unflagged (new anomalous-magnitude flag).

## 5. Caveats

- **No skipped cases.** All five case folders contained the four required PDFs and at least one AI response file.
- **case1**: `report-k.docx` (AI-KIMI) missing from the case folder → AI-KIMI marked N/A; three-way evaluation (HUMAN, AI-GPT5.5, AI-GPT5.5-FU).
- **case4**: `report-f.docx` is byte-identical to `report.docx` (verified by MD5 in the rating file); AI-GPT5.5-FU therefore duplicates AI-GPT5.5 and the Delta is recorded as null.
- **case1 execution**: the subagent was interrupted mid-run and resumed via a follow-up message with the same instructions. Its rating file then needed one compliance fix — a column shift in Red-Flag row 5 (the AI-KIMI cell must read N/A; the FU cell was blank) — which the subagent corrected on send-back. No scores were changed.
- **case3**: AI-KIMI's red-flag 6 (anomalous magnitudes) is marked "not assessable" rather than found / not found, with the stated justification that the report contains too few reported numbers to judge.
- All other rating files passed the compliance spot-check on first delivery (all six dimensions scored per present response; totals recompute from weights; all 7 red flags marked; Delta present where both GPT5.5 files exist).

## 6. Pointers

- Per-case rating files: `evaluations-2/rating_case1.md` … `rating_case5.md`.
- Rubric: `../EVAL_PROMPT.md`; orchestration protocol: `../RUN_ALL.md`.
