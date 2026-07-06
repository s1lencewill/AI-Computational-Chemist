# Peer-review-replication benchmark

This folder contains the complete materials for the benchmark reported in the
AICC paper: real referees' computational requests on published Nature
Communications papers, with the original authors' computational answers
removed, posed to autonomous agents — and the full evaluation records that
score the agents' reports head-to-head against the authors' own calculations.

## Contents

```text
prompt.md                 the fixed task prompt given to the benchmarked agents
EVAL_PROMPT.md            the grading rubric (six dimensions, seven red flags,
                          zero-prior protocol, ±5-point tie band)
RUN_ALL.md                the batch-orchestration protocol for evaluator runs
EVAL_DESIGN_RATIONALE.md  the rubric's design rationale (withheld from graders
                          during evaluation; published here for transparency)
cases/                    the five evaluated cases (fixtures + agent reports)
evaluations/              the two end-to-end evaluator runs cited in the paper
```

## The five cases

Each case folder contains four PDFs — `01` main article, `02` supplementary
information and `03` peer-review/response file, each with all computational
content removed, plus `04`, the removed computational content itself (the
original authors' calculations; the HUMAN arm, withheld from the agents) —
and the agent reports: `report.docx` (autonomous AI-GPT5.5 arm) and
`report-f.docx` (AI-GPT5.5-FU, the human-steered follow-up).

| Case folder | Source paper (DOI) | System |
|---|---|---|
| `cases/case1_task7` | [10.1038/s41467-026-70476-2](https://doi.org/10.1038/s41467-026-70476-2) | Pt single atoms in liquid Ga (MLP-MD dispersion certification) |
| `cases/case2_task5` | [10.1038/s41467-026-68315-5](https://doi.org/10.1038/s41467-026-68315-5) | IDMP ligand anchoring on quasi-2D CsPbBr3 (slab DFT, defect DOS) |
| `cases/case3_task2` | [10.1038/s41467-026-70993-0](https://doi.org/10.1038/s41467-026-70993-0) | Pt1Ni single-atom-alloy lignocellulose hydrogenolysis (pathway DFT, COHP) |
| `cases/case4_task4` | [10.1038/s41467-026-69612-9](https://doi.org/10.1038/s41467-026-69612-9) | Pt clusters on hydroxyl-tuned TiO2 (DFT + Bader charge analysis) |
| `cases/case5_task11` | [10.1038/s41467-025-56188-z](https://doi.org/10.1038/s41467-025-56188-z) | Hydrous RuOx vs crystalline RuO2 in acidic OER (vacancy/proton energetics) |

The source articles, their supplementary information and their
transparent-peer-review files are open access under CC BY 4.0; the redacted
PDFs here are derivatives with the computational content removed so that the
reviewer questions remain answerable but the authors' answers are not visible.
Agents received `01`–`03` only; `04` is the grading reference.

## The evaluations

The full five-case evaluation was executed twice end-to-end under the identical
rubric and orchestration protocol, once per evaluator model. Run folders are
labelled by the git commit of the case data they scored:

| Run folder | Evaluator | Mean weighted totals (HUMAN / AI-GPT5.5 / AI-GPT5.5-FU) |
|---|---|---|
| `evaluations/evaluation-v2-a312cf8b-gpt5.5xhigh` | GPT-5.5 (high reasoning effort) | 54.7 / 65.5 / 72.2 |
| `evaluations/evaluation-v2-a312cf8b-fable5` | Claude (Fable 5) | 72.6 / 64.8 / 69.8 |

Each run contains five per-case rating files (`rating_case<N>.md`) and an
aggregate `SUMMARY.md`. Weighted totals recompute from the itemized dimension
scores in every rating file.

## Provenance notes

- **Published verbatim, paths normalized.** The rating files and summaries are
  the evaluators' original outputs. The only modification for publication is
  mechanical: absolute local file paths in file headers were normalized to
  repository-relative paths (`benchmark/cases/...`). No scores, red flags,
  commentary or verdicts were changed.
- **Four-response template.** The rubric and rating files follow a
  four-response template that includes an additional autonomous arm (AI-KIMI)
  collected during development. That arm is not part of the paper's analysis,
  and its response files are not distributed here; the corresponding sections
  in the rating files are retained unedited for record integrity.
- **Reproducing an agent run.** Give an agent the three redacted PDFs from a
  case folder plus `prompt.md`, with this skill collection installed and
  online access to the original publication disabled. Reproducing an
  evaluation run: follow `RUN_ALL.md`, which embeds `EVAL_PROMPT.md` verbatim;
  keep `EVAL_DESIGN_RATIONALE.md` away from the grader.
