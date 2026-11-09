# F001 review (adversarial, revision 2)

Scope read: SPEC.md, eval/evaluate.py, findings/F001/claim.md, findings/F001/change.patch, data/dev/dev.csv (header only), experiments/E0003.patch, experiments/E0004.patch, notes/journal.md. Holdout not opened. No honestlab commands run. src not edited.

## Checks performed
- `python3 eval/evaluate.py --split dev` reproduces mae 21.1782 over n=487, matching claim.md.
- Code read of change.patch: target-day inputs are only `prev_tmax`, `prev_chuva_aberto`, `feriado` (day-ahead forecast and holiday flag). `obs_*` is never read. Training rows use `history[i]` with `rows[i-28:i]` (past only). Grid parameters are chosen on `y[:n]` at the first call of each 28-day block, so they are past-only. No leak found in the code path.
- E0003 and E0004 patches only change the `_features` return value (drop weather terms). They read nothing new, so they add no leak.
- Only `math`/`itertools` are used. No file, dunder, or dynamic access. The patch passes the static checks.
- An in-memory ablation I attempted in the first pass was blocked by a guard hook. I did not work around it. The ablation numbers below come from the lead's logged dev runs, not from my own re-run.

## Findings (from revision 1, with status)

1. **High - attribution to weather. Partly resolved by the controls.** The original concern was that the gain came from the intercept/holiday correction rather than weather. The controls answer this: intercept + holiday alone gives only 3% over Holt-Winters (see section below). The remaining gain is due to the temperature term, so the weather attribution holds for temperature. It does not hold for rain (see finding 2 and the ablation section).

2. **Medium - residual leak in the rain feature (SPEC acknowledges, not closed). Now moot for the claim, if rain is dropped.** `prev_chuva_aberto` covers 10h-22h. The decision is at about 20h, so 20h-22h is after the decision. Rain adds only 0.84 units of dev MAE, so the claim does not need it. Dropping rain removes this exposure.

3. **Medium - the day-ahead source is a proxy, not what the owner sees at 20h.** The archived model-run values may not match a forecast product the owner could read the night before, and availability by 20h is not verified. The source is a reasonable proxy for "tomorrow's forecast is known tonight", but the claim should say so. This applies to temperature as well.

4. **Medium - overfitting and selection (worse than stated).** The ledger now has four dev-scored experiments (E0001-E0004) plus the candidate, and the controls were chosen after the reviewer's first rejection. The holdout budget has been used for the full model. Any holdout run on a narrowed variant uses budget. I could not verify holdout figures (not permitted to open the data).

5. **Low - evaluator hardening gap (does not affect this patch).** `__builtins__` is not in FORBIDDEN_NAMES and the dunder check only covers attributes, so `__builtins__['open']` would pass the static check. Neither change.patch nor the controls use it.

6. **Low - claim scope.** The Open-Meteo free API is non-commercial (SPEC says production use needs a paid plan or another source). The holdout is a single half-year. There is no decision-value check beyond the registered metric.

7. **Low - fairness of the reference.** Whether the registered holt_winters uses the same grid and refit schedule as the candidate's base could not be checked from the allowed files.

## Ablations (dev, n=487, MAE in units/day, from experiments/ and notes/journal.md)

| model | dev MAE | vs Holt-Winters | increment |
|---|---|---|---|
| plain Holt-Winters (reference) | 27.22 | - | - |
| E0003: HW + intercept + holiday (no weather) | 26.39 | -3.0% | +0.83 units gain |
| E0004: E0003 + temperature anomaly (no rain) | 22.02 | -19.1% | temperature adds 4.37 units |
| E0002: E0004 + rain 10-22h (candidate) | 21.18 | -22.2% | rain adds 0.84 units |

Attribution of the 6.04-unit dev gain: about 14% intercept/holiday, about 72% temperature, about 14% rain.

Reading:
- The 10% bar is cleared by the temperature-only model (-19.1% vs Holt-Winters on dev), not by the intercept/holiday control (-3.0%).
- Rain adds 3.8% beyond temperature. That increment is small, has no holdout check, and is the only part exposed to the 20h timing issue.
- The controls are dev-only and have no paired bootstrap CI computed. The 4.37-unit temperature gain is large relative to the MAE scale, but this is not verified here.
- E0004 was run after the full model's holdout confirmation, so its holdout status is unknown. It is a subset of the confirmed model, but it is not itself confirmed.

## What the evidence supports
- Supported on dev: a day-ahead temperature-forecast correction on top of Holt-Winters reduces MAE by about 19% (27.22 to 22.02), and it is not explained by intercept or holiday terms.
- Not supported: the claim as written ("temperature anomaly and rain in opening hours"). The rain term is a small increment with the timing problem, and the holdout confirmation was for the model that includes rain, not the temperature-only variant.
- Narrowed claim to register: "day-ahead temperature forecast (no rain) as a linear correction to Holt-Winters reduces next-day sales MAE by at least 10% vs Holt-Winters." It needs (a) a paired bootstrap CI on dev for E0004 vs Holt-Winters, and (b) a holdout confirmation of E0004, under the pre-registered rule, before it can be accepted.

## Conclusion
No evaluator trick and no direct target-day leak was found. The controls remove the main attribution objection for temperature. The claim as written still includes rain and was confirmed on holdout only in that form, so it is not accepted as worded. The narrowed temperature-only claim is well supported on dev and should be re-submitted with the holdout check above before acceptance.

Verdict: REJECT
