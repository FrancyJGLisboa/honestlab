"""Uncertainty for keep/discard and finding decisions (stdlib only, deterministic).

A *sample* is what one evaluation produced:
    {"score": float, "units": [float, ...] | None, "repeats": [float, ...]}
`units` are per-instance scores whose mean is the metric (paired across
solutions, because every solution is scored on the same instances).
`repeats` are whole-evaluation scores from repeated runs (for noisy evaluators).
`item_runs` (lab.json "aggregate": "custom") holds, for every run, the items the lab's own measure
function (eval/measure.py or similar, protected) turns into the score: F1, median, RMSE, rank correlation.
`auc_runs` (lab.json "aggregate": "auc") replaces `units`: for every run, the [label, prediction]
pair of each item. AUC compares pairs of items, so it has no per-item score; the comparison
resamples items and recomputes AUC on both sides.
`unit_runs` (optional) keeps the per-instance scores of every repeated run. With two or more
runs on both sides, the comparison resamples runs as well as instances, so the run-to-run
noise of training or sampling is part of the uncertainty.
"""

from __future__ import annotations

import random

SEED = 20260611  # fixed, so every decision is reproducible


def _resamples(n: int, budget: int) -> int:
    # keep cost bounded (about 4M draws) while never going below 300 resamples
    return max(300, min(budget, int(4_000_000 / max(n, 1))))


def _percentiles(vals, alpha):
    vals = sorted(vals)
    b = len(vals)
    lo = vals[max(0, int((alpha / 2) * b))]
    hi = vals[min(b - 1, int((1 - alpha / 2) * b) - 1)]
    return lo, hi


def _idx(rng, n, block=1):
    """Item indices for one bootstrap draw. block > 1 draws runs of `block` neighbours (a moving-block
    bootstrap), for items in time order whose values depend on their neighbours."""
    if block <= 1:
        return rng.choices(range(n), k=n)
    block = min(block, n)
    out = []
    while len(out) < n:
        s = rng.randrange(n - block + 1)
        out.extend(range(s, s + block))
    return out[:n]


def mean_ci(d, alpha, budget=2000, block=1):
    """Bootstrap percentile CI for the mean of d."""
    n = len(d)
    m = sum(d) / n
    if n < 2:
        return m, None, None
    rng = random.Random(SEED)
    b = _resamples(n, budget)
    if block <= 1:
        means = [sum(rng.choices(d, k=n)) / n for _ in range(b)]
    else:
        means = [sum(d[i] for i in _idx(rng, n, block)) / n for _ in range(b)]
    lo, hi = _percentiles(means, alpha)
    return m, lo, hi


def diff_ci(a, c, alpha, budget=2000):
    """Bootstrap CI for mean(a) - mean(c), independent samples."""
    m = sum(a) / len(a) - sum(c) / len(c)
    rng = random.Random(SEED)
    b = _resamples(len(a) + len(c), budget)
    diffs = []
    for _ in range(b):
        ra = rng.choices(a, k=len(a))
        rc = rng.choices(c, k=len(c))
        diffs.append(sum(ra) / len(ra) - sum(rc) / len(rc))
    lo, hi = _percentiles(diffs, alpha)
    return m, lo, hi


def two_level_ci(ref_runs, cand_runs, sign, alpha, budget=2000, block=1):
    """Bootstrap CI for the mean improvement, resampling runs (each side) and instances (paired).

    ref_runs, cand_runs: lists of runs, each a list of per-instance scores of equal length.
    """
    n = len(ref_runs[0])
    rng = random.Random(SEED)
    b = _resamples(n * (len(ref_runs) + len(cand_runs)), budget)
    point = sign * (sum(map(sum, ref_runs)) / (n * len(ref_runs)) - sum(map(sum, cand_runs)) / (n * len(cand_runs)))
    diffs = []
    for _ in range(b):
        rr = rng.choices(ref_runs, k=len(ref_runs))
        cr = rng.choices(cand_runs, k=len(cand_runs))
        idx = _idx(rng, n, block)
        tot = 0.0
        for i in idx:
            tot += sum(r[i] for r in rr) / len(rr) - sum(c[i] for c in cr) / len(cr)
        diffs.append(sign * tot / n)
    lo, hi = _percentiles(diffs, alpha)
    return point, lo, hi


def auc(pairs, idx=None):
    """Area under the ROC curve from [label, prediction] pairs (label 1 = positive), ties counted as half.

    idx (optional) picks the items, with repeats, for a bootstrap draw. Returns None without both classes.
    """
    rows = pairs if idx is None else [pairs[i] for i in idx]
    rows = sorted(rows, key=lambda r: r[1])
    n1 = sum(1 for r in rows if r[0] == 1)
    n0 = len(rows) - n1
    if not n1 or not n0:
        return None
    rank_sum, i = 0.0, 0
    while i < len(rows):  # average ranks over tied predictions
        j = i
        while j + 1 < len(rows) and rows[j + 1][1] == rows[i][1]:
            j += 1
        avg = (i + j) / 2 + 1
        rank_sum += avg * sum(1 for r in rows[i:j + 1] if r[0] == 1)
        i = j + 1
    return (rank_sum - n1 * (n1 + 1) / 2) / (n1 * n0)


def _safe(measure, items):
    try:
        v = measure(items)
    except Exception:  # noqa: BLE001  (a draw the measure cannot score, for example one class only)
        return None
    return float(v) if isinstance(v, (int, float)) and not isinstance(v, bool) and v == v and abs(v) != float("inf") \
        else None


def auc_ci(ref_runs, cand_runs, sign, alpha, budget=2000, measure=None, block=1):
    """Bootstrap CI for the improvement in a measure computed from items (AUC by default).

    Resamples items (paired) and, with 2+ runs per side, runs. ref_runs, cand_runs: lists of runs, each a
    list of items on the same items in the same order. A draw the measure cannot score is skipped.
    """
    measure = measure or auc
    n = len(ref_runs[0])
    mean = lambda v: sum(v) / len(v)
    full_r, full_c = [_safe(measure, r) for r in ref_runs], [_safe(measure, c) for c in cand_runs]
    if None in full_r or None in full_c:
        return None, None, None
    point = sign * (mean(full_r) - mean(full_c))
    rng = random.Random(SEED)
    b = _resamples(n * (len(ref_runs) + len(cand_runs)) * 4, budget)  # each draw sorts every run
    diffs = []
    for _ in range(b):
        rr = rng.choices(ref_runs, k=len(ref_runs)) if len(ref_runs) > 1 else ref_runs
        cr = rng.choices(cand_runs, k=len(cand_runs)) if len(cand_runs) > 1 else cand_runs
        idx = _idx(rng, n, block)
        a = [_safe(measure, [r[i] for i in idx]) for r in rr]
        c = [_safe(measure, [x[i] for i in idx]) for x in cr]
        if None in a or None in c:
            continue
        diffs.append(sign * (mean(a) - mean(c)))
    if len(diffs) < 50:
        return point, None, None
    lo, hi = _percentiles(diffs, alpha)
    return point, lo, hi


def _auc_ok(cand, ref):
    ca, ra = cand.get("auc_runs"), ref.get("auc_runs")
    return bool(ca) and bool(ra) and len(ca[0]) == len(ra[0]) and \
        [p[0] for p in ca[0]] == [p[0] for p in ra[0]]


def _items_ok(cand, ref):
    ci, ri = cand.get("item_runs"), ref.get("item_runs")
    return bool(ci) and bool(ri) and len(ci[0]) == len(ri[0])


def paired(a: dict, b: dict) -> bool:
    """True when two samples were scored item by item on the same items, so a paired comparison is possible."""
    if _auc_ok(a, b) or _items_ok(a, b):
        return True
    return bool(a.get("units")) and bool(b.get("units")) and len(a["units"]) == len(b["units"])


def _runs_ok(sample):
    runs = sample.get("unit_runs")
    return bool(runs) and len(runs) >= 2 and all(isinstance(r, list) and r for r in runs) and \
        len({len(r) for r in runs}) == 1


def compare(cand: dict, ref: dict, direction: str, alpha: float, budget: int = 2000, measure=None,
            block: int = 1) -> dict:
    """Improvement of cand over ref (positive = cand is better), with a CI when possible.

    measure: the lab's own measure function (lab.json "aggregate": "custom"), used when both samples
    carry `item_runs`. Without it such samples fall back to repeats or the point estimate.
    block: lab.json "block_size". Items are in time order and depend on their neighbours, so the
    bootstrap draws runs of this many neighbours instead of single items.
    """
    block = max(1, int(block or 1))
    bl = f" in blocks of {block}" if block > 1 else ""
    sign = 1.0 if direction == "minimize" else -1.0
    cu, ru = cand.get("units"), ref.get("units")
    m = None
    if measure is not None and _items_ok(cand, ref):
        m, lo, hi = auc_ci(ref["item_runs"], cand["item_runs"], sign, alpha, budget, measure, block)
        k = (f" and runs ({len(cand['item_runs'])} vs {len(ref['item_runs'])})"
             if len(cand["item_runs"]) > 1 or len(ref["item_runs"]) > 1 else "")
        method = f"paired bootstrap of the lab's measure over {len(cand['item_runs'][0])} items{bl}{k}"
    if m is not None:
        pass  # the lab's own measure scored both sides
    elif _auc_ok(cand, ref):
        m, lo, hi = auc_ci(ref["auc_runs"], cand["auc_runs"], sign, alpha, budget, block=block)
        k = (f" and runs ({len(cand['auc_runs'])} vs {len(ref['auc_runs'])})"
             if len(cand["auc_runs"]) > 1 or len(ref["auc_runs"]) > 1 else "")
        method = f"paired bootstrap of AUC over {len(cand['auc_runs'][0])} items{bl}{k}"
    elif _runs_ok(cand) and _runs_ok(ref) and len(cand["unit_runs"][0]) == len(ref["unit_runs"][0]):
        m, lo, hi = two_level_ci(ref["unit_runs"], cand["unit_runs"], sign, alpha, budget, block)
        method = (f"two-level bootstrap over runs ({len(cand['unit_runs'])} vs {len(ref['unit_runs'])}) "
                  f"and {len(cu or cand['unit_runs'][0])} paired units{bl}")
    elif cu and ru and len(cu) == len(ru):
        d = [sign * (r - c) for c, r in zip(cu, ru)]
        m, lo, hi = mean_ci(d, alpha, budget, block)
        method = f"paired bootstrap over {len(d)} units{bl}"
    elif len(cand.get("repeats") or []) >= 2 and len(ref.get("repeats") or []) >= 2:
        if sign > 0:
            m, lo, hi = diff_ci(ref["repeats"], cand["repeats"], alpha, budget)
        else:
            m, lo, hi = diff_ci(cand["repeats"], ref["repeats"], alpha, budget)
        method = f"bootstrap over repeats ({len(cand['repeats'])} vs {len(ref['repeats'])})"
    else:
        m, lo, hi = sign * (ref["score"] - cand["score"]), None, None
        method = "point estimate (evaluator gives no per_unit scores or repeats)"
    rel = (m / abs(ref["score"])) if ref.get("score") else None
    return {"effect": m, "rel": rel, "lo": lo, "hi": hi, "method": method, "alpha": alpha}


def significant(cmp: dict) -> bool:
    return cmp["lo"] is not None and cmp["lo"] > 0


def meets(cmp: dict, finding: dict) -> bool:
    """Does the point effect reach the pre-registered minimum effect?"""
    need = finding.get("min_effect")
    if need is None:
        return False
    eff = cmp["effect"] if finding.get("effect", "absolute") == "absolute" else cmp["rel"]
    return eff is not None and eff >= float(need)


def describe(cmp: dict, finding: dict = None) -> str:
    def f(x):
        return "n/a" if x is None else f"{x:.4g}"
    s = f"effect {f(cmp['effect'])}"
    if cmp.get("rel") is not None:
        s += f" ({cmp['rel'] * 100:.2f}%)"
    if cmp["lo"] is not None:
        s += f", {100 * (1 - cmp['alpha']):.1f}% CI [{f(cmp['lo'])}, {f(cmp['hi'])}]"
    s += f"; {cmp['method']}"
    return s
