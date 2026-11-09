# F001 adversarial review

Scope: read SPEC.md, eval/evaluate.py, findings/F001/claim.md, findings/F001/change.patch, src/model.py, and the dev split file. Did not open the sealed split, did not run the evaluator on it, did not run any honestlab command. Scratch scripts are in /tmp/review_f001 only.

## Checks made

1. Reproduced `python3 eval/evaluate.py --split dev`: mae 20.3426, n_days 336 (matches claim).
2. Leak review of `predict`: `_factors`, `level`, `rows`, and the feature fit use only `history`; `day` carries no `vendas`; no file reads, no mutable module state; output is range-checked by the evaluator. No leak found in code.
3. Weather off (same code, `prev_tmax` set to None, so base only): mae 28.2989. This equals the registered `suavizacao` reference exactly, so the candidate changes nothing in the base; the only difference is the weather term.
4. Alpha sweep of the weather-free base (dev only): alpha 0.05 28.82, 0.1 28.30, 0.2 27.45, 0.3 26.91, 0.5 26.55, 0.6 26.54 (best), 0.7 26.67, 1.0 27.53.
5. Candidate with weather on the best base (alpha 0.6): 24.01, i.e. only 9.5% below the best weather-free base.
6. Weather-free control using the same regression machinery with lagged sales (lag1 28.27, lag7 28.52): no gain. The gain is not a generic local-level or lag correction.
7. Placebo shifts of the weather features (dev only): same day 20.34, -1 day 26.41, +1 day 25.12, -7 days 27.81, +7 days 29.24. Same-day alignment is clearly best.
8. Feature ablation: prev_tmax alone 21.22; rain hours alone 26.54; both 20.34.
9. Calendar control (sin/cos day of year, same machinery): 29.15, worse than base. This control is weak evidence because it is a linear 2-term fit.
10. Bootstrap (5000 resamples of the 48 dev weeks) of the relative reduction vs the best weather-free base (alpha 0.6): 23.3%, 95% CI [14.6%, 30.7%].
11. Data scale: dev scored sales mean 185, sd 56, range 58–354. Correlation of prev_tmax with sales minus weekday mean is 0.79, which is unusually strong for real shop data.

## Findings

- The evaluator is clean. It deep-copies history, strips `vendas` from `day`, and enforces finite output in [0, 10000]. The candidate reads no files and keeps no state.
- The improvement comes from the weather term. The candidate's base is identical to the registered reference, and the lag-sales control gives no gain.
- The reference is not the strongest weather-free method. Exponential smoothing with alpha around 0.6 gives dev MAE 26.54, not 28.30. Against that stronger reference the candidate is still 23% better, so the 10% threshold is met on dev.
- The size of the gain depends on the base smoothing rate. Weather on alpha 0.1 cuts error 28%, but weather on alpha 0.6 cuts it only 9.5%. The weather term partly substitutes for a slow smoother that lags the level. The headline effect is therefore partly "weather fixes a lagging smoother", not "weather adds 10% to a good method".
- Alpha, WINDOW, FIT_DAYS, RIDGE and the feature set were all chosen on dev. The alpha sweep shows the dev optimum sits well away from the chosen 0.1, so the claimed effect depends on that choice.
- Same-day alignment is much better than +/-1 day. That is what a real day-ahead forecast would show, but it is also what observed weather of the same day would show. I could not check which it is: the fetch script (notes/fetch_weather.py) is outside the files I was allowed to read. The 0.79 correlation makes the provenance worth checking.
- I did not verify the sealed-split numbers in claim.md (19.6455 vs 26.9026). Those are self-reported and rest on the sealed split.

## Remaining caveats

- Provenance of `prev_*` values: confirm they are archived GFS forecasts issued about 24 h before, not observed weather. The SPEC says so; I could not confirm from the files I read.
- Timing: the GFS 00Z run is only available a few hours after it is issued, so the forecast the owner can use may be from a slightly different issue time than `previous_day1` implies. This is minor.
- Scope: the claim is about one shop, one year of dev data, and one later year used once, after 5+ dev experiments.
- Licensing: the Open-Meteo free API is non-commercial (see SPEC). This does not change the statistics but should be noted before any commercial use.

Verdict reasoning: no leak, evaluator trick or unfair base comparison invalidates the stated claim (weather term vs strongest registered weather-free reference, dev MAE 20.34 vs 28.30, or vs the stronger 26.54). The sensitivity to base smoothing and the unverified provenance are caveats on the size and mechanism of the effect, not failures of the stated rule on dev. The later-year result is not verified by me.

Verdict: ACCEPT
