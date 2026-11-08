"""How often does honestlab's decision rule say "found"?

Simulates many labs with honestlab's own statistics (honestlab.stats): an agent tries 15 changes on
the development split, the keep rule decides which survive, the best one is checked against the
pre-registered bar on dev, and then on the held-out split with alpha divided by the holdout budget.
The worst case is also simulated: the agent spends the whole holdout budget (3 looks) on its three
best candidates, and "found" counts if any one passes.

Each candidate's true effect is drawn around the scenario's effect, so some candidates are better
than others, as in real experiments. Per-unit errors are paired across methods (same instances).

Usage: python3 stress/calibration.py [labs_per_scenario]
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from honestlab import stats  # noqa: E402

N_DEV, N_HOLD, N_EXP, BUDGET = 200, 100, 15, 3
FINDING = {"min_effect": 0.10, "effect": "relative", "alpha": 0.05}
KEEP_ALPHA, BOOT = 0.10, 400


def errors(rng, base, effect, noise):
    """Per-unit errors of a method whose true relative improvement over the reference is `effect`."""
    return [max(0.0, b * (1 - effect) + rng.gauss(0, noise)) for b in base]


def one_lab(rng, true_effect, spread=0.03, noise=1.5):
    dev_base = [abs(rng.gauss(10, 3)) for _ in range(N_DEV)]
    hold_base = [abs(rng.gauss(10, 3)) for _ in range(N_HOLD)]
    ref_dev = {"score": sum(dev_base) / N_DEV, "units": dev_base}
    ref_hold = {"score": sum(hold_base) / N_HOLD, "units": hold_base}
    best = ref_dev
    tried = []
    for _ in range(N_EXP):
        eff = rng.gauss(true_effect, spread) if spread else true_effect   # some changes are better than others
        u = errors(rng, dev_base, eff, noise)
        cand = {"score": sum(u) / N_DEV, "units": u}
        tried.append((cand, eff))
        cmp = stats.compare(cand, best, "minimize", KEEP_ALPHA, BOOT)
        if cand["score"] < best["score"] and stats.significant(cmp):
            best = cand
    # candidates that meet the bar on dev, best first
    ranked = sorted(tried, key=lambda t: t[0]["score"])
    passing = [(c, e) for c, e in ranked
               if stats.meets(stats.compare(c, ref_dev, "minimize", FINDING["alpha"], BOOT), FINDING)]
    alpha_h = FINDING["alpha"] / BUDGET
    outcomes = []
    for c, e in passing[:BUDGET]:
        hu = errors(rng, hold_base, e, noise)
        hc = stats.compare({"score": sum(hu) / N_HOLD, "units": hu}, ref_hold, "minimize", alpha_h, BOOT)
        outcomes.append((stats.meets(hc, FINDING) and stats.significant(hc), e))
    bar = FINDING["min_effect"]
    found1 = bool(outcomes and outcomes[0][0])
    false1 = found1 and outcomes[0][1] < bar
    found3 = any(o for o, _ in outcomes)
    false3 = any(o and e < bar for o, e in outcomes)
    real = max(e for _, e in tried) >= bar          # at least one tried change truly reaches the bar
    return found1, false1, found3, false3, real


SCENARIOS = [
    # label, mean true effect, spread between changes, per-unit measurement noise
    ("no effect at all, quiet measurement", 0.00, 0.0, 1.5),
    ("no effect at all, noisy measurement", 0.00, 0.0, 6.0),
    ("small effects (mean 5%), noisy", 0.05, 0.03, 6.0),
    ("effects just below the bar (8%), noisy", 0.08, 0.0, 6.0),
    ("effect at the bar (10%), noisy", 0.10, 0.0, 6.0),
    ("effect above the bar (15%), noisy", 0.15, 0.0, 6.0),
    ("effect well above the bar (20%), quiet", 0.20, 0.0, 1.5),
]


def main():
    labs = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    rng = random.Random(2026)
    rows = []
    for label, eff, spread, noise in SCENARIOS:
        c = [0, 0, 0, 0, 0]
        for _ in range(labs):
            for k, v in enumerate(one_lab(rng, eff, spread, noise)):
                c[k] += v
        r = {"scenario": label, "mean_effect": eff, "spread": spread, "noise": noise, "labs": labs,
             "found_one_look": c[0] / labs, "false_found_one_look": c[1] / labs,
             "found_three_looks": c[2] / labs, "false_found_three_looks": c[3] / labs,
             "a_change_truly_reaches_bar": c[4] / labs}
        rows.append(r)
        print(f"{label:42} found {r['found_one_look']:6.1%} (false {r['false_found_one_look']:5.1%}) | "
              f"3 looks: found {r['found_three_looks']:6.1%} (false {r['false_found_three_looks']:5.1%}) | "
              f"a change truly >= bar in {r['a_change_truly_reaches_bar']:6.1%} of labs", flush=True)
    out = Path(__file__).resolve().parent / "calibration.json"
    out.write_text(json.dumps({"settings": {"n_dev": N_DEV, "n_holdout": N_HOLD, "experiments": N_EXP,
                                            "holdout_budget": BUDGET, "finding": FINDING,
                                            "keep_alpha": KEEP_ALPHA, "bootstrap": BOOT, "seed": 2026},
                               "results": rows}, indent=2))


if __name__ == "__main__":
    main()
