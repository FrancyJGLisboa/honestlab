"""Evaluator for the character model example (honestlab contract).

python eval/evaluate.py --split dev|holdout
Last stdout line: {"bpc": <float>, "per_unit": [...], ...}

What it measures: bits per character (bpc) on text the model never trained on. Lower is
better. 8 bits per character is a plain text file; a perfect guesser would need 0.

How, step by step:
1. Hand the training text (data/train) to train() in src/model.py, as integer ids.
2. Stop the clock. Training must finish within BUDGET_SEC, like Karpathy's autoresearch.
3. Cut the scored text (data/dev or data/holdout) into chunks of CHUNK characters.
4. Score every chunk from left to right: predict() sees only the characters before the one
   it guesses, inside the same chunk. All chunks advance one step per call.
5. The metric is the mean bpc over chunks. per_unit is the bpc of each chunk.
"""
import argparse
import importlib.util
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BUDGET_SEC = 60.0   # training time for every attempt, fixed before any result is seen
SLACK_SEC = 5.0     # tolerance for the last training step
CHUNK = 400         # characters per scored chunk
MAX_CONTEXT = 512


def load_model():
    spec = importlib.util.spec_from_file_location("model", ROOT / "src" / "model.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    split = ap.parse_args().split
    train_text = (ROOT / "data" / "train" / "text.txt").read_text(encoding="utf-8")
    test_text = (ROOT / "data" / split / "text.txt").read_text(encoding="utf-8")

    chars = sorted(set(train_text))
    index = {c: i + 1 for i, c in enumerate(chars)}  # id 0: padding and characters never seen in training
    vocab = len(chars) + 1
    train_ids = np.array([index[c] for c in train_text], dtype=np.int64)
    test_ids = np.array([index.get(c, 0) for c in test_text], dtype=np.int64)

    seed = int(os.environ.get("HONESTLAB_SEED", "0"))
    t0 = time.time()
    model = load_model()
    k = int(getattr(model, "CONTEXT", 0))
    if not 1 <= k <= MAX_CONTEXT:
        raise ValueError(f"CONTEXT must be an int from 1 to {MAX_CONTEXT}, got {k!r}")
    state = model.train(train_ids.copy(), vocab, BUDGET_SEC, np.random.default_rng(seed))
    train_sec = time.time() - t0
    if train_sec > BUDGET_SEC + SLACK_SEC:
        raise ValueError(f"training took {train_sec:.1f} s; the budget is {BUDGET_SEC:.0f} s")

    n = len(test_ids) // CHUNK
    chunks = test_ids[: n * CHUNK].reshape(n, CHUNK)
    padded = np.concatenate([np.zeros((n, k), dtype=np.int64), chunks], axis=1)
    bits = np.zeros((n, CHUNK))
    rows = np.arange(n)
    t1 = time.time()
    for t in range(CHUNK):
        ctx = padded[:, t:t + k].copy()  # only characters before position t of each chunk
        p = np.asarray(model.predict(state, ctx), dtype=np.float64)
        if p.shape != (n, vocab):
            raise ValueError(f"predict must return shape {(n, vocab)}, got {p.shape}")
        if not np.all(np.isfinite(p)) or p.min() < 0:
            raise ValueError("predict returned negative or non-finite probabilities")
        if np.max(np.abs(p.sum(axis=1) - 1.0)) > 1e-3:
            raise ValueError("every row returned by predict must sum to 1")
        bits[:, t] = -np.log2(np.maximum(p[rows, chunks[:, t]], 1e-12))
    per_unit = bits.mean(axis=1)
    print(json.dumps({"bpc": float(per_unit.mean()), "per_unit": [float(x) for x in per_unit],
                      "chunks": int(n), "train_seconds": round(train_sec, 1),
                      "score_seconds": round(time.time() - t1, 1), "seed": seed}))


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"evaluation failed: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)
