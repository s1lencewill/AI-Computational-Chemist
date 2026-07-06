# Design Rationale — Standardized Evaluation Rubric (EVAL_PROMPT.md)

This document explains why the rubric in `EVAL_PROMPT.md` is designed the way it is. It is the reference to consult before changing any weight, dimension, or rule, so that changes are made deliberately rather than by drift.

**Important**: this file is for the benchmark designer only. It contains settled verdicts and known failure modes from past tasks (1, 4, 7), which would anchor a grading session evaluating those same tasks — do not give it to a grader.

## 1. Background and problem statement

The benchmark compares, for each task, two answers to the same real reviewer comment on a published paper:

- **Human side**: the original authors' calculations, extracted from the paper / SI / response letters.
- **AI side**: an AI agent's independent attempt at the same reviewer question, delivered as a report plus (usually) raw calculation outputs.

(Identities are disclosed to the grader, but under the zero-prior rules of §5 they carry no evidentiary weight.)

Before standardization, two incompatible scoring formats coexisted in this repo:

1. `task_XX.md` files used a 100-point scale with four items (coverage/30, completion & convergence/30, methodological rigor/20, consistency of results/20).
2. `rating_taskN_*.md` files used a 10-point scale with five dimensions whose **names changed between tasks** (e.g., "soundness of methods and models" in task 4 became "training set / force-field quality" in task 7), and whose overall score was assigned holistically rather than computed.

Both formats produced good qualitative analysis, but the scores were not comparable across tasks or across graders (including the same grader in different sessions). The rubric fixes that.

## 2. Design goals

1. **Cross-task comparability** — identical dimensions, weights, and anchors for every task, whether the work is DFT + Bader analysis or MLP training + MD.
2. **Reproducibility across grading sessions** — a fresh LLM session given the same materials should land within ~0.5 points per dimension of a previous session. This is achieved through score-band anchors, evidence-first scoring, and deterministic aggregation.
3. **Evidence-based, not impression-based** — every score must trace to a file, number, or page; report polish must not leak into scores.
4. **Encode known failure modes** — the issues actually caught in earlier manual evaluations become mandatory checks, so later evaluations cannot silently miss them.
5. **Impartial and symmetric** — identities (human vs. AI) are disclosed but carry no evidentiary weight: neither side is presumed better, and all checks and standards apply identically to both. See §5.

## 3. Why these six dimensions

The six dimensions were derived by merging the two legacy formats and splitting along lines where the earlier evaluations found that AI and human scores genuinely diverge:

| Dimension | Origin / justification |
|---|---|
| D1 Responsiveness to the reviewer's question | The single biggest AI failure mode observed. In task 4, the AI reported ensemble-average Bader charges when the reviewer asked about a **dynamic valence transition of a specific interfacial Pt atom** — the human's same-atom before/after tracking was what persuaded the reviewer. Dimension names it explicitly so graders check "which question was actually answered." |
| D2 Computational coverage and scale | From the legacy "coverage/30." Separated from methods because AI runs were often methodologically clean but 1–2 orders of magnitude short on sampling (task 7: 1 ns vs. 20 ns; task 1: 100-atom vs. 21385-atom systems). Scale problems must not hide behind good method choices. |
| D3 Soundness of methods and models | From the legacy "methodological rigor." Kept task-agnostic by listing concrete sub-criteria (functional, +U, dispersion, ENCUT, k-points, model construction, force-field training-set coverage and independent validation) instead of renaming the dimension per task, which is what broke comparability in the legacy 10-point format. |
| D4 Execution completeness and technical rigor | From the legacy "completion & convergence." Task 1 showed why this must be independent: a correct pipeline (AIMD → DeepMD → LAMMPS) whose production run was **CANCELLED** delivered zero comparable physics. Also rewards genuine troubleshooting (task 4's three restart strategies for a non-converging relaxation). |
| D5 Correctness and internal consistency | The second-biggest AI failure mode. Task 7 exposed selective reporting (citing positive cluster-formation energies while omitting negative ones from the same table), an implausible 6.66 eV barrier, and a misreading of the original composition (Pt43 → Pt432). The human side also loses points here for overinterpretation (Bader charge treated as formal oxidation state). |
| D6 Transparency and stated limitations | The dimension where AI consistently **beats** humans (explicit limitation statements, full data provenance). Kept as its own dimension so this real strength is credited — but capped at 10% so honesty about weak work cannot buy a win. |

## 4. Why these weights

Weights encode the answer to: *what is this benchmark actually measuring?* The verdict that matters is "would this response satisfy the reviewer, and can its numbers be trusted?"

- **D1 (25%) + D5 (20%) = 45%** — dominance is deliberate. In every task evaluated so far, the gap between AI and human was decided by responsiveness and trustworthiness of results, not by methodology. AI routinely matched or beat humans on D3/D4/D6; weighting those heavily would manufacture AI wins that contradict the qualitative judgment that the human response was the one that actually persuaded reviewers.
- **D2 = D3 = D4 (15% each)** — necessary infrastructure, individually insufficient. No known task outcome was decided by these alone, but each has a veto-like failure mode (missing critical calculation, wrong functional family, cancelled production run) that the 0–2 anchor band handles.
- **D6 (10%)** — real but least decisive. A model limitation statement does not compensate for numbers that don't hold up.

Sensitivity check when re-weighting: recompute the legacy tasks (1, 4, 7). A weighting under which task-1's AI (cancelled production run) scores above ~40/100, or task-4's AI vs. human ordering flips by more than ~1 point on the 10-scale, contradicts the settled qualitative judgments and should be rejected.

## 5. Disclosed-identity, zero-prior protocol

The grading prompt tells the grader which response is human and which is AI, but strips that fact of all evidentiary weight. This replaced a fully blind design (v1.1) for practical reasons:

- **Blinding was not actually achievable with these materials.** The two response documents have unmistakable formats (a structured AI report vs. published-paper extracts), the peer-review file `03` contains the human rebuttal nearly verbatim, and file names like `04_human.pdf` / `report.docx` leak identity. A "blind" grader would infer the labels anyway and then reason about them covertly — worse than addressing the bias head-on with explicit rules.
- **Honesty over ceremony.** Disclosing identity and instructing impartiality makes the anti-bias requirement auditable: the grader can be told exactly which priors are forbidden, and the self-check can ask directly whether authorship moved any score.

The real risks blinding was meant to counter are handled by explicit rules instead:

1. **Authorship priors are strong and bidirectional.** Deference to the published side ("it passed peer review, so it must be right") is not harmless — task 4's human original itself contained overinterpretation (Bader charge → formal oxidation state). Conversely, an AI prior can cut either way (distrust, or over-crediting apparent rigor). The prompt states both presumptions are forbidden, and the self-check includes a dedicated item: numeric disagreements must be resolved on the merits, never by defaulting to the human value.
2. **Outcome information is excluded.** Real reviewers' satisfaction with the human answer is authority, not content; "no deference to publication" is a standing calibration rule, and `03` is quarantined to question extraction (see §6a).
3. **Symmetry discipline.** All checks (red flags, cross-verification, undocumented-claim handling) are explicitly required for both responses — in the earlier labeled evaluations, verification effort was visibly asymmetric. The red-flag section reminds the grader that published work commits red flags too.
4. **Style/polish firewall.** AI reports are systematically longer and more structured; the "score the evidence, not the prose" rule prevents this surface feature from translating into points, in either direction.

## 6. Why 0–10 per dimension with weighted aggregation

- **Anchored 0–10 bands** (9–10 / 7–8 / 5–6 / 3–4 / 0–2) map to reviewer-meaningful outcomes ("submittable" → "reviewer would reject" → "absent"), which LLM graders apply far more consistently than an unanchored percentage.
- **The total is computed, never assigned.** In the legacy 10-point format the overall score was holistic, which is where grader drift concentrated. Any disagreement between "computed total" and "gut feeling" must be resolved by fixing a dimension score with evidence — not by adjusting the total.
- Reporting both /100 and /10 keeps the output comparable with both legacy formats.

## 6a. Material structure and document-level verification (v1.2)

Each grading session receives a fixed material package:

- **Shared background**: `01` manuscript and `02` SI (both with computational content removed — the same "question package" both responders worked from), plus `03` the peer-review file.
- **Responses**: three AI-side documents (`report.docx` = AI-GPT5.5, `report-k.docx` = AI-KIMI, `report-f.docx` = AI-GPT5.5-FU) and the human side's `04` extracts. **No raw calculation data (OUTCARs, logs, trajectories) are provided to the grader.**

Two consequences are handled explicitly in the prompt:

1. **`03` is quarantined to question extraction.** The peer-review file contains the real authors' rebuttals and the reviewers' subsequent reactions. Read further, it is simultaneously (a) outcome information ("the reviewer was satisfied") and (b) an apparent answer key that would make the human response self-certifying. The prompt therefore restricts `03` to locating and understanding the target comment, and states that rebuttal content is not ground truth.
2. **Verification degrades from raw-data-level to document-level.** This is a real loss, accepted for practicality, and the operator must remember what it costs: in the legacy labeled evaluations, the two most damning AI findings came from raw outputs — task 1's CANCELLED production run and task 7's unfinished 21385-atom run were only visible in Slurm logs / missing completion markers. At document level, a response that **misrepresents** an unfinished run as complete is undetectable; only honestly-disclosed gaps and internally-inconsistent claims can be caught. Selective reporting remains detectable as long as reports include their full data tables (task 7's did). D4 and red flag #3 were rewritten to judge *documented* completeness ("undocumented — no credit") rather than verified completeness. If a task's verdict hinges on execution claims, the operator can re-run that task with raw data attached as a follow-up check outside the standard protocol.

## 7. Why a fixed procedure (read order matters)

The procedure forces the grader to distill the reviewer's question **before** reading either answer, because the observed failure mode (task 4) is subtle: an answer can be internally excellent while answering an adjacent question, and a grader who reads the answer first will anchor on its framing. Recording both sources' contents before judging ("record only — do not judge") separates fact-gathering from evaluation, reducing halo effects from a well-written report.

Cross-verification (step 4) is mandatory because the reports cannot be trusted as self-descriptions: task 1's report-level pipeline looked complete while the production run was cancelled, and task 7's narrative disagreed with its own data tables. When raw outputs exist, key claims must be traced to them.

## 8. Why the red-flag checklist

Every item is a failure mode **actually observed** in this repo's earlier evaluations — the checklist is empirical, not theoretical:

1. Answering the wrong question — task 4 (ensemble statistics vs. same-atom tracking).
2. Selective reporting — task 7 (omitted negative formation energies at n = 4, 8).
3. Unfinished runs treated as deliverables — task 1 (CANCELLED Slurm job), task 7 (21385-atom run with no completion marker).
4. Misreading the original paper — task 7 (Ga2063Pt43 misread as Pt432, then used to criticize the original).
5. Overinterpretation — task 4, on **both** sides (human: Bader → formal oxidation state; AI: +0.166 eV called "energetically compatible").
6. Anomalous magnitudes — task 7 (6.66 eV pairing barrier vs. the human's ~2.9 eV estimate).
7. Insufficient statistics — task 7 (SEMs overlapping zero used for a quantitative claim).

Making "found / not found" explicit for all seven, on both sources, prevents silent omission and produces per-flag frequency data across tasks — itself a useful benchmark output. Flags apply symmetrically: humans commit #5 too.

## 9. Calibration rules — the biases they counter

| Rule | Bias it counters |
|---|---|
| Score the evidence, not the prose | One source's reports are typically long, structured, and confident; halo effect inflates scores. Verbosity must earn nothing, and terseness must cost nothing beyond the evidence it fails to show. |
| Score extract-style D3/D6 on visible evidence only | Two opposite temptations: crediting a source for methods it "surely used" (unverifiable), or over-penalizing extracts for thinness. Both sides are scored on what can be seen. |
| Ignore outcome information (reviewer/editor reactions, publication status) | Authority substitution: "the reviewer accepted it" is evidence about the process, not the content. Persuasiveness is judged from the science alone. |
| No deference to publication; authorship, style, polish, length must not move scores | The core zero-prior rule (§5): scores must measure the work, not the grader's prior about AI or about published papers — in either direction. |
| Numeric disagreements resolved on the merits, not by defaulting to the human value | The subtlest form of deference: treating the published number as the reference and scoring the AI by its deviation. Discrepancies are investigated, not adjudicated by authorship. |
| Deduct once, in the most pertinent dimension | One flaw (e.g., a cancelled run) touches D2/D4/D5 simultaneously; naive scoring triple-counts it and produces implausibly low totals. |
| Name the strongest and weakest point of each side | Confirmation bias: once a grader decides who won, commentary tends to become one-sided. Forcing both directions keeps dimensions independent. |
| Unverifiable = no credit, flagged (not a middle score) | LLM graders default to charitable midpoints under uncertainty, which systematically favors the side with more unverifiable claims — usually the AI. |
| "Why not an 8" required above 9 | Score compression at the top; 9+ should be rare and justified. |
| ≤ 5 points apart ⇒ "effectively a tie" | The rubric's resolution is roughly ±5/100; declaring winners inside the noise band creates false rankings across tasks. |

## 10. Known limitations and non-goals

- **Grader ≠ oracle.** The rubric reduces variance; it does not supply domain knowledge the grading session lacks (e.g., recognizing that 6.66 eV is implausible requires expertise). Pairing the rubric with spot-checks by a human expert on a sample of tasks remains necessary.
- **Human materials are extracts**, so human D3/D6 scores systematically understate the original work. This is accepted (visible-evidence rule) and should be remembered when reading absolute human scores; the cross-task **AI-vs-human gap** is more meaningful than either absolute value.
- **The rubric measures response quality, not scientific truth.** A persuasive-but-slightly-overinterpreted human response can outscore a more literally-correct AI response on D1 by design, because the benchmark's question is "who serves the peer-review situation better," with D5 as the counterweight against rewarding rhetoric over correctness.
- **Single-grader design.** For higher-stakes conclusions, run the same task through 2–3 independent grading sessions and check per-dimension spread; disagreement > 1 point on any dimension signals either a rubric gap (fix here) or a materials gap (note in the task file).

## 10a. Cheap bias sensitivity check (optional, run on demand)

The zero-prior rules of §5 suppress but cannot eliminate label bias. Rather than paying for blinding on every task (unachievable anyway, §5), run a one-off calibration experiment to *measure* how much the labels move scores:

- **When**: once, on 2–3 tasks that already have settled verdicts (tasks 1/4/7 are natural picks); or as a spot-check on any task whose verdict looks suspicious.
- **How**: run the same task twice in fresh sessions.
  - *Arm L (labeled)*: the standard protocol, `EVAL_PROMPT.md` as-is.
  - *Arm D (de-identified)*: same rubric, but responses presented as "Response 1 / Response 2" in plain text with provenance labels and meta-sentences stripped (extraction headers like "Response letter PDF page …", agent meta-statements like "calculations were designed from the supplied manuscript"), and only the extracted reviewer comment provided instead of the full `03` (which contains the human rebuttal verbatim).
- **Read-out**: compare per-dimension scores. |Δ| ≤ 0.5 on every dimension and an unchanged verdict → the disclosed protocol is trustworthy; proceed. A systematic shift (especially the human side gaining on D1/D5 only when labeled) → label bias is real at that magnitude; switch the affected tasks to isolation grading (each response scored in a separate session against the anchors only, no side-by-side comparison, merged by the operator).
- **Caveat**: Arm D is only approximately blind (style cues survive de-identification), so the measured Δ is a **lower bound** on the true label effect. A small Δ is reassuring but not proof; a large Δ is decisive.

## 11. Change policy

If a dimension, weight, or rule must change:

1. Record the change and reason in this file (append a dated changelog entry below).
2. Re-run at least the previously settled tasks (1, 4, 7) under the new rubric and confirm their verdicts don't flip; if one flips, either the change is wrong or the earlier verdict was — resolve explicitly before adopting.
3. Never change the rubric mid-batch: finish scoring the current set of tasks under one version.

## Changelog

- 2026-07-03 — v1. Initial rubric and rationale, derived from manual evaluations of tasks 1, 4, and 7 (legacy formats: `task_XX.md` 100-point / `rating_taskN` 10-point).
- 2026-07-03 — v1.1. Converted to a blind protocol (§5): sources anonymized as A/B with no provenance; added rules forbidding authorship guessing, style-based scoring, and use of outcome information (reviewer reactions / publication status); removed the v1 rule that peer-review acceptance may support D1; all cross-verification and red-flag checks now explicitly symmetric across both sources; added operator requirements (neutral file paths, A/B randomization, redacting reviewer verdicts).
- 2026-07-03 — v1.2. Fixed the material package (§6a): shared background `01`/`02`/`03` + exactly one response document per source, no raw calculation data. `03` restricted to question extraction (it contains rebuttals and reviewer reactions). Cross-verification, D4, and red flag #3 rewritten from raw-data-level to document-level ("undocumented — no credit"); trade-off documented in §6a.
- 2026-07-03 — v1.3. Dropped blinding in favor of a disclosed-identity, zero-prior protocol (§5 rewritten): identities are stated openly (blinding was unachievable with these materials and invited covert inference), but carry no evidentiary weight — no deference to publication, no AI prior in either direction, numeric disagreements resolved on the merits rather than defaulting to the human value (new calibration rule + self-check item). Operator requirements for path neutralization and A/B randomization removed; outcome-information exclusion, style firewall, and symmetric checks retained. Output template columns renamed to Human / AI, matching the legacy `rating_taskN` format.
- 2026-07-03 — v1.4. Added §10a: optional cheap bias sensitivity check (labeled vs. de-identified re-run on settled tasks; ≤0.5/dimension → trust the disclosed protocol; systematic shift → isolation grading). No change to the grading prompt.
- 2026-07-03 — v2.0. Extended to a three-way comparison: HUMAN (`04`), AI-AUTO (`2.docx`, fully autonomous), AI-FU (`2-a.docx`, revised after human follow-up instructions). Rubric, weights, anchors, and red flags unchanged; each response scored as a standalone submission. Added a "no revision prior" rule (AI-FU not presumed better than AI-AUTO — human steering can also push toward agreeable answers), an AI-FU-vs-AI-AUTO consistency check (conclusion shifts without new evidence = selective-reporting red flag), and a mandatory "AI-AUTO → AI-FU Delta" output section classifying each change as substantive / cosmetic / regression to measure what human follow-up actually buys. Input file names fixed to the standardized bundle layout (`01`–`04`, `2.docx`, `2-a.docx`).
- 2026-07-03 — v2.1. Renamed AI report files to the final layout (`report.docx` = AI-AUTO, `report-f.docx` = AI-FU; task folders are numbered directories). Added `RUN_ALL.md`, a batch orchestration prompt: one subagent per task folder run in parallel, each given the verbatim rubric plus a task addendum (self-identification of target comments anchored to the HUMAN extracts, docx extraction guidance, fixed output path, machine-readable final message); orchestrator validates protocol compliance (recomputed totals, all flags marked) without touching scores, retries once, then aggregates `SUMMARY.md` (score matrix, per-dimension averages, red-flag frequencies, follow-up deltas).
- 2026-07-03 — v3.0. Extended the comparison from three-way to four-way: HUMAN (`04`), AI-GPT5.5 (`report.docx`), AI-KIMI (`report-k.docx`), and AI-GPT5.5-FU (`report-f.docx`). Rubric, weights, anchors, and red flags are unchanged; each response is still scored as a standalone submission. Added a "no cross-AI prior" rule so AI-KIMI is judged independently rather than against AI-GPT5.5. Updated orchestration to support optional AI response files: the four shared-background files are required, but any subset of the three AI `.docx` files may be present; missing responses are marked `N/A` and do not block evaluating the rest. Rating files use four-response score tables and an AI-GPT5.5 → AI-GPT5.5-FU Delta section whenever both GPT-5.5 files are present.
