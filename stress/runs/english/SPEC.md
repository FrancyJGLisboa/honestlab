# SPEC: english

## Question
Can a forecast of tomorrow's support tickets that also uses the known release schedule (and other past information) have at least 10% lower average error than today's method, the average of the same weekday over the last 4 weeks?

## Why it matters
The support team plans staffing from this forecast. Release days average about twice the tickets of normal days (about 132 vs 66 in the development data), and today's method cannot see them coming. A 10% lower average miss is the improvement the person said would be worth it. Spike days matter too, so the 90th-percentile miss is reported as well.

## Metric
`score` = mean absolute error of the one-day-ahead forecast, in tickets per day. Lower is better. Also reported (not the success rule): `p90_abs_err`, the miss that 90% of days stay under.

## Evaluator
`eval/evaluate.py` runs walk-forward: for each scored day it calls `predict(history, target)` in `src/forecast.py`. `history` has only days strictly before the target (date, weekday, release_day, active_users, tickets). `target` has only date, weekday and release_day, which are known the day before. Output must be finite and not negative, or the run fails. Runs in about a second.

## Data
`tickets.csv`, 730 daily rows, 2024-01-01 to 2025-12-30, from the person. Development data: 2024-01-01 to 2025-06-30 (546 days, 518 scored after a 4-week warm-up). Kept for the final test: 2025-07-01 to 2025-12-30 (182 days), the latest period. In the final test, earlier days serve only as past history; only the later days are scored. Today's `active_users` is not given to the forecaster (the person was unsure it is known in advance); only past values are.

## Baseline
`src/forecast.py` is today's method: the mean of tickets on the same weekday over the last 4 weeks. Development score: 13.31 tickets/day, p90 27.

## Budget
15 experiments, each about a second, no money or special compute.

## What counts as a finding
At least 10% lower mean absolute error than the strongest known method (today's 4-week weekday average), on the development data and on the kept final period, with a paired bootstrap at 95% confidence on the daily errors. Set in lab.json as `min_effect` 0.10, relative.

## Prior work
Searched the web for support-ticket forecasting methods. Found only practitioner guides and a thesis, no controlled benchmark: seasonal baselines (same weekday/trailing average), SARIMA, and regression with predictors such as prior-week volume and known events; guides suggest release spikes of +15% to +50%, and aiming for MAPE under 10%. These are rough, not rigorous. The only method the person has is today's 4-week weekday average, registered as a reference.

## Known ways to cheat this metric
1. Using the target day's tickets or active users: closed, since the forecaster only gets history before the day and the target's date, weekday and release flag.
2. Reading the data files directly inside `src/` (including the kept period): the guard hook forbids reading the kept data, and the final check on it is run only a few times.
3. Tuning to quirks of the development period: closed by the final test on a later period, and by the 10% margin plus the bootstrap.
4. Strange outputs (NaN, negative): the evaluator rejects them.
