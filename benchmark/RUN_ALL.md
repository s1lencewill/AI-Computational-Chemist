You are the **orchestrator** for a batch of standardized four-way evaluations. Do not perform any evaluation yourself — delegate each case to a subagent and aggregate the results.

## Step 1 — Enumerate and validate

List the case folders in the current directory: folders whose names start with `case<C>` (`C` = case number, e.g. `case1` … `case7`; a folder name may carry a descriptive suffix, which is not part of the identifier). Cases are identified as `case<C>` everywhere — in prompts, rating filenames, and the summary. Enumerate by pattern rather than hard-coding the list, so newly added cases are picked up automatically.

**Never enumerate or read `evaluations/` or any `evaluations-*/` folder** — those hold outputs of previous evaluation runs, and their contents must not reach any evaluator.

**Required files** (a case cannot be evaluated without these):

- `01_main_article_calculation_removed.pdf`
- `02_SI_calculation_removed.pdf`
- `03_response_letter_calculation_removed.pdf`
- `04_removed_calculation_content_original_extracts.pdf`

**Optional AI response files** (evaluate each one that is present; missing files are recorded but do not block evaluating the others):

- `report.docx` (AI-GPT5.5)
- `report-k.docx` (AI-KIMI)
- `report-f.docx` (AI-GPT5.5-FU)

Skip a folder only if it is missing one of the four required files or if it contains no AI response files at all. Record the reason for any skipped folder in the final summary. Do not silently drop folders.

Pick a fresh output folder for this run: `evaluations/` if it does not yet exist, otherwise `evaluations-<k>/` with the next unused suffix (e.g. `evaluations-2/`). Never write into an existing run's folder. All evaluation outputs (rating files and the summary) go into this run's output folder — never into the case folders.

Read `EVAL_PROMPT.md` once — you will embed its full text in each subagent prompt.

## Step 2 — Launch one subagent per case, all in parallel

Launch all subagents **in a single message** so they run concurrently. Each subagent is a general-purpose agent whose prompt consists of:

1. The **complete verbatim text of `EVAL_PROMPT.md`**, followed by
2. This per-case addendum (fill in the placeholders):

```
--- CASE ASSIGNMENT ---

Your assigned case is case<C>; its folder is: <absolute path to the case folder>. Work ONLY with the files inside that folder. Do not open anything else in the parent directory — in particular, `evaluations/` and `evaluations-*/` folders contain previous evaluation results and reading them would contaminate your independent judgment; `EVAL_DESIGN_RATIONALE.md` and `RUN_ALL.md` are orchestration files, not inputs.

Additional instructions:

1. TARGET REVIEWER COMMENT(S): not pre-filled for this batch. Determine them yourself:
   - The HUMAN extracts (04) show which comment(s) the original calculations responded to.
   - The AI reports state which comment(s) they address.
   - Cross-check all present responses against the reviewer comments in 03.
   If the present responses disagree on scope, evaluate against the comment(s) that the HUMAN extracts respond to (that defines the case), score each response on how well it addresses those, and record the discrepancy under "Materials compared".

2. MISSING FILES: before reading, check which of `report.docx`, `report-k.docx`, and `report-f.docx` exist in the folder. Record any missing AI response files under "Materials compared" and omit them from the scoring tables (mark as `missing` or `N/A`). The AI-GPT5.5 → AI-GPT5.5-FU Delta section is required only if both `report.docx` and `report-f.docx` are present.

3. READING THE FILES: the PDFs can be read directly. For the .docx files that exist, extract the text and tables, e.g.:
   - `unzip -p report.docx word/document.xml` and parse the XML, or
   - `pandoc report.docx -t markdown` or python-docx if available.
   Do this for each present file among `report.docx` (AI-GPT5.5), `report-k.docx` (AI-KIMI), and `report-f.docx` (AI-GPT5.5-FU).
   Extract the DATA TABLES faithfully — the selective-reporting and internal-consistency checks depend on comparing narrative numbers against complete tables. If a table or figure cannot be extracted, say so explicitly in the rating file rather than guessing its contents.

4. OUTPUT: write the finished evaluation to `<absolute path to this run's output folder>/rating_case<C>.md` — NOT into the case folder — following the output format in the rubric exactly.

5. FINAL MESSAGE: your final response must contain ONLY: (a) the Overall Scores table (weighted totals /100 and /10 for every present response: HUMAN, AI-GPT5.5, AI-KIMI, AI-GPT5.5-FU), (b) the verdict ranking line (include only ranked responses; omit missing ones), (c) a count of red flags found per present response, and (d) the path of the rating file you wrote. No other prose — the orchestrator aggregates from this.
```

Do not summarize, shorten, or paraphrase `EVAL_PROMPT.md` when embedding it — the calibration rules and anchors only work verbatim.

## Step 3 — Collect and retry

Wait for all subagents. If one fails or returns an unusable result, re-launch it once with the same prompt. If it fails again, mark the case as "not evaluated" in the summary — do not fabricate scores and do not evaluate it yourself.

Spot-check each returned rating file for protocol compliance (not for scores): the file exists; all six dimensions are scored for every response present; the totals match the weighted sums (recompute them); all 7 red flags are marked for every response present; and the Delta section exists if both AI-GPT5.5 and AI-GPT5.5-FU are present. If a file is non-compliant, send the subagent back once to fix the specific defect (via a follow-up message to that agent, or one re-launch). Do not adjust any scores yourself.

## Step 4 — Aggregate

After all cases complete, write `SUMMARY.md` in this run's output folder:

1. **Score matrix**: one row per case (`case<C>`); columns: case, HUMAN total, AI-GPT5.5 total, AI-KIMI total, AI-GPT5.5-FU total (out of 100; `N/A` for missing responses), verdict ranking (only among present responses). Mark pairs within 5 points as ties (≈).
2. **Per-dimension averages**: mean score per dimension for each of the four response types across all cases where that response was present.
3. **Red-flag frequency table**: per red-flag type, how many cases each present response type triggered it in.
4. **AI-GPT5.5 → AI-GPT5.5-FU**: for each case where both are present, one line from the rating's Delta section on what the follow-up bought (substantive / cosmetic / regression).
5. **Caveats**: cases skipped or not evaluated and why; any missing AI response files per case; any rating file whose compliance had to be fixed.

Keep `SUMMARY.md` to facts derived from the rating files; no new judgments. Your final message to the user: the score matrix, the biggest cross-case pattern (one or two sentences), and pointers to this run's `SUMMARY.md` and per-case rating files.
