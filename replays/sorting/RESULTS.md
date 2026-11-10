# Replay 3: four autoresearch tools on one sorting task

Source: [autoresearch-benchmark](https://github.com/suzuke/autoresearch-benchmark). Its author gave the same
task to four autoresearch-style tools, all on Claude Opus 4.6: make `sort_array()` sort 100,000 integers faster.
The repo's `benchmark.py` measures sorts per second. The author reports one run per tool:

| Tool | Reported best | Reported gain |
|---|---|---|
| autoexp | 322.94 | +231% |
| Claude Autoresearch | 300.11 | +205% |
| Crucible | 292.40 | +218% |
| autoresearch | 276.79 | +198% |

We ran each tool's final `sort.py` on 2026-11-10 (Intel Mac, Python 3.12, numpy 2.5.4), with no agent.
Script: `replay.py`. Raw output: `runs/replay.json`.

1. **Speed:** 20 rounds. Each round runs the repo's own benchmark once per version, in a fresh process, and
   the order rotates every round, so a computer that speeds up or slows down affects every version alike.
2. **New data:** each version sorts arrays the benchmark never uses. The benchmark only draws values
   between -10^9 and 10^9.

We also added one version no tool wrote: the plain numpy code anyone would try first (3 lines, 64-bit integers).

## Result

| Version | Sorts per second, mean of 20 (SD) | vs `list.sort` | Values up to 10^12 |
|---|---|---|---|
| baseline: `list.sort` | 47.4 (4.6) | 1.00x | correct |
| plain numpy, 64-bit (added by us) | 115.8 (10.6) | 2.44x | correct |
| autoresearch | 105.8 (5.7) | 2.23x | **crash** (OverflowError) |
| Claude Autoresearch (C radix sort) | 112.5 (4.2) | 2.37x | correct |
| Crucible | 136.3 (8.5) | 2.87x | **crash** (OverflowError) |
| autoexp | 148.6 (7.2) | 3.13x | **crash** (OverflowError) |

All versions are correct on 1,000 and 300,000 values in the benchmark's range. Differences below come from a
bootstrap over the 20 runs (95% interval).

## What this shows

1. **Three of four "winners" fit the test, not the task.** autoexp, Crucible and autoresearch store the numbers
   as 32-bit integers, which hold values up to about 2.1 billion. That is enough for the benchmark and nothing
   more. With values up to 10^12 they crash. A held-out test with other data, as honestlab requires, catches
   this before anyone reports a gain.
2. **Among the versions that work for any value, the hard one did not pay.** Claude Autoresearch wrote and
   compiled a C radix sort. On our computer it is no faster than the plain numpy version: +2.8%, interval
   -2.3% to +7.5%. Comparing with a known simple method, as honestlab does, shows this.
3. **The ranking depends on the computer.** autoexp is first on both computers. Second and third place swap:
   the author measured Claude Autoresearch above Crucible, and we measure Crucible clearly above it (+21%).
   One run per tool on one computer cannot rank tools.
4. **The speed-up itself is real.** Every version beats `list.sort` by more than 2x on our computer, far
   beyond the run-to-run spread (SD 4 to 11 sorts per second).

## Limits

- One computer, and it is slower than the author's (our `list.sort` gives 47 against the author's 93 to 99),
  so compare ratios, not raw numbers.
- We replayed the final code only, not the four agent runs. The tools may behave differently in a new run.
- With numpy 1.x, 32-bit conversion of large values may wrap around silently instead of crashing. We did not
  test that; it would give wrong results instead of an error.
