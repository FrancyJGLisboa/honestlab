# Proposals (labloop-scout)

Repo: cropcast, county yield forecasting, numpy only (CLAUDE.md: pure functions, IO only in `cropcast/io.py`).
Data: `data/yields.csv`, 80 counties x 30 years (1995-2024), columns yield, rain_mm, gdd.
Existing metric: `scripts/backtest.py` prints rolling-origin MAE (bu/ac), currently **8.448** over 800 county-years (2015-2024), runs in well under a second.
Tests: 2 pass, 1 fails (`tests/test_clean.py::test_flags_extreme_value`, see Rejected).

## 1. Better `predict_yield` (frameable, recommended first)

- **Target:** `cropcast/forecast.py` (`predict_yield`). Nothing else.
- **Metric:** MAE in bu/ac, minimize. Already exists in `scripts/backtest.py`. The evaluator needs to reimplement that loop, reading only the split's data, and also print `per_unit` (per county-year absolute errors, or per-county MAE).
- **Data and holdout:** the panel has 80 counties. Split by county (e.g. 50 dev / 30 holdout), written to `lab/data/dev` and `lab/data/holdout`. Keep the 2015-2024 rolling-origin protocol so there is no time leakage. Risks: neighbouring counties are correlated (shared weather), so a county split leaks less than a random row split but more than a split by region. Check whether county IDs encode geography. Splitting by time as well (holdout = 2020-2024 only) is stricter but costs power.
- **Cost per evaluation:** about 1 s (I ran the full 800-prediction backtest). Thousands of experiments are feasible.
- **Ways to cheat:** use `weather` of the target year only as permitted (it is known at forecast time) but never `yield` of the target year. The evaluator must pass `history` truncated strictly before the target year (as the backtest does) and not expose the full panel. Hardcoding county constants or fitting on the whole file at import time would leak, so the solution must have no data files and must only use `history`/`weather`. Also check for NaN or non-finite output and non-float return types.
- **Why it matters:** the commodities desk's weekly note depends on this forecast. The baseline is a 5-year mean with no trend and no weather. Plausible gains of 10-30% MAE are meaningful.
- **Prior work hint:** per-county linear trend, shrinkage toward the cross-county mean (pooled/hierarchical), detrended weather regressions (rain, GDD, quadratic terms), ridge regression, robust (median) trends, ensembles. Yield-forecasting literature is large, so the prior-work search should be easy.
- **Verdict:** frameable. Main risk: with only 30 years per county, weather-model gains may be small and noisy, so use a paired bootstrap on per-county-year errors and a pre-registered minimum effect (e.g. 0.3 bu/ac absolute). `predict_yield` only sees one county's history, so pooling across counties is not possible unless the signature changes. That changes the contract, so decide it at framing.

## 2. Outlier screening `flag_outliers` (needs proxy)

- **Target:** `cropcast/clean.py`.
- **Metric:** F1 or precision/recall against labeled outliers. No labels exist, so a proxy is needed: inject synthetic outliers into the dev/holdout series with a seeded generator, or use downstream backtest MAE after cleaning the history inside `predict_yield`.
- **Cost:** about 1 s. **Cheat:** thresholds tuned to the injection scheme. **Verdict:** needs proxy (synthetic injection, or backtest MAE of cleaning + forecast). Main risk: the proxy defines the answer. Prior work: MAD / modified z-score, Hampel filter, IQR fences, leave-one-out z-score.

## 3. Forecast runtime or robustness (weak)

- Reduce `predict_yield` runtime while keeping MAE fixed: the metric exists, but runtime is already negligible and nobody benefits. Verdict: reject-ish / `needs proxy`.

## Rejected

- `cropcast/report.py` `markdown_table`: formatting, no automatic verifier ("make it nicer").
- Fixing `tests/test_clean.py::test_flags_extreme_value`: not a research loop. With n=10 the largest possible population z-score is sqrt(n-1) = 3.0, so with `z=3.0` and a strict `>` the test cannot pass (the 100 has z=2.9992). It is a bug in the test or the threshold, for a human to decide. Flagged because the baseline test suite is red.
- Panel I/O (`cropcast/io.py`): no metric beyond correctness.
- Code cleanliness or docs: no verifier.

## Ranking

1. Forecast accuracy (verifiable, existing metric, sub-second, high impact).
2. Outlier screening (only with a synthetic proxy; lower impact).
3. Runtime (low impact).

Frame first: **#1**. Biggest uncertainty to settle during framing: the dev/holdout county split, and whether `predict_yield` may see other counties.
