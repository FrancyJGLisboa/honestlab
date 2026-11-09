# SPEC: clima_publico

## Question
Does adding the day-ahead weather forecast (temperature and rain predicted the day before)
reduce the daily error of tomorrow's sales forecast for an ice cream shop in Pinheiros,
São Paulo, by at least 10% compared with the strongest weather-free method?

## Why it matters
The owner buys stock from tomorrow's forecast. Today she uses the mean of the last 4 sales
on the same weekday. She said 10% less error would already help (less waste, fewer
stockouts).

## Metric
`mae`: mean absolute error per day, in the sales units of the owner's spreadsheet
(column `vendas`). Minimize. `per_unit` = mean absolute error of each scored Monday–Sunday week.

## Evaluator
`eval/evaluate.py --split dev|holdout` walks forward day by day. For each day D it calls
`src/model.py: predict(history, day)` with all days before D (including sales) and day D
without sales (date, weekday, holiday flag, weather forecast made the day before). The
prediction must be a finite number in [0, 10000], otherwise the evaluator exits with an
error. Only full Monday–Sunday weeks are scored; other days only join the history. Dev scores
2024-01-29..2024-12-29 (336 days, 48 weeks; January before that is history only).
Holdout uses all dev days as history and scores the full weeks of 2025; each holdout day
joins the history only after it has been predicted. Runtime: a few seconds.

## Data
- Sales: `vendas.csv` from the owner, daily 2024-01-01..2025-12-31 (731 days): date,
  weekday, holiday flag, sales. Not changed.
- Weather: Open-Meteo Previous Runs API, https://previous-runs-api.open-meteo.com/v1/forecast
  (docs: https://open-meteo.com/en/docs/previous-runs-api), model `gfs_seamless`
  (NOAA GFS), point -23.5629, -46.6919 (Pinheiros), timezone America/Sao_Paulo,
  downloaded 2026-11-09. Variables `temperature_2m_previous_day1` and
  `precipitation_previous_day1`: hourly values as forecast ~24 h earlier. Aggregated per
  day into `prev_tmax`, `prev_tmedia`, `prev_chuva_mm` (daily sum) and
  `prev_horas_chuva_aberto` (hours 11h–21h with ≥0.1 mm). Days with incomplete forecast
  (2024-01-01..2024-01-19, 19 days) are left empty (None).
  Terms: Open-Meteo data is CC BY 4.0; the free API is for non-commercial use, so
  ongoing commercial use needs an Open-Meteo API subscription or NOAA GFS directly
  (public domain).
- Fetch and join script: `notes/fetch_weather.py vendas.csv notes/tmp`.
- Split by time: dev = 2024 (`data/dev/dev.csv`), holdout = 2025 (`data/holdout/final.csv`,
  sealed, never inspected).

## Baseline
`src/model.py` = the owner's current method: mean of the last 4 sales on the same weekday.
Dev MAE = 32.71.

## Budget
Up to 15 experiments, each a few seconds of CPU; no money cost. Standard library only.

## What counts as a finding
A model that uses the weather forecast must have MAE at least 10% lower (relative) than
the strongest registered weather-free reference (currently exponential smoothing with
weekday profile and holiday adjustment, dev MAE = 28.30, so ≤ ≈25.5), on dev and then on
the sealed 2025 holdout, with honestlab's paired bootstrap over weeks (alpha 0.05).
lab.json: `min_effect` 0.10 relative, `compare_to` strongest.

## Prior work
Searched the web (2026-11-09, "ice cream daily sales forecasting temperature weather
regression versus seasonal naive"). Ice cream sales are widely modelled with linear
regression on temperature (e.g. AIUB conference paper "Weathering the Forecast", linear
regression vs XGBoost on temperature-driven ice cream sales,
https://dspace.aiub.edu/jspui/handle/123456789/2663; University of Reading climate
intelligence course, https://futurelearn.com/info/courses/climate-intelligence-using-climate-data-to-improve-business-decision-making/0/steps/300833).
No published benchmark against seasonal naive was found. Standard forecasting baselines
(Hyndman & Athanasopoulos, Forecasting: Principles and Practice): seasonal naive,
moving averages, exponential smoothing (Holt-Winters). Registered references:
`semana_passada` (seasonal naive, dev 40.06), `media8` (mean of last 8 same weekday,
30.53), `suavizacao` (exponential smoothing × weekday profile × holiday factor, 28.30).

## Known ways to cheat this metric
1. Using the actual sales of the day being predicted: the evaluator removes `vendas` from
   `day` and passes only earlier days in `history` (deep copies, so the model cannot
   modify the evaluator's data).
2. Using the actual (observed) weather of the day instead of a forecast: the data only
   contains the forecast made ~24 h before, never observed weather.
3. Reading the data files or future rows directly from src/: the model receives data only
   through `predict`; reading files from src is forbidden and reviewed before any finding.
   Overfitting to 2024 is checked by the sealed 2025 holdout.
4. Returning absurd values or NaN: the evaluator rejects non-finite or out-of-range output.
