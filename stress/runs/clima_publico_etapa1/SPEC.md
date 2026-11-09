# SPEC: clima_publico

## Question
Does a day-ahead forecast that uses the public weather forecast (temperature and rain) for
Pinheiros, Sao Paulo, reduce the mean absolute error of next-day ice-cream sales by at least
10% compared with the strongest weather-free method (the shop's 4-same-weekday average and
the standard benchmarks below)?

## Why it matters
The owner buys stock the night before based on the expected sales. They said an error
about 10% lower is enough to help buy the right stock. If weather does not add that much
over a good weather-free method, paying attention to (or paying for) weather data is not
worth it for this decision.

## Metric
`mae`: mean absolute error, in units sold per day, over the scored days. Minimize.
`per_unit` = absolute error of each scored day.

## Evaluator
`eval/evaluate.py --split dev|holdout`, Python standard library only, runtime < 5 s.
Walk-forward: for each scored day (column `avaliar`=1), in date order, it calls
`src/model.py: predict(history, target)`.
- `history`: every day strictly before the target, with sales, holiday flag, day-ahead
  forecast (`prev_*`) and observed weather (`obs_*`).
- `target`: date, weekday, holiday flag and day-ahead forecast only. No sales and no
  observed weather of the target day.
The output must be a finite number between 0 and 10x the largest history sale, otherwise
the evaluator exits with an error. Before running, it parses `src/` and rejects file
access, dynamic imports/eval and any import outside a small standard-library allow-list
(math, statistics, collections, itertools, functools, datetime, random, bisect, heapq).

## Data
- Sales: `vendas.csv` from the owner (2024-01-01 to 2025-12-31, one row per day: date,
  weekday, holiday flag, units sold). Unchanged.
- Day-ahead weather forecast: Open-Meteo Previous Model Runs API
  (https://previous-runs-api.open-meteo.com/v1/forecast, variables
  `temperature_2m_previous_day1`, `precipitation_previous_day1`), point lat -23.566,
  lon -46.692 (Pinheiros; grid cell reported -23.585, -46.660), downloaded 2026-11-09.
  Hourly values predicted ~24 h ahead, aggregated per local day into `prev_tmax`,
  `prev_tmed` (°C), `prev_chuva` (mm, whole day), `prev_chuva_aberto` (mm, 10h-22h).
  The archive starts 2024-01-19; earlier days are left blank (they are history only,
  scoring starts 2024-03-01).
- Observed weather: Open-Meteo Historical Weather API (ERA5 reanalysis,
  https://archive-api.open-meteo.com/v1/archive), daily `obs_tmax`, `obs_tmed`, `obs_chuva`,
  same point, downloaded 2026-11-09. Given only for past days.
- Terms: Open-Meteo data is CC BY 4.0 (attribution "Weather data by Open-Meteo.com");
  the free API is for non-commercial use, so a production use in the shop would need a
  paid Open-Meteo plan or another source (e.g. INMET, whose API was unreachable today).
- Fetch script: `notes/fetch_weather.py` (re-runnable: `python3 -I notes/fetch_weather.py
  vendas.csv notes/staging`). Cleaning: hourly to daily aggregation only, no outlier edits.
- Split by time. `data/dev`: 2024-01-01 to 2025-06-30, scored 2024-03-01 to 2025-06-30
  (487 days). `data/holdout`: scored 2025-07-01 to 2025-12-31 (184 days); the file also
  holds all earlier days as unscored history. The holdout was written by the script and
  never opened.

## Baseline
`src/model.py`: what the owner does today, the average sales of the last 4 days with the
same weekday. Dev MAE 32.25 units/day.

## Budget
15 experiments, each < 1 minute, no paid compute. Holdout used at most 3 times by honestlab.

## What counts as a finding
A weather-using model whose MAE is at least 10% lower (relative) than the strongest
registered weather-free reference, on dev and confirmed on holdout, with honestlab's
paired bootstrap check (alpha 0.05). On dev the strongest reference is Holt-Winters
(27.22), so the bar there is about 24.5 units/day. lab.json: min_effect 0.10 relative,
compare_to strongest.

## Prior work
Searched the web (2026-11-09) for daily retail / ice-cream sales forecasting with weather
and standard benchmarks.
- Seasonal naive (same weekday last week) is the standard benchmark for daily retail
  (Hyndman & Athanasopoulos, Forecasting: Principles and Practice, 3rd ed.). Dev MAE 37.57.
- Holt-Winters / Winters' method gave the lowest errors among classic methods for
  ice-cream flavor sales (Forecasting Seasonal Products: A Case of Ice-Cream Sales,
  Emerald 2021, https://www.emeraldinsight.com/insight/content/doi/10.1108/S1477-407020210000014003/full/html).
  Implemented additive, weekly season, parameters grid-fitted on history. Dev MAE 27.22.
- Temperature-driven regression / gradient boosting for ice-cream sales
  (https://dspace.aiub.edu/jspui/handle/123456789/2663); practitioner guidance to put
  weather effects on top of a stable baseline forecast
  (https://www.scm.dk/best-practices-weather-based-sales-forecasting). No published
  numbers comparable to this shop.
- The owner's method (4-same-weekday average): dev MAE 32.25.

## Known ways to cheat this metric
1. Reading the sales file to look up the true value. Closed: the evaluator rejects
   `open`, file/os/pathlib/sys imports, dynamic import and eval in `src/`.
2. Using what happened on the target day (observed weather or sales). Closed: the
   target only carries the ~24 h-ahead forecast; history holds only earlier days.
3. Tuning to the dev period (many tries until one fits by chance). Partly closed: the
   final claim needs confirmation on the untouched later half-year (holdout) and the
   paired bootstrap; experiments are all logged.
Residual: `prev_*` values for late-evening hours come from model runs a few hours after
a typical 20h decision time; a small optimistic bias. Not closable with this source.
