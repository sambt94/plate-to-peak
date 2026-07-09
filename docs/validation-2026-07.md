# Validation — 2026-07 (Sam's own data, local)

Real Clarity export (5 days, 1482 EGVs, no sensor gaps) + real meal diary vs. the
hand-curated phase2 answer key (8 meals covering the first 3 days of the window).

Result: matched 5/8 key meals, **0 missed real spikes**, **1 false blame**.

- 3 key meals were unmatchable because the diary gave them no placeable time
  (excluded from pipeline input per the no-guessing rule). The one spiked meal
  among them was still surfaced independently by orphan detection.
- The 1 false blame is the answer key's documented exercise confound: a
  zero-carb meal eaten immediately after intense exercise, where the
  post-exercise rebound marginally crossed the threshold inside the causal
  window. The key marks it not-spiked (elevation caused by exercise, not the
  meal). Window/baseline arithmetic cannot distinguish exercise rebound from a
  food response, so no tuning was applied — this is a known, documented limit,
  and the skill's LLM adjudication layer (activity context) is the intended
  mitigation, not tighter defaults.
- All 9 orphan spikes detected were genuine unexplained-or-exercise peaks; the
  three largest known real peaks all appeared (as orphans, since they were
  exercise-driven or pre-window).

No defaults were changed. Defaults: window [15,90] min, threshold 7.8 mmol/L,
baseline lookback 15/30 min, orphan dedupe 45 min.

Verdict: DONE_WITH_CONCERNS — the concern is exercise confounding only, which
is out of scope for the deterministic layer by design.
