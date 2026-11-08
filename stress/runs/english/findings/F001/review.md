# F001: independent review

<!-- Written by a reviewer that did NOT run the experiments (a subagent or a fresh
     session). Inputs: SPEC.md, eval/, claim.md, change.patch. Goal: refute. -->

## Evaluator exploits
None found. `predict` gets `tuple(rows[:i])` (strictly earlier days) and `(date, weekday, release_day)` of the target. NaN or negative outputs exit the run. Dev and holdout use the same loop. The patch reads `history[-1][3]`, which is yesterday's active_users and legitimately known. It never touches the target's tickets or users. It reads no files and has no globals or state across calls. I did not read or run the holdout.

## Leakage or overfitting
No leakage. The release flag is a permitted input. The model has few free choices (10-day window, 12 past releases, lift as a mean ratio), chosen after 5 experiments, so dev is mildly optimistic, as claim.md says. I re-ran the patch on dev only, by halves: baseline 12.17 / 14.45 against candidate 9.10 / 10.82 (25% in both halves). So the gain is not from one stretch of dev. Without any user scaling (a crude fixed x1.9 release multiplier) dev MAE is 10.23, so the result does not depend on the users feature or on tuned constants. Release days: baseline 54.5 against candidate 15.5 (n=24). Non-release days: 11.31 against 9.69 (14%).

## Fairness of the comparison
The baseline is the registered 'today' method and runs through the same evaluator. In the holdout, dev rows serve as history for both methods, which is normal walk-forward and what a real forecaster would have. Why the holdout gain (42%) exceeds dev (25%): active_users roughly doubles over dev (5.0k to 11.2k; tickets about 42 to 80 per day), and the trend continues. A 4-week same-weekday mean lags a growing level and treats release spikes as normal days, so the baseline degrades (13.3 dev, 19.6 holdout) while a per-user rate tracks growth. This is a real baseline weakness and not an evaluator trick, though it also means the candidate's advantage depends on the growth trend and release share continuing. It is a regime-dependent gain, not a stable 42%. In dev the baseline also worsens from 12.2 to 14.5 between halves, which matches this.

## Does the claim say more than the numbers?
The claim as worded (at least 10% lower error) is supported: dev 25.2% with CI [2.4, 4.3] and holdout 42.2% with a 98.3% CI [5.0, 11.9] that excludes zero. Cautions: (1) the 42% should not be quoted as the expected improvement. 25% on dev is the better guide, and the holdout is one 6-month period. (2) Release-day evidence is thin: 24 dev releases, so the lift estimate and release-day error are noisy, and the holdout probably has few release days as well. (3) The spec says 546 days / 518 scored while dev has 547 / 519, a trivial documentation slip. (4) Only the 10% point-estimate rule is registered; the CI excluding zero does not itself show that the effect is at least 10%. The lower holdout CI bound is 5.0 tickets, about 26% of baseline, so it clears 10% anyway. (5) It relies on yesterday's active_users, which is known in history, so fine.

## Strongest objection
The holdout number is inflated by user growth and a lagging baseline. A stronger honest baseline (a trend-adjusted or user-scaled weekday average) would shrink the gap. Without the release flag the candidate would likely still beat the 4-week mean on growth alone, so some of the gain comes from the user-scaling and not only from the release schedule that the SPEC question is about. The spec's registered reference is the 4-week average, though, so the claim is valid against it, and the no-users variant above still beats it by 23% on dev. This limits how the result is described, not whether it holds.

Verdict: ACCEPT
