"""Uncertainty for keep/discard and finding decisions (stdlib only, deterministic).

A *sample* is what one evaluation produced:
    {"score": float, "units": [float, ...] | None, "repeats": [float, ...]}
`units` are per-instance scores whose mean is the metric (paired across
solutions, because every solution is scored on the same instances).
`repeats` are whole-evaluation scores from repeated runs (for noisy evaluators).
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


def mean_ci(d, alpha, budget=2000):
    """Bootstrap percentile CI for the mean of d."""
    n = len(d)
    m = sum(d) / n
    if n < 2:
        return m, None, None
    rng = random.Random(SEED)
    b = _resamples(n, budget)
    means = [sum(rng.choices(d, k=n)) / n for _ in range(b)]
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


def compare(cand: dict, ref: dict, direction: str, alpha: float, budget: int = 2000) -> dict:
    """Improvement of cand over ref (positive = cand is better), with a CI when possible."""
    sign = 1.0 if direction == "minimize" else -1.0
    cu, ru = cand.get("units"), ref.get("units")
    if cu and ru and len(cu) == len(ru):
        d = [sign * (r - c) for c, r in zip(cu, ru)]
        m, lo, hi = mean_ci(d, alpha, budget)
        method = f"paired bootstrap over {len(d)} units"
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
