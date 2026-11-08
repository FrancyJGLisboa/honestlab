# Journal

One to three lines per experiment: id, result, what was learned.
- E0001 KEEP mae 6.632 (baseline 8.195): linear trend over all history. Lesson: longer window beats short (noise dominates).
- E0002 DISCARD 6.553: slope shrunk 30% to typical slope; -1.2%, CI includes zero.
- E0003-E0005 DISCARD (6.66-6.69): winsorised trend, 85/15 blend with 5y mean, median level. Nothing beats plain trend.
- Dev exploration: residuals show no autocorrelation (AR terms hurt), so remaining error looks like noise; floor ~6.55-6.6 history-only.
