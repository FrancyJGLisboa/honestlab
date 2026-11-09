# F002 review (adversarial)

Scope: SPEC.md, eval/evaluate.py, findings/F002/claim.md, findings/F002/change.patch, data/dev/dev.csv. Holdout not opened. Dev checks: `python3 eval/evaluate.py --split dev` and a replica of the evaluator run on variants reconstructed from change.patch (scratch files in /tmp/f002review, outside the project).

## Findings

1. **HIGH: the claimed candidate is not the code the repo keeps.** claim.md says the candidate is E0004 (dev 22.0242). The ledger commit for E0004 reads "discard ... Control (ablation): drop the rain input". The current tree evaluates to 21.1782 on dev, which matches the rain-included model in change.patch (replica: 21.1782) and the E0002 "keep" commit. The temperature-only model (replica: 22.0242) reproduces the claim's dev number but is the discarded control. The holdout figures (23.5007) cannot be tied to a kept artifact in this repo. Severity high because the claim names a model that is not the one that would be shipped.

2. **MEDIUM: the 5.2-unit "effect" is not attributed to temperature.** The reference is plain Holt-Winters (27.22). Replica results on dev:
   - HW + intercept + holiday, no weather: 26.39 (matches ledger E0003 discard).
   - HW + intercept + temperature anomaly + holiday (claimed): 22.02.
   - Same without the holiday flag: 22.73.
   - Committed rain-included version: 21.18.
   So 0.83 of the 5.20 gain comes from the non-weather correction machinery, not weather. Temperature alone adds 4.37 units, 16.6% vs the no-weather control. That still clears 10% on dev, but the claimed 19.10% overstates the weather effect. The holiday term (0.7 units) is non-weather and is not discussed.

3. **MEDIUM: holdout evidence is not clearly one-shot or traceable.** claim.md says 4 experiments preceded this candidate and reports holdout confirmation, but the commit history shows an earlier holdout-confirmed candidate (F001) that was later rejected. The number of holdout uses is not stated in claim.md. Given finding 1, I cannot verify which code the holdout result belongs to. I did not open holdout data as instructed.

4. **LOW: residual forecast-timing bias.** The temperature feature uses the daily max of the day-ahead forecast, which is typically an afternoon value and is available before a ~20h decision, so it is mostly fair. The rain-included version used by the kept code uses prev_chuva_aberto (10h-22h), which includes hours after the decision time. SPEC.md already flags this as a small optimistic bias; it is not closed for the rain version.

5. **Checked, no leak found.** The model uses only `history` and the target's prev_* fields. It does not use obs_* or any target sales. The Holt-Winters grid and regression are fit on history up to the current day. The module-level cache is keyed only by n // 28, which is safe for the single-series evaluator but would be wrong if reused across series. The evaluator's AST checks and walk-forward loop show no trick that inflates the score. The Holt-Winters reference is fit with the same grid and the same method, so the comparison is fair.

6. **Dev overfitting.** Dev has 487 scored days and the effect is well outside noise on dev (CI [3.68, 6.64]). Selection across 4 or more variants adds optimistic bias that the claim acknowledges but does not quantify.

## Conclusion (initial)

On dev, a temperature-anomaly correction on top of Holt-Winters does reduce MAE by about 17% over a no-weather correction control and about 19% over plain Holt-Winters. That part reproduces. The initial rejection rested on the candidate identity and attribution issues, addressed below.

## Addendum (after coordinator clarifications, 2026-11-09)

Checked against `experiments/E0004.patch`, `notes/journal.md`, `honestlab status` and `honestlab history -n 15` (read-only).

- Finding 1 resolved. change.patch stacks E0002 (rain) then E0004 (drop rain). `finding new --candidate E0004` checked out the E0004 code for the dev check and the holdout run, so 22.0242 and 23.5007 belong to the same temperature-only code. The 21.18 I measured is the working tree (E0002), as the coordinator said. The E0004 "discard" is because it is a control, not because it is worse. The finding is about the temperature-only model, which is not what src currently holds, so adopting it needs a code change through the normal loop.
- Finding 2 weighed. The pre-registered rule compares against plain Holt-Winters (>= 10% on dev and holdout). Dev: 22.02 vs 27.22 = 19.1%, CI [3.68, 6.64] excludes zero. Holdout: 23.50 vs 29.75 = 21.0%, 98.3% CI [3.04, 9.43] excludes zero. The intercept+holiday control (E0003, 26.39) is dev-only and shows temperature adds about 16.6% beyond it on dev; that is a fair extra attribution and should be reported as the honest weather-only share, but it does not change the pre-registered pass.
- Finding 3 resolved. Holdout is 2 of 3 runs (F001, F002), Bonferroni alpha 0.0167 is applied. The holdout result is attributable to the temperature-only code.
- Finding 4 mostly resolved. The temperature-only model drops the 20-22h rain input, so the timing bias the review flagged for the rain version does not apply to F002. The daily-max forecast is typically available before a ~20h decision.
- Findings 5 and 6 stand (no leak; selection over ~4 variants is a bounded optimistic bias that the holdout effect (21%, far above the 10% bar) makes unlikely to explain the result).

Remaining caveats for the report: state the gain as about 19-21% over Holt-Winters, of which about 17% is attributable to temperature beyond the intercept/holiday correction (dev only); the holiday flag is part of the model; the owner must not treat F002 as the shipped code until src is changed.

Verdict: ACCEPT
