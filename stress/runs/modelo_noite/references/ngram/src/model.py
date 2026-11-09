"""Reference: an interpolated character n-gram model with Witten-Bell smoothing.

Witten and Bell (1991) smoothing, interpolated across orders 0 to ORDER - 1 (Chen and
Goodman 1998 compare it with other smoothing methods). It counts which character followed
each context in the training text. No neural network and no training loop: counting the
text takes a few seconds, so the time budget does not limit it.
"""
import numpy as np

ORDER = 6          # contexts of up to 5 characters
CONTEXT = ORDER - 1


def train(ids, vocab, seconds, rng):
    tables = [dict() for _ in range(ORDER)]
    seq = [int(x) for x in ids]
    for k in range(ORDER):
        table = tables[k]
        for i in range(k, len(seq)):
            key = tuple(seq[i - k:i])
            nxt = table.get(key)
            if nxt is None:
                nxt = table[key] = {}
            nxt[seq[i]] = nxt.get(seq[i], 0) + 1
    packed = []
    for table in tables:
        out = {}
        for key, nxt in table.items():
            chars = np.fromiter(nxt.keys(), dtype=np.int64)
            counts = np.fromiter(nxt.values(), dtype=np.float64)
            out[key] = (chars, counts, counts.sum(), len(chars))
        packed.append(out)
    return vocab, packed


def predict(state, contexts):
    vocab, packed = state
    probs = np.empty((len(contexts), vocab))
    for r, row in enumerate(contexts.tolist()):
        p = np.full(vocab, 1.0 / vocab)
        for k in range(ORDER):
            key = tuple(row[len(row) - k:]) if k else ()
            if k and 0 in key:
                break
            hit = packed[k].get(key)
            if hit is None:
                break
            chars, counts, total, types = hit
            lam = total / (total + types)
            p *= 1 - lam
            p[chars] += lam * counts / total
        probs[r] = p
    return probs
