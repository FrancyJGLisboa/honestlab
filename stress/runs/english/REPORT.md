# honestlab report: english

## Verdict

**Found: a real improvement over the best known method, confirmed on new data and by an independent review.**

**Confidence:** High: it held on new data with a statistical margin and passed the independent review.

**Approval:** by you in the chat (confirmed by your own message).

## In plain words

You asked whether tomorrow's tickets can be forecast with at least 10% less average error than your 4-week same-weekday average. Yes: a method that uses the known release schedule and scales by active users missed by 9.96 tickets a day on the development data, against 13.31 for yours (about 25% less). On the kept last six months it was about 42% better, and an independent review found no tricks or leaks. The 42% is probably inflated, because your average lags behind the growing user base, so I would plan on about 25%. Next step: try it alongside your current forecast for a few weeks and have someone from your team check it.

## The numbers

- Measure: `score` (lower is better)
- Starting point (what already existed): 13.31
- Best known method registered: baseline = 13.31
- Agent's best result: 9.961 (E0004) (+25.2% vs baseline)
- Agreed margin to count as a finding: 10%
- On new data (locked until the end) (F001, E0004 vs baseline): +42.2%, CI [5.026, 11.91]

## What was tried

5 attempt(s): 3 kept (improved), 2 undone, 0 errors. All of them are recorded.

**Best ideas:**
- E0005 (9.777, discard): Pool days of the same kind (Mon-Thu, Fri, weekend) to get a steadier rate; release lift from same-kind release days
- E0004 (9.961, keep): Add per-user scaling on top of the 10-day smoothing
- E0003 (10.27, keep): Per-user rate smoothed over the last 10 same-weekday non-release days (less noise than 4), with user scaling

**Ideas that did not work (examples):**
- E0005 (9.777 vs 9.961): Pool days of the same kind (Mon-Thu, Fri, weekend) to get a steadier rate; release lift from same-kind release days
- E0002 (10.67 vs 10.74): Forecast tickets per active user, scaled by the latest known users, so growth in users is followed

## Finding candidates

- F001: verified: Forecasting tickets per active user, pooled over recent same-weekday non-release days, with a release-day lift, cuts average daily error by at least 10% versus the 4-week same-weekday average

## Next step

Ask someone from the field to check the method, and test it on the next period of data before using it for important decisions.

## How this compares with what AI labs do

| What honestlab did | Equivalent in the labs |
|---|---|
| A question with a measure the computer computes by itself | The automatic "evaluator" in FunSearch and AlphaEvolve (DeepMind) |
| Known methods registered before starting | Comparing with the best published result, not with a weak starting point |
| The agent changes one thing at a time and honestlab measures it | The generate, evaluate, keep-the-best loop, over thousands of attempts |
| Worse changes are undone but recorded | The scored program database, failures included |
| Locked data, used only at the end | Separating development from testing so luck or evaluator tricks do not fool you |
| Review by someone who did not do the work | Independent verification: experts, formal provers such as Lean |

---
Record: 10 entries, hash chain intact.
