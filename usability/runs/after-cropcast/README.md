# cropcast

County-level crop yield forecasting toolkit used by the commodities desk.

- `cropcast/io.py`: load the county panel (`data/yields.csv`).
- `cropcast/forecast.py`: `predict_yield(history, weather)`, the production forecast.
- `cropcast/clean.py`: outlier screening for reported yields.
- `cropcast/report.py`: markdown summary tables for the weekly note.
- `scripts/backtest.py`: rolling-origin backtest (2015 to 2024); prints MAE in bu/ac.

Run `python -m pytest` and `python scripts/backtest.py`.
