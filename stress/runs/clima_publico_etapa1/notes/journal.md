# Journal

One to three lines per experiment: id, result, what was learned.
- E0001 KEEP 27.22: base switched to registered Holt-Winters (stepping stone, not progress by itself).
- E0002 KEEP 21.18: HW + ridge regression of HW errors on day-ahead temp anomaly, rain 10-22h, holiday. -22% vs HW. Checked for leakage: target only has prev_* and holiday; regression fitted on earlier days only.
- Reviewer (F001) REJECT on attribution: gain could be intercept/holiday, not weather; rain 20-22h after decision time.
- E0003 DISCARD 26.39 (control: HW + intercept + holiday, no weather). Only -3% vs HW 27.22: the gain is not from bias/holiday.
- E0004 DISCARD 22.02 (control: HW + temperature anomaly + intercept + holiday, no rain). -19% vs HW on dev: temperature alone clears the 10% bar; rain adds ~4% more.
