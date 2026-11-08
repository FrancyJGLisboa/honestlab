# Review of F001 (independent, trying to refute)

## What I checked
I read the SPEC, the evaluator, the claim and the patch. I did not touch the held-out data. I tried to run an ablation on a scratch copy of dev, but a guard hook blocked the copy, so the ablation below is a recommendation and not a result.

## Cheating and leaks: none found
- The evaluator gives the model a deep copy of strictly earlier days. The target day arrives without its sales column.
- The patch only uses `history[-120:]` and `today`'s weekday, holiday, temperature and rain. It reads no files and has none of the forbidden strings.
- The prediction is checked to be finite and between 0 and 5000. It is not a constant, and the number varies by day.
- On the holdout split the dev days are history, which is legitimate because they are the past.

## Real weaknesses
1. **The comparison is not like for like, and the claim does not isolate weather.**
   - The candidate shifts its prediction to the 2/3 quantile of its residuals. That is the exact optimum for a loss where under-forecasting costs 2x.
   - Every reference (owner's mean, general mean, median, temp_linear) predicts a mean or median and gets no such adjustment.
   - Part of the gain, perhaps a large part, comes from tuning to the loss and not from weather. The SPEC question is about weather versus no weather. A fair test needs two extra rows: the same model with the quantile shift but no weather, and weather with no shift. Without them the claim "weather helps by 10%+" is not supported.
   - The claim wording does say "ajuste para faltar custar o dobro", so it is not hidden. But the "best reference" it beats is handicapped.
2. **The candidate adds holiday and rain on top of temp_linear.** These are extra inputs, so the gain over temp_linear is not attributable to one thing.
3. **Selection bias is small and mostly handled.**
   - Only 1 experiment was tried before this candidate.
   - The window of 120 days and the lambda of 1.0 were chosen by hand, possibly after looking at dev.
   - The holdout correction (alpha 0.05 / budget) is stated.
4. **The holdout is a single 183-day period (July to December).**
   - It is one regime, and the references swing a lot there. The median method goes from 41.8 to 63.0, and the baseline from 41.1 to 52.8.
   - temp_linear is stable at 27.5, so the candidate's holdout gain of 32% looks real. The holdout CI [5.4, 12.4] excludes zero.
   - Paired bootstrap over days ignores autocorrelation, so the CI is likely somewhat too narrow. The margin is large, so I do not think it flips the result.
5. **Weather is the weather that actually happened, not a forecast.**
   - The SPEC admits this. In real use the owner only has a forecast, which is noisier.
   - The real-world gain is therefore an upper bound. Any claim about "the owner will see 32% less error" is overreach.
6. **Metric weighting.** The score is in units and asymmetric. A reduction of 32% in this score is not a 32% reduction in typical absolute error, and it is not a measured reduction in lost sales or waste.

## What the numbers support
The candidate beats temp_linear by about 8.9 points (32%) on the holdout and about 11.7 (41%) on dev. Both clear the 10% bar by a wide margin. The evaluator seems sound, with no leak and no trick. The result is a real improvement in this evaluator's score. It is not evidence that weather is the cause, and it holds only under known weather.

## Conditions on any report
- State that the gain mixes quantile tuning, holiday, rain and temperature.
- State that weather is the observed value, not a forecast.
- Ideally add the two ablation rows (quantile shift without weather, and weather without shift) before saying weather is the reason.

I do not find grounds to refute the numerical claim as written, which is only that the model beats the best registered reference by at least 10% with the CI excluding zero. The causal reading about weather needs the caveats above.

Verdict: ACCEPT
