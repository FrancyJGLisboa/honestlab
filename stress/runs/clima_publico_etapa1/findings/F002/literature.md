# F002: prior work

## How I searched
Web search on 2026-11-09: "daily retail sales forecasting weather temperature ice cream
seasonal naive exponential smoothing benchmark". Followed the top results. No academic
database (Scopus, Google Scholar) was queried directly.

## Closest existing work
- Forecasting Seasonal Products: A Case of Ice-Cream Sales (Emerald, 2021),
  https://www.emeraldinsight.com/insight/content/doi/10.1108/S1477-407020210000014003/full/html :
  Winters' method best among classic methods for ice-cream flavours; no weather inputs.
  Our weather-free reference is that method.
- Weathering the Forecast (AIUB), https://dspace.aiub.edu/jspui/handle/123456789/2663 :
  linear regression and XGBoost with temperature for ice-cream sales; uses temperature as
  a driver, as here, but not a day-ahead forecast nor a smoothing base.
- Best Practices in Weather-based Sales Forecasting (SCM),
  https://www.scm.dk/best-practices-weather-based-sales-forecasting : recommends adding
  weather effects on top of a stable baseline forecast, which is exactly this design.
- More generally, smoothing / ARIMA with external regressors ("ARIMAX", regression with
  ETS errors) is textbook (Hyndman & Athanasopoulos, FPP3, ch. 10).

## Assessment
Similar work exists: the method (baseline time-series model plus a weather regression on
its errors) is a standard, well-known technique. The finding is not a new method; it is a
measured answer for this shop: weather adds a real, confirmed improvement over the best
weather-free method. I could not check paywalled papers in full.
