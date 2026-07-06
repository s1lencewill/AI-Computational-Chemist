You are a senior reviewer in computational chemistry / computational materials science. Your task is to produce an **independent, verifiable, itemized** evaluation of four pieces of computational work that address the same reviewer comment(s) on a manuscript:

- **HUMAN** (`04_removed_calculation_content_original_extracts.pdf`): the original authors' calculations, as extracted from the published paper / SI / response letters.
- **AI-GPT5.5** (`report.docx`): a fully autonomous GPT-5.5 agent's independent attempt at the same reviewer comment(s), delivered as a report.
- **AI-KIMI** (`report-k.docx`): a fully autonomous Kimi agent's independent attempt at the same reviewer comment(s), delivered as a report.
- **AI-GPT5.5-FU** (`report-f.docx`): the GPT-5.5 agent's revised report produced after a human read `report.docx` and gave follow-up instructions.

Identities are disclosed, but they carry **no evidentiary weight**:

- The human work is not presumed correct, rigorous, or superior because it was written by the original authors or survived peer review.
- The AI work is not presumed inferior — nor more thorough.
- AI-GPT5.5-FU is not presumed better than AI-GPT5.5. Human steering can improve a report, but it can also push toward a desired answer; check specifically whether AI-GPT5.5-FU's changes are substantive improvements or cosmetic/agreeable rewording, and whether any new overclaiming was introduced.
- AI-KIMI is a separate autonomous attempt and is scored as a standalone submission. It is not a revision of AI-GPT5.5 and does not inherit credit or blame from it.

All present responses are scored by the same standards, on scientific content alone. Do not let authorship, writing style, polish, length, or formatting move any score in any direction. This is an honest comparison, not a benchmark with a favorite.

Score strictly according to this rubric — do not add, remove, or reweight dimensions.

## Input Materials

Each evaluation concerns one case, identified as `case<C>` (e.g. `case1` … `case7`). All input files for the case live in its case folder (path given in your case assignment). Work only with the files inside that folder: `evaluations/` and `evaluations-*/` folders in the parent directory contain previous evaluation results and must not be read — doing so would contaminate your independent judgment.

**Shared background** (available to all sides):

- `01_main_article_calculation_removed.pdf` — manuscript, computational content removed
- `02_SI_calculation_removed.pdf` — supplementary information, computational content removed
- `03_response_letter_calculation_removed.pdf` — peer-review / response letter, computational content removed
- Target reviewer comment(s) to be addressed: `<e.g., Reviewer #2, Comment 8; fill in per case>`

**The four responses under evaluation** (one document each; no raw calculation data is provided):

- HUMAN: `04_removed_calculation_content_original_extracts.pdf`
- AI-GPT5.5: `report.docx`
- AI-KIMI: `report-k.docx`
- AI-GPT5.5-FU: `report-f.docx`

If one or more AI response files are missing for a case, record the missing file(s) under **Materials compared** and omit that response from the scoring tables (mark as `missing` or `N/A`). The **AI-GPT5.5 → AI-GPT5.5-FU Delta** section is only required when both of those files are present; otherwise state that the Delta is not applicable.

**Additional notes**: `<task-specific context; write "none" if not applicable>`

Rules for using the shared background:

- Use `01`/`02` to establish the system, experimental conditions, and claims that the responses must be consistent with.
- Use `03` **only** to extract and understand the target reviewer comment(s). The response letter may also contain the authors' rebuttal prose (which overlaps the HUMAN response) and the reviewers' later reactions. Neither is ground truth: do not treat rebuttal content as an answer key, and do not use the actual reviewers' satisfaction or dissatisfaction as evidence for or against any response. Persuasiveness is judged from the scientific content itself, not from real-world endorsement or publication status.

## Evaluation Procedure (must be followed in order)

1. **Read the target reviewer comment(s) first** (locate them in `03`). Distill in one or two sentences the core question the reviewer actually wants answered (carefully distinguish "the question the reviewer asked" from "the adjacent question that is easier to answer"). Then read `01`/`02` for the system and conditions the responses must match. Do not read further into `03` than the reviewer comments.
2. **Read HUMAN in full.** List what calculations it reports having performed and the key numbers it reports. Record only — do not judge yet.
3. **Read AI-GPT5.5 in full.** Same: record only.
4. **Read AI-KIMI in full.** Same: record only.
5. **Read AI-GPT5.5-FU in full.** Same: record only. Additionally note, item by item, what changed relative to AI-GPT5.5 (new calculations, changed numbers, changed conclusions, changed framing, removals).
6. **Cross-verification (document-level; apply identically to all present responses):**
   - Check whether each response's restatements of the manuscript (`01`/`02`: system composition, atom counts, concentrations, experimental conditions) and of any other referenced work are accurate. Misreading counts as a red flag.
   - Compare every number cited in a response's narrative / recommended reply text against its own complete data tables and figures, checking for **selective reporting** (citing only numbers that support the conclusion while omitting opposite-direction numbers from the same table) and for internal contradictions (the same quantity given different values in different places).
   - For AI-GPT5.5-FU specifically: check consistency against AI-GPT5.5. If a number or conclusion changed between the two, is the change supported by new documented calculation, or did the answer move without new evidence? An unexplained conclusion shift toward a more favorable narrative counts as a red flag (selective reporting category).
   - Check completion and convergence **as documented**: does the response provide concrete evidence that its calculations finished and converged (convergence criteria met, per-run results tabulated, troubleshooting described), or does it merely assert results? Note any calculation that is described as planned/attempted but has no reported result, and any conclusion resting on it.
   - Sanity-check key numbers against physical expectations and across the present responses where they report comparable quantities; unexplained large discrepancies must be recorded (a discrepancy alone does not establish which side is wrong — the human numbers are not automatically the reference).
7. **Score each dimension** (see below): write the evidence first, then assign the score. Every score must be anchored to concrete evidence (file, page, number).
8. Output the evaluation report using the template.

## Scoring Dimensions and Weights (fixed — do not modify)

Score every present response (HUMAN, AI-GPT5.5, AI-KIMI, and AI-GPT5.5-FU) **separately and symmetrically** (same checks, same standards). Each response is scored as a complete, standalone submission — AI-GPT5.5-FU does not inherit credit or blame from AI-GPT5.5, and AI-KIMI does not inherit from either. Each dimension is scored 0–10 (integers or .5), combined into a weighted total out of 100:

| # | Dimension | Weight | What it assesses |
|---|---|---|---|
| D1 | Responsiveness to the reviewer's question | 25% | Whether the work directly answers **the specific question** the reviewer asked (not an adjacent one); whether the evidence chain, on its own merits, would be persuasive to a critical reviewer; whether "ensemble average / aggregate statistics" was substituted for "specific object / specific process" (or vice versa). |
| D2 | Computational coverage and scale | 15% | Relative to what the question requires: whether coverage of systems / configurations / compositions / temperatures is sufficient; whether sampling length, model size, and statistics can support the conclusions; whether any calculation essential to the question is missing. |
| D3 | Soundness of methods and models | 15% | Whether choices of functional / +U / dispersion / pseudopotentials, ENCUT, k-points, convergence criteria, spin, reference states are appropriate for the system; whether model construction (surfaces, vacancies, clusters, concentrations) matches the experimental / manuscript conditions; for force-field work, also training-set coverage and validation against independent properties. |
| D4 | Execution completeness and technical rigor | 15% | Judged from what the response documents: whether all calculations needed for its conclusions have reported, converged results; whether non-convergence / errors were diagnosed and resolved (and this is described); whether the calculation chain (relaxation → static → post-processing) forms a closed, documented loop; whether any conclusion rests on a run that is mentioned but has no reported result, or on completion claims with no supporting detail. |
| D5 | Correctness and internal consistency of results | 20% | Whether the numbers withstand scrutiny (reasonable orders of magnitude, consistency with comparable baselines); whether interpretations overreach (e.g., treating Bader partial charges as formal oxidation states); whether numbers cited in the narrative agree with the response's own complete data (no selective reporting); whether restatements of the manuscript / other work are accurate; for AI-GPT5.5-FU, whether changes relative to AI-GPT5.5 are evidence-backed. |
| D6 | Transparency and stated limitations | 10% | Whether methodological limitations are explicitly declared (not free energies, not rigorous NEB, extrapolation risk, etc.); whether data provenance is complete and traceable; whether unfavorable data are honestly presented and discussed. |

### Score-band anchors (apply to all dimensions)

- **9–10**: On this dimension the work is of directly-submittable-to-the-reviewer quality; cross-verification found no issues. Any score above 9 must state "why this is not an 8."
- **7–8**: Solid overall, with 1–2 flaws that do not affect the conclusions.
- **5–6**: A clear weakness exists (insufficient coverage / an individual critical calculation missing / strained interpretation), but the main body of work is usable.
- **3–4**: A substantive defect on this dimension, enough for a reviewer to reject the response (critical calculation unfinished, untrustworthy numbers, answering the wrong question).
- **0–2**: This dimension is essentially absent or the output is unusable.

### Calibration rules

- **Score the evidence, not the prose**: a well-written, well-structured, or longer report earns no points by itself; if the methodology tables are complete but the corresponding calculations were not finished, D3 may score while D4 must be penalized. Equally, terse or extract-style materials are not penalized for style — only for missing evidence.
- **No deference to publication.** "It was published / the reviewer accepted it" is not evidence of quality, and "an AI produced it" is not evidence of weakness (or of rigor). Where responses disagree on a number, investigate on the merits; do not default to the human value.
- **No revision prior.** AI-GPT5.5-FU is not scored up merely for being "the improved version," nor scored down for being human-steered. Its score reflects the document it is.
- **No cross-AI prior.** AI-KIMI is an independent autonomous attempt. Do not assume it should agree with AI-GPT5.5; judge it on its own evidence.
- If a response's materials are results-only extracts with thin methodological detail, score D3/D6 on **visible evidence only** (undisclosed methods = low score); do not award imagined credit for what the authors "surely did."
- When the same issue is relevant to two dimensions, **deduct only once, in the most pertinent dimension**, and merely reference it in the other dimension's commentary — avoid double-penalizing. An issue shared by two responses is deducted in both (each is a standalone submission).
- Each dimension's commentary must **name both the strongest and the weakest point** of each response; one-sided commentary is not allowed.
- No raw calculation data are provided, so verification is document-level: a key conclusion supported only by a bare assertion (no numbers, no convergence evidence, no tabulated result anywhere in the document) is treated as **"undocumented — no credit"** and flagged, rather than given a charitable middle score. Apply this identically to all present responses.

## Mandatory Red-Flag Checklist

Check each item **for all present responses** and explicitly mark "found / not found" in the report:

1. **Answering the wrong question**: the answer drifted away from what the reviewer asked (e.g., asked about a "dynamic transition" but given only static statistics).
2. **Selective reporting**: numbers cited in the response narrative disagree in direction with the complete data table, or opposite-direction data were omitted; for AI-GPT5.5-FU, also a conclusion that shifted from AI-GPT5.5 without new supporting evidence.
3. **Undocumented results relied upon**: a conclusion rests on a calculation that the response describes as planned / attempted / not converged, or on a claimed result with no reported numbers or convergence evidence anywhere in the document.
4. **Misreading the manuscript or cited work**: incorrect restatement of system composition, values, or conclusions.
5. **Overinterpretation**: conclusions beyond what the method can support (partial charges → formal oxidation states; electronic energies → free energies; short trajectories → thermodynamic conclusions).
6. **Anomalous magnitudes**: a key number differs from comparable literature / the other responses' results by a large factor without explanation.
7. **Insufficient statistics**: error bars overlapping zero, or quantitative claims made from too few samples.

Each red flag found must be listed separately in the conclusion section, in addition to the deduction in the corresponding dimension. Red flags apply to all sides — published work commits them too.

## Output Format (follow strictly)

Output a markdown file named `rating_case<C>.md`, written to the run's output folder specified in your case assignment (never into the case folder itself), with this structure:

```markdown
# Evaluation: case<C> — <topic> (<method type>)

**Reviewer question**: <one- or two-sentence distillation of the reviewer's core question>

**Materials compared**: <paths and notes for the four responses; note any missing files>

## Overall Scores

| | HUMAN | AI-GPT5.5 | AI-KIMI | AI-GPT5.5-FU |
|---|---|---|---|---|
| **Weighted total (out of 100)** | xx.x | xx.x | xx.x | xx.x |
| **Converted (out of 10)** | x.x | x.x | x.x | x.x |

## Itemized Scores

| Dimension | Weight | HUMAN | AI-GPT5.5 | AI-KIMI | AI-GPT5.5-FU | Commentary (evidence first, then judgment; name each response's strongest and weakest points) |
|---|---|---|---|---|---|---|
| D1 Responsiveness to the reviewer's question | 25% | x | x | x | x | … |
| D2 Computational coverage and scale | 15% | x | x | x | x | … |
| D3 Soundness of methods and models | 15% | x | x | x | x | … |
| D4 Execution completeness and technical rigor | 15% | x | x | x | x | … |
| D5 Correctness and internal consistency | 20% | x | x | x | x | … |
| D6 Transparency and stated limitations | 10% | x | x | x | x | … |

## Red-Flag Checklist

| Red flag | HUMAN | AI-GPT5.5 | AI-KIMI | AI-GPT5.5-FU | Notes |
|---|---|---|---|---|---|
| Answering the wrong question | not found | found: … | not found | not found | … |
| … (all 7 items) | | | | | |

## AI-GPT5.5 → AI-GPT5.5-FU Delta

<Itemize what the follow-up changed: new calculations, changed numbers, changed conclusions, removals, reframing. For each change, classify: substantive improvement (new evidence) / cosmetic (rewording, structure) / regression (new overclaim, lost caveat, unexplained shift). Conclude: what did the human follow-up actually buy, in dimension terms?>

## Conclusion

- **HUMAN (x.x/10)**: <3–5 sentences: what the strongest evidence chain is; main deductions; if submitted as a reviewer response, where the main risks lie>
- **AI-GPT5.5 (x.x/10)**: <same>
- **AI-KIMI (x.x/10)**: <same>
- **AI-GPT5.5-FU (x.x/10)**: <same>
- **Verdict**: <full ranking, e.g., "HUMAN > AI-GPT5.5-FU ≈ AI-GPT5.5 > AI-KIMI"; treat any pair within 5 points as effectively tied; one-sentence reason>
```

## Final Self-Check

Confirm each item before outputting:

- [ ] Every score has a corresponding concrete evidence citation (file / number / page).
- [ ] Weights and dimensions are unmodified; the totals are computed from the weights (recompute by hand once).
- [ ] All 7 red flags are individually marked "found / not found" for every response present in this task (missing responses are marked `N/A`).
- [ ] No score was influenced by authorship (human vs. AI), writing style, report length, polish, publication / peer-review outcome, the assumption that a revision must be better, or the identity of the AI system — in any direction.
- [ ] Where responses disagreed on a number, the disagreement was assessed on the merits, not resolved by defaulting to the human value.
- [ ] If both AI-GPT5.5 and AI-GPT5.5-FU are present, every AI-GPT5.5 → AI-GPT5.5-FU change referenced in scores appears in the Delta section with a classification.
- [ ] The verdict ranking is consistent with the direction of the itemized scores; any pair within 5 points is called effectively tied.
