"""The model being improved. Only this directory (src/) may change.

A character model guesses the next character of a text from the characters before it.
The evaluator calls two functions:

    train(ids, vocab, seconds, rng) -> state
        ids: numpy int array, the training text as character ids (0 = unknown).
        vocab: number of possible ids. seconds: the training budget; stop before it ends.
        rng: numpy random generator, seeded by the evaluator.
    predict(state, contexts) -> probabilities
        contexts: int array (rows, CONTEXT), the CONTEXT characters before each guess,
        padded on the left with 0. Return (rows, vocab) probabilities; each row sums to 1.

No file access and no other programs: use only what the evaluator hands over.

Baseline: a tiny neural network (Bengio et al. 2003 style): embed the last 3 characters,
one hidden layer of 64 units, softmax output, plain stochastic gradient descent.
"""
import time

import numpy as np

CONTEXT = 5
EMBED = 16
HIDDEN = 256
BATCH = 128
LR = 0.6


def _forward(params, ctx):
    emb, w1, b1, w2, b2 = params
    x = emb[ctx].reshape(len(ctx), -1)
    h = np.tanh(x @ w1 + b1)
    logits = h @ w2 + b2
    logits -= logits.max(axis=1, keepdims=True)
    p = np.exp(logits)
    p /= p.sum(axis=1, keepdims=True)
    return x, h, p


def train(ids, vocab, seconds, rng):
    start = time.time()
    total = seconds * 0.9
    deadline = start + total
    params = [rng.normal(0, 0.1, (vocab, EMBED)), rng.normal(0, 0.1, (CONTEXT * EMBED, HIDDEN)),
              np.zeros(HIDDEN), rng.normal(0, 0.1, (HIDDEN, vocab)), np.zeros(vocab)]
    padded = np.concatenate([np.zeros(CONTEXT, dtype=ids.dtype), ids])
    windows = np.lib.stride_tricks.sliding_window_view(padded, CONTEXT + 1)
    while (now := time.time()) < deadline:
        lr = LR * max(0.02, 1 - (now - start) / total)
        batch = windows[rng.integers(0, len(windows), BATCH)]
        ctx, y = batch[:, :CONTEXT], batch[:, CONTEXT]
        x, h, p = _forward(params, ctx)
        emb, w1, b1, w2, b2 = params
        d = p
        d[np.arange(BATCH), y] -= 1
        d /= BATCH
        gw2, gb2 = h.T @ d, d.sum(axis=0)
        dh = (d @ w2.T) * (1 - h * h)
        gw1, gb1 = x.T @ dh, dh.sum(axis=0)
        dx = (dh @ w1.T).reshape(BATCH, CONTEXT, EMBED)
        np.add.at(emb, ctx, -lr * dx)
        w1 -= lr * gw1
        b1 -= lr * gb1
        w2 -= lr * gw2
        b2 -= lr * gb2
    return params


def predict(state, contexts):
    return _forward(state, contexts)[2]
