# SPEC: plugin-cropcast

## Question
A new version of `predict_yield` (cropcast/forecast.py), using only information known before the season, reduces the out-of-sample mean absolute error of county yield forecasts by at least 10% relative to the best known simple method (current 5-year mean, linear trend, Olympic average, exponential smoothing).

## Why it matters
The commodities desk uses this forecast in the weekly note. A forecast that errs 10% less is worth acting on; a smaller gain is not enough to change how the desk works (stated by the requester).

## Metric
`mae`: mean absolute error in bu/ac, lower is better. Computed per county (mean over the target years) and averaged over the 80 counties; with the complete panel this equals the error over all county-years. Matches lab.json.

## Evaluator
`lab/eval/evaluate.py --split dev|holdout` loads `cropcast/forecast.py`, rolls through the target years (year by year, all counties), and calls `predict_yield(history, weather)` with only the past records of one county. It rejects non-finite or out-of-range predictions (exit code 2), and checks the source of forecast.py statically (allowed imports, no file or code-loading calls, no global state, at most 200 lines and 40 numeric literals). Prints `{"mae": ..., "per_unit": [80 county values]}`. Runtime: about 1 second.

## Data
Source: `data/yields.csv`, 80 counties, 1995-2024, columns yield, rain_mm, gdd (season totals). Split by time:
- dev (`lab/data/dev`): years 1995-2021. Forecast targets 2015-2021.
- holdout (`lab/data/holdout`): years 2022-2024, kept for the final confirmation. History for a holdout target also includes the dev years and earlier holdout years (past yields are known when a later season is forecast). The agent never reads or scores this split; it is used at most 3 times.
The holdout file was written by a script and never opened or summarised.

## Baseline
The starting solution is the current production code: mean of the last five reported yields of the county. `honestlab baseline` records its score. On dev it is expected near 8.2 bu/ac (measured 8.195 before freezing; the team's old backtest of 8.45 covers 2015-2024).

## Budget
Up to 15 experiments, each evaluated in about 1 second. No money or heavy compute. Editable file: `cropcast/forecast.py` only; numpy only, pure function (team rules in CLAUDE.md).

## What counts as a finding
At least 10% lower `mae` than the strongest registered reference method, on dev and again on the holdout (which is read only at the end), with a paired bootstrap over the 80 counties (alpha 0.05). The number is in lab.json (`min_effect` 0.10, relative). On dev the strongest reference is the 15-year linear trend (6.93 bu/ac), so a finding needs about 6.24 bu/ac or lower (current method: 8.20; the trend alone is already 15% better than it, which is a known method, not a finding).

## Prior work
Searched the web (standard search) for county-level yield forecast baselines. Findings, as reported by search summaries (full texts not read):
- farmdoc daily (Univ. of Illinois, April 2026), comparison of yield projection methods 2015-2024: a 5-year moving average excluding the minimum was the most accurate for dryland corn, soybeans and wheat (about 6.5% mean absolute error), ahead of the 5-year Olympic average (7.7%), OLS trend (8.2%) and the RMA method (8.9%). https://farmdocdaily.illinois.edu/2026/04/forecast-performance-of-rma-expected-yields-comparison-of-yield-projection-methods.html
- A North Dakota State study of county forecasts 2015-2024 found that simple recent-average models beat more complex ones.
- Detrending studies show linear, log-linear and ARIMA trends can differ by 6-8% in county risk measures.
So simple trailing averages are a hard bar to beat; this is why the bar is 10% over the best of several simple methods. Registered references: current 5-year mean (the baseline), linear trend over 15 years, 5-year Olympic average, exponential smoothing (alpha 0.4). A regression with season weather was not registered because season weather is hidden (see below).

## Known ways to cheat this metric
1. Using the weather totals of the target season (they are known only after the season). Closed: the evaluator passes rain_mm and gdd of the target year as NaN. Past years' weather in the history stays available.
2. Reading the real answers: opening data files, `data/yields.csv` (which contains the holdout years), or loading anything at run time. Closed: the evaluator rejects imports other than numpy and the standard maths modules, and calls such as open, exec, eval, np.load; agents are also forbidden from reading the holdout. Limit: a determined author could still hard-code constants learned elsewhere; the holdout confirmation exists to catch this.
3. Carrying future information between calls or memorising data (global state, lookup tables of yields). Closed: the evaluator calls year by year so earlier calls only ever contained earlier years; `global`/`nonlocal` are rejected; at most 40 numeric literals and 200 lines.
4. Tuning to the dev years until they look good. Not closed on dev; closed by the holdout, which is used once for a candidate and at most 3 times in total.
