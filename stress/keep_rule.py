"""Which keep rule fools itself less: autoresearch's or honestlab's?

Usage: python3 stress/keep_rule.py run [budget_sec]   # trains every variant, writes stress/keep_rule_runs.json
       python3 stress/keep_rule.py report             # applies the rules, writes stress/keep_rule.json

The task is the character model example (`honestlab init --example charlm`): bits per
character on Dom Casmurro, lower is better. Each variant changes one setting of the baseline
model, as an agent would in one experiment. Two variants change nothing (same code), to show
what noise alone does.

Every variant is trained with 6 seeds. Each training is scored on the dev text and on the
holdout text, which no rule ever sees:
- Seeds 0 to 2 are what a rule may use to decide.
- Seeds 3 to 5 on the holdout text are the truth: did the change really help on new text and
  new training runs?

Rules compared (lower bpc is better):
- autoresearch: one run (seed 0), keep if dev bpc is lower than the baseline's.
- honestlab today, 1 run: seed 0, keep if the paired bootstrap over text chunks says the gain is
  unlikely to be luck (alpha 0.1, honestlab's default keep rule).
- honestlab, 3 runs: seeds 0 to 2 averaged per chunk, then the same bootstrap (repeats = 3).
- honestlab, 3 runs, two-level: the bootstrap resamples the runs as well as the chunks, so
  run-to-run noise counts (what honestlab now does when repeats is 2 or more).
"""
import json
import os
import re
import sys
import time
import gzip
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from honestlab import stats  # noqa: E402

EX = REPO / "honestlab" / "examples" / "charlm"
RUNS = REPO / "stress" / "keep_rule_runs.json"
OUT = REPO / "stress" / "keep_rule.json"
SEEDS = 6
DECIDE = (0, 1, 2)
TRUTH = (3, 4, 5)

VARIANTS = {
    "baseline": [],
    "same code (a)": [],
    "same code (b)": [],
    "learning rate 0.05": [("LR = 0.1", "LR = 0.05")],
    "learning rate 0.2": [("LR = 0.1", "LR = 0.2")],
    "learning rate 0.4": [("LR = 0.1", "LR = 0.4")],
    "hidden 32": [("HIDDEN = 64", "HIDDEN = 32")],
    "hidden 128": [("HIDDEN = 64", "HIDDEN = 128")],
    "embedding 8": [("EMBED = 16", "EMBED = 8")],
    "embedding 24": [("EMBED = 16", "EMBED = 24")],
    "context 4": [("CONTEXT = 3", "CONTEXT = 4")],
    "context 6": [("CONTEXT = 3", "CONTEXT = 6")],
    "batch 64": [("BATCH = 128", "BATCH = 64")],
    "batch 256": [("BATCH = 128", "BATCH = 256")],
    "smaller start weights": [("rng.normal(0, 0.1, (vocab, EMBED))", "rng.normal(0, 0.05, (vocab, EMBED))")],
}


def splits():
    body = gzip.open(EX / "dom_casmurro.txt.gz", "rt", encoding="utf-8").read()
    chap = [m.start() for m in re.finditer(r"(?m)^[IVXLC]+\n", body)]
    parts = [body[a:b] for a, b in zip(chap, chap[1:] + [len(body)])]
    return "".join(parts[:104]), "".join(parts[104:126]), "".join(parts[126:])


def load_variant(name):
    src = (EX / "model.py").read_text(encoding="utf-8")
    for old, new in VARIANTS[name]:
        assert old in src, (name, old)
        src = src.replace(old, new)
    mod = type(sys)("model_" + re.sub(r"\W", "_", name))
    exec(compile(src, f"<{name}>", "exec"), mod.__dict__)
    return mod


def score(mod, state, ids, chunk=400):
    """The same scoring as the example's evaluator: chunks, left to right, mean bpc per chunk."""
    k = mod.CONTEXT
    n = len(ids) // chunk
    chunks = ids[: n * chunk].reshape(n, chunk)
    padded = np.concatenate([np.zeros((n, k), dtype=np.int64), chunks], axis=1)
    bits = np.zeros((n, chunk))
    rows = np.arange(n)
    for t in range(chunk):
        p = mod.predict(state, padded[:, t:t + k].copy())
        bits[:, t] = -np.log2(np.maximum(p[rows, chunks[:, t]], 1e-12))
    return bits.mean(axis=1).tolist()


def run(budget):
    train, dev, hold = splits()
    chars = sorted(set(train))
    index = {c: i + 1 for i, c in enumerate(chars)}
    vocab = len(chars) + 1
    enc = lambda s: np.array([index.get(c, 0) for c in s], dtype=np.int64)  # noqa: E731
    tr, dv, ho = enc(train), enc(dev), enc(hold)
    data = json.loads(RUNS.read_text()) if RUNS.exists() else {"budget_sec": budget, "runs": {}}
    assert data["budget_sec"] == budget, "delete stress/keep_rule_runs.json to change the budget"
    for seed in range(SEEDS):  # seed-major order: an early stop still leaves comparable seeds
        for name in VARIANTS:
            key = f"{name}|{seed}"
            if key in data["runs"]:
                continue
            mod = load_variant(name)
            t0 = time.time()
            state = mod.train(tr.copy(), vocab, budget, np.random.default_rng(seed))
            secs = time.time() - t0
            data["runs"][key] = {"dev": score(mod, state, dv), "holdout": score(mod, state, ho),
                                 "train_seconds": round(secs, 2)}
            RUNS.write_text(json.dumps(data))
            d = data["runs"][key]
            print(f"{name:24} seed {seed}  dev {np.mean(d['dev']):.4f}  holdout {np.mean(d['holdout']):.4f}  "
                  f"{secs:.1f}s", flush=True)


def sample(units_list, two_level=False):
    units = [sum(col) / len(col) for col in zip(*units_list)]
    out = {"score": sum(units) / len(units), "units": units, "repeats": [sum(u) / len(u) for u in units_list]}
    if two_level:
        out["unit_runs"] = units_list
    return out


def report():
    data = json.loads(RUNS.read_text())
    runs = data["runs"]
    get = lambda name, seeds, split: [runs[f"{name}|{s}"][split] for s in seeds]  # noqa: E731
    base_truth = np.mean([np.mean(u) for u in get("baseline", TRUTH, "holdout")])
    rows = []
    for name in VARIANTS:
        if name == "baseline":
            continue
        truth = base_truth - np.mean([np.mean(u) for u in get(name, TRUTH, "holdout")])  # > 0: really better
        one_c, one_b = sample(get(name, (0,), "dev")), sample(get("baseline", (0,), "dev"))
        three_c, three_b = sample(get(name, DECIDE, "dev")), sample(get("baseline", DECIDE, "dev"))
        c1 = stats.compare(one_c, one_b, "minimize", 0.1, 2000)
        c3 = stats.compare(three_c, three_b, "minimize", 0.1, 2000)
        c3t = stats.compare(sample(get(name, DECIDE, "dev"), True), sample(get("baseline", DECIDE, "dev"), True),
                            "minimize", 0.1, 2000)
        rows.append({
            "variant": name,
            "dev_gain_one_run": round(c1["effect"], 4),
            "true_gain": round(float(truth), 4),
            "autoresearch_keeps": c1["effect"] > 0,
            "honestlab_1run_keeps": stats.significant(c1),
            "honestlab_3runs_keeps": stats.significant(c3),
            "honestlab_3runs_two_level_keeps": stats.significant(c3t),
            "ci_1run": [round(c1["lo"], 4), round(c1["hi"], 4)],
            "ci_3runs": [round(c3["lo"], 4), round(c3["hi"], 4)],
            "ci_3runs_two_level": [round(c3t["lo"], 4), round(c3t["hi"], 4)],
        })
    # A change "really helps" when its true gain beats the run-to-run noise of identical code.
    noise = max(abs(r["true_gain"]) for r in rows if r["variant"].startswith("same code"))
    summary = {}
    for rule in ("autoresearch_keeps", "honestlab_1run_keeps", "honestlab_3runs_keeps",
                 "honestlab_3runs_two_level_keeps"):
        kept = [r for r in rows if r[rule]]
        good = [r for r in kept if r["true_gain"] > noise]
        bad = [r for r in kept if r["true_gain"] <= 0]
        missed = [r for r in rows if not r[rule] and r["true_gain"] > noise]
        summary[rule] = {"kept": len(kept), "kept_really_better": len(good), "kept_really_worse_or_equal": len(bad),
                         "missed_really_better": len(missed),
                         "kept_names": [r["variant"] for r in kept]}
    out = {"budget_sec": data["budget_sec"], "seeds": SEEDS, "decide_seeds": DECIDE, "truth_seeds": TRUTH,
           "baseline_true_bpc": round(float(base_truth), 4), "noise_threshold": round(noise, 4),
           "summary": summary, "rows": rows}
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(f"budget {data['budget_sec']} s, baseline holdout bpc {base_truth:.4f}, noise threshold {noise:.4f}")
    print(f"{'variant':24} {'dev gain':>9} {'true gain':>9}  auto  hl-1  hl-3  hl-3b")
    for r in rows:
        f = lambda b: " yes" if b else "  - "  # noqa: E731
        print(f"{r['variant']:24} {r['dev_gain_one_run']:9.4f} {r['true_gain']:9.4f}  {f(r['autoresearch_keeps'])}"
              f"  {f(r['honestlab_1run_keeps'])}  {f(r['honestlab_3runs_keeps'])}"
              f"  {f(r['honestlab_3runs_two_level_keeps'])}")
    for rule, s in summary.items():
        print(f"{rule}: kept {s['kept']}, really better {s['kept_really_better']}, "
              f"worse or equal {s['kept_really_worse_or_equal']}, missed {s['missed_really_better']}")


if __name__ == "__main__":
    if sys.argv[1:2] == ["run"]:
        run(float(sys.argv[2]) if len(sys.argv) > 2 else 15.0)
    else:
        report()
