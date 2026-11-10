# Replay 1: MLP_AutoResearch on MNIST

Source: [MLP_AutoResearch](https://github.com/HuangShengZeBlueSky/MLP_AutoResearch). An autoresearch agent
changed a small neural network for MNIST digits and kept 3 versions. The author reports test accuracy
0.9809 -> 0.9832 -> 0.9836 (one training run each).

We trained each kept version 5 times with seeds 0-4, with the code from the author's commits unchanged.
Measured on 2026-11-09 on an Intel Mac CPU (Python 3.12, torch 2.2.2). Raw numbers: `results.json`.

## Result

| Version | What the agent changed | Reported (1 run) | Our mean of 5 runs | Spread (SD) |
|---|---|---|---|---|
| b3d24d4 | hidden 256, GELU, AdamW | 0.9809 | 0.9808 | 0.0013 |
| 5769834 | + weight decay 1e-4, + "cosine" learning rate | 0.9832 | 0.9817 | 0.0021 |
| 8baab10 | + hidden 512 | 0.9836 | 0.9815 | 0.0011 |
| 8baab10, one line fixed | remove the second softmax (see below) | not tried | **0.9839** | 0.0015 |

Comparisons, with the honestlab bootstrap over the 5 runs (90% interval of the difference, in accuracy points):

| Step | Difference | 90% interval | Clear gain? |
|---|---|---|---|
| b3d24d4 -> 5769834 | +0.09 | -0.07 to +0.24 | no |
| 5769834 -> 8baab10 | -0.02 | -0.18 to +0.13 | no |
| b3d24d4 -> 8baab10 (all agent steps) | +0.07 | -0.04 to +0.18 | no |
| 8baab10 -> one line fixed | +0.25 | +0.12 to +0.37 | yes |

## What this shows

1. **The reported gain is within run-to-run noise.** The reported +0.27 points shrink to +0.07 over 5 runs,
   and the interval includes 0. One run of the same code moves by up to 0.5 points (0.9791 to 0.9840).
2. **The "cosine" learning rate does nothing.** The code wraps a second optimizer that training never uses.
   With the cosine part turned off, all 20 epochs give the same numbers to 4 decimals (seeds 0 and 1).
3. **A known bug beats all agent steps.** The model applies softmax and then `CrossEntropyLoss`, which applies
   it again. Removing the first softmax gives +0.25 points over the agent's best, and the interval excludes 0.
   This fix is standard knowledge, which is what honestlab's "known method" comparison is for.
4. **The test set picked the winner.** The agent kept changes by test accuracy, so 0.9836 is a best-of-many
   reading. Our 5 runs of that version never reach it (highest 0.9832).

## Limits

- Per-image results were lost to a path bug in the first run, so the comparison is over 5 runs only, not
  the two-level bootstrap over runs and images. The script is fixed for later runs.
- 5 runs per version. A difference below about 0.1 points needs more runs to settle.
- Our machine and torch version differ from the author's. The baseline matches (0.9808 vs 0.9809).
- We did not rerun this case inside honestlab end to end. This is a check of the published result.

## Run it again

```
git clone https://github.com/HuangShengZeBlueSky/MLP_AutoResearch replays/mnist/MLP_AutoResearch
python3 -m venv replays/mnist/.venv && replays/mnist/.venv/bin/pip install torch==2.2.2 torchvision==0.17.2 "numpy<2"
replays/mnist/replay_all.sh   # 27 trainings, about 1.5 hours on a laptop CPU
```
