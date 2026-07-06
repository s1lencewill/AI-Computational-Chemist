# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""Recompute the per-arm means cited in the manuscript (main Table 1,
Supplementary Table 3 and the evaluator-replication paragraph) from the
per-case weighted totals of the two cited evaluation-v2 runs under benchmark/evaluations/:

  evaluation-v2-a312cf8b-fable5       (Claude evaluator — primary)
  evaluation-v2-a312cf8b-gpt5.5xhigh  (GPT-5.5 evaluator)

Score matrices are hard-coded from each run's SUMMARY.md §1 with per-block
provenance comments, mirroring fig6.py. The AI-KIMI response arm and the Kimi
evaluator run were not part of the paper analysis and are not distributed
in this repository. The script asserts that
recomputed means match the published SUMMARY / manuscript values after
1-decimal rounding.
"""

ARMS = ["HUMAN", "AI-GPT5.5", "AI-GPT5.5-FU"]

# Per-case weighted totals (cases 1-5).
RUNS = {
    # evaluation-v2-a312cf8b-fable5/SUMMARY.md §1
    "Claude": {
        "HUMAN":        [82.0, 70.0, 82.0, 65.0, 63.8],
        "AI-GPT5.5":    [54.8, 79.5, 58.5, 67.3, 64.0],
        "AI-GPT5.5-FU": [65.8, 81.5, 68.5, 67.3, 65.8],
    },
    # evaluation-v2-a312cf8b-gpt5.5xhigh/SUMMARY.md, Score Matrix
    "GPT-5.5": {
        "HUMAN":        [65.5, 45.8, 66.5, 50.5, 45.0],
        "AI-GPT5.5":    [65.8, 66.5, 53.5, 74.8, 66.8],
        "AI-GPT5.5-FU": [77.0, 74.3, 60.8, 74.8, 74.0],
    },
}

# Published means: SUMMARY.md of each run == manuscript main Table 1 (primary
# row doubles as Supplementary Table 3's Mean row).
PUBLISHED = {
    "Claude":  {"HUMAN": 72.6, "AI-GPT5.5": 64.8, "AI-GPT5.5-FU": 69.8},
    "GPT-5.5": {"HUMAN": 54.7, "AI-GPT5.5": 65.5, "AI-GPT5.5-FU": 72.2},
}


def main() -> None:
    means: dict[str, dict[str, float]] = {}
    for run, totals in RUNS.items():
        means[run] = {}
        for arm in ARMS:
            vals = totals[arm]
            m = sum(vals) / len(vals)
            means[run][arm] = m
            pub = PUBLISHED[run][arm]
            ok = abs(round(m, 1) - pub) < 0.051
            print(f"{run:18s} {arm:13s} n={len(vals)} "
                  f"mean={m:6.2f} published={pub:5.1f} {'OK' if ok else 'MISMATCH'}")
            assert ok, (run, arm, m, pub)

    # Cross-evaluator spreads quoted in the evaluator-replication paragraph.
    print()
    for arm in ARMS:
        vs = [means[r][arm] for r in RUNS]
        spread = max(vs) - min(vs)
        print(f"spread across evaluators {arm:13s} "
              f"{min(vs):5.1f}–{max(vs):5.1f}  Δ={spread:4.1f}")

    # Case-level claims: case 2 AI win and case 4 AI >= HUMAN, under every run.
    for run, totals in RUNS.items():
        assert totals["AI-GPT5.5"][1] > totals["HUMAN"][1] + 5, run   # case 2
        assert totals["AI-GPT5.5"][3] >= totals["HUMAN"][3], run      # case 4

    # Headline claims: FU parity-or-better under both evaluators (>= HUMAN - 5,
    # the rubric's tie band); autonomous agent strictly ahead under GPT-5.5.
    assert means["Claude"]["AI-GPT5.5-FU"] >= means["Claude"]["HUMAN"] - 5
    assert means["GPT-5.5"]["AI-GPT5.5-FU"] > means["GPT-5.5"]["HUMAN"] + 5
    assert means["GPT-5.5"]["AI-GPT5.5"] > means["GPT-5.5"]["HUMAN"] + 5
    print("\nall published means, case-level and headline claims verified")


if __name__ == "__main__":
    main()
