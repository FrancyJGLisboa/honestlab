# Review of F001 (independent, attempt to refute)

Files read: SPEC.md, evaluate.py, claim.md, change.patch. I did not read the holdout data or run the evaluator.

## Evaluator tricks
- No trick found. The patch uses only numpy and the arguments it is given. It has no file access, no global or mutable state, and it does not touch `history`. The evaluator also passes a deep copy of the history and asserts that every history year is earlier than the target year.
- The forbidden-construct check is a regex on source text and could be evaded in principle. This patch does not try to. Its only literals are numeric constants.
- Output is always finite, and a trend plus a bounded quadratic stays in a plausible range.

## Leakage of target-year yields
- The code takes no target yield and reads no target-year file. Within the code, nothing leaks.
- The remaining risk is provenance of the hardcoded constants (RAIN/GDD means and SDs, B0..B_GDD2, SLOPE_PRIOR = 1.75, SLOPE_SHRINK = 200). The comment says they were "fitted on county-years up to 2014 only". Neither the patch nor the claim includes the fitting script or the ledger entry that shows it.
  - If that statement is true, the constants carry no information from dev targets (2015-2021) or from the final-test years (2022-2024).
  - I cannot verify it from the four files. Nothing in them contradicts it either. 1.75 bu/ac/yr is a round number, and a pooled slope from 1995-2014 would plausibly be about that size.
  - Because the constants are frozen and not refit per split, the same values are applied to dev and holdout.
  - A cheap check by the owner: refit SLOPE_PRIOR and the weather coefficients on data up to 2014 and confirm that the numbers match. Then refit them on the full panel and see whether the holdout score moves.
- The holdout gain (14.9%) is larger than the dev gain (10.75%). With constants fitted on early years this is plausible, because the weather deviations in 2022-2024 may simply be larger. It is also the pattern a leaked constant would produce, so this is the main reason to ask for the check above.

## Overfitting
- The author tried 5 experiments before this one, and the dev effect is selection-biased, as claim.md says. Dev clears 10% by only 0.75 points (10.75%).
- Many constants (7 weather coefficients plus the means/SDs, a prior and a shrinkage strength) were tuned on pre-2015 data. They are pooled across 80 counties, so the risk of overfitting a single county is low.
- The holdout was reportedly scored once, with a Bonferroni-style alpha of 0.05/3.

## Fairness of the comparison
- The candidate uses information the references do not have.
  - It uses pooled cross-county weather coefficients, which are effectively training on other counties' history up to 2014.
  - It uses a cross-county slope prior.
  - It uses the county's full history, while `trend_15` uses only the last 15 seasons.
- SPEC says "usando só o histórico do município e o clima da safra". The pooled constants stretch that wording. This is legitimate if the constants are recomputable from past data in production, and it should be stated.
- `trend_weather` is a per-county ridge, and it did not beat `trend_15`. So the gain comes from pooling and shrinkage, not from "weather helps" in general. The claim title should say that.
- Reference methods were not tuned with the same effort as the candidate (for example a shrunk-slope trend without weather was not tested). We cannot say how much of the gain is the weather term and how much is the slope shrinkage.

## Claim larger than the numbers
- The 10% is a point estimate. The CI lower bounds are about 6.6% (dev, 0.46/6.93) and 6.4% (holdout, 0.49/7.53). That shows a real improvement but does not show one of at least 10%.
- Bootstrap units are county-years. Weather and yield shocks are shared across counties within a year, so the units are strongly correlated. The effective sample is 7 dev years and 3 holdout years, so the CIs are too narrow, especially the holdout CI.
- The weather used is the actual season weather, not a forecast. The data has no forecast, and the evaluator says so. A desk that forecasts before the season ends would get a worse result, because the weather term is where much of the gain probably comes from. The claim should be restricted to "in-season or post-season nowcast with observed weather".

## Verdict reasoning
I found no cheating, no leak in the code, and no evaluator exploit. The open items are the unverifiable provenance of SLOPE_PRIOR and the other constants, and the overstated confidence. Neither is evidence of a defect. The finding holds if it is reported as: "about 15% on 2022-2024 holdout, with observed weather, probably 7-15% given correlated years, not yet shown to be at least 10% with confidence". It should not be reported as a forecast improvement usable before the weather is known.

Verdict: ACCEPT
