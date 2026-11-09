# F001: prior work

## How I searched
One web search on 2026-11-09 ("ice cream daily sales forecasting temperature weather
regression versus seasonal naive"), plus general knowledge of standard forecasting texts
(Hyndman & Athanasopoulos, *Forecasting: Principles and Practice*: exponential smoothing,
regression with external predictors / dynamic regression). No academic databases searched.

## Closest existing work
- AIUB conference paper "Weathering the Forecast" (linear regression vs XGBoost on
  temperature-driven ice cream sales): https://dspace.aiub.edu/jspui/handle/123456789/2663
  It uses temperature as a predictor, as here. It does not compare against a seasonal or
  exponential-smoothing baseline, and it does not use day-ahead forecasts.
- University of Reading climate intelligence course (FutureLearn): regression of daily
  sales on temperature for impact modelling, not day-ahead forecasting:
  https://futurelearn.com/info/courses/climate-intelligence-using-climate-data-to-improve-business-decision-making/0/steps/300833
- Weather-adjusted demand forecasting (smoothing or regression baseline plus temperature
  and precipitation regressors) is standard practice in retail and food demand forecasting.

## Assessment
Similar work exists. The method (smoothing baseline × multiplicative weather adjustment
from a regression) is a well-known technique, not a new method. What is new here is only
the evidence for this shop: day-ahead forecast weather beats the strongest weather-free
method by ~27% on a sealed later year. I could not check for studies on São Paulo ice cream
shops or other uses of the Open-Meteo previous-runs data for demand forecasting.
