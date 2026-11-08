# Journal

One to three lines per experiment: id, result, what was learned.
E0001 KEEP 8.159 -> 7.017 (15-yr window linear trend). Beats baseline but is worse than the full-history trend reference (6.650): longer history helps, so windowing hurts.
E0002 KEEP 7.017 -> 6.650: window=30 is just the registered `trend` reference re-implemented; not progress, a sanity check that evaluator and reference agree.
E0003 KEEP 6.650 -> 6.484 (trend + rain anomaly regression on trend residuals). First real gain over the `trend` reference (-0.166, still short of the 0.3 bar). GDD and quadratic terms did not help in scratch checks on dev.
E0004 KEEP 6.484 -> 6.397 (slope shrunk 20% toward prior 1.7). Caveat: 1.7 and 0.2 were picked by looking at dev, so this gain is partly tuned; holdout will tell.
E0005 DISCARD 6.268 (mean -0.129 vs E0004, CI [-0.057, 0.311]): unregularised quadratic rain term helps on average but is not significant; per-county fit of 2 coefficients on <=29 points is high-variance.
E0006 DISCARD (no-op, my error): only a constant was added because my edit assumed the E0005 file, but E0005 had been reverted to E0004; the score is identical to E0004 and says nothing about ridge. Redo as E0007.
E0007 KEEP 6.397 -> 6.153 (ridge, standardised rain + rain^2). Beats `trend` (6.650) by 0.497 on dev, above the 0.3 bar. Caveat: PRIOR_SLOPE 1.7, SHRINK 0.2 and RIDGE 1.0 were chosen with dev in view, so dev is optimistic; holdout confirmation is the real test.
F001 NOT CONFIRMED: E0007 vs `trend` on holdout: effect 0.237 bu/ac (3.4%), 98.3% CI [-0.056, 0.528], below the 0.3 bar and CI includes zero. Negative result. Dev effect (0.497) was inflated by hand-picked PRIOR_SLOPE, SHRINK, RIDGE and by choosing the rain terms with dev in view. 1 of 3 holdout runs used.
