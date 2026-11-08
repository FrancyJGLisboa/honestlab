# Journal

One to three lines per experiment: id, result, what was learned.

- E0001 KEEP 8.195 -> 6.632: linear trend on full county history (longer window beats 5/15 seasons).
- E0002 KEEP 6.329: pooled concave rain effect (coefficients fitted on targets up to 2014 only).
- E0003 DISCARD 6.258: fit trend on rain-adjusted history; better but not significant vs E0002.
- E0004 DISCARD 6.258: same plus concave GDD term; same size of gain, not significant.
- E0005 KEEP 6.184: weather-adjusted trend with county slope shrunk toward the pooled slope (1.75 bu/ac/yr). Reaches the bar on dev (6.93 -> 6.18, -10.8%). Next: confirm on the final data.
