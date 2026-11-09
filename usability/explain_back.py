"""Explain-back test: can a person repeat the result correctly after reading the report?

For each finished lab folder:
1. A reader model plays a person with no technical training. It reads one document once and
   explains the result to a business partner in its own words.
2. An extractor model reads ONLY that explanation and writes down what it claims (verdict,
   numbers, how sure, whether it is new) as JSON. It does not see the document.
3. Python compares those claims with the truth computed from the lab files (state.json, lab.json,
   ledger.jsonl), not from the report text.

Two documents are compared on the same labs:
- "report": honestlab's REPORT.md.
- "log": an autoresearch-style results.tsv (one row per attempt: id, score, keep/discard,
  description), built from the same ledger.

python explain_back.py --labs stress/runs/english stress/runs/ruido ... --samples 3 --out RESULT.json
"""
import argparse
import concurrent.futures as cf
import json
import os
import re
import shlex
import subprocess
from pathlib import Path

ENV = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
EXTRA = shlex.split(os.environ.get("HONESTLAB_SIM_CLAUDE_ARGS", ""))
READER_MODEL = os.environ.get("HONESTLAB_EXPLAIN_READER", "haiku")
EXTRACT_MODEL = os.environ.get("HONESTLAB_EXPLAIN_EXTRACTOR", "sonnet")

READER = """You are a person with no technical training. You own a small business. Someone ran a test of
your idea and gave you the document below. Read it once. Then explain the result to your business
partner, in your own words, in 120 words or fewer. Say:
- what was tested;
- what the result is;
- how much better or worse, with numbers;
- how sure the result is;
- what you will do next.
Write in the same language as the document. Write only the explanation.

DOCUMENT ({name}):
{doc}"""

EXTRACT = """Read the explanation below. Write down ONLY what it claims. Do not guess. Use null when the
explanation does not say it.

Fields:
- verdict: "found" (it says the new method is a real improvement over the best method that
  already existed), "fragile" (it says there is a sign of improvement but it is not sure or not
  confirmed), "not_found" (it says nothing beat the existing method by the agreed margin), or
  "unclear".
- start_value: the score of what the person used before, as a number.
- known_value: the score of the best method that already existed before the test, as a number.
- best_value: the score of the best new attempt, as a number.
- gain_percent: the improvement it states, in percent (positive = better). null if not in percent.
- gain_vs: what that improvement is compared with: "start", "known" or "unclear".
- confirmed_on_new_data: "yes", "no" or null.
- novelty: "proven_new" (it says the result is certainly new to the world), "not_proven" (it says
  that newness is unknown or not proven) or null.
- next_step: the next action it states, in a few words, or null.

EXPLANATION:
{text}"""

SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"enum": ["found", "fragile", "not_found", "unclear"]},
        "start_value": {"type": ["number", "null"]},
        "known_value": {"type": ["number", "null"]},
        "best_value": {"type": ["number", "null"]},
        "gain_percent": {"type": ["number", "null"]},
        "gain_vs": {"enum": ["start", "known", "unclear", None]},
        "confirmed_on_new_data": {"enum": ["yes", "no", None]},
        "novelty": {"enum": ["proven_new", "not_proven", None]},
        "next_step": {"type": ["string", "null"]},
    },
    "required": ["verdict", "start_value", "known_value", "best_value", "gain_percent", "gain_vs",
                 "confirmed_on_new_data", "novelty", "next_step"],
}

VERDICTS = [("fragile", r"(Sinal promissor|Promising but fragile)"),
            ("not_found", r"(Não encontrou|Not found)"),
            ("found", r"(Encontrou|Found)")]


def load(lab: Path):
    cfg = json.loads((lab / "lab.json").read_text())
    st = json.loads((lab / ".honestlab" / "state.json").read_text())
    led = [json.loads(x) for x in (lab / (cfg.get("lab_dir") or ".") / "ledger.jsonl").read_text().splitlines()
           if x.strip()]
    return cfg, st, led


def truth(lab: Path) -> dict:
    """The facts a correct explanation must not contradict, from the lab files."""
    cfg, st, led = load(lab)
    report = (lab / "REPORT.md").read_text(encoding="utf-8")
    head = report.split("##", 2)[1] if "##" in report else report
    verdict = next((v for v, rx in VERDICTS if re.search(rx, head)), "unclear")
    sign = 1 if cfg.get("direction", "minimize") == "minimize" else -1
    start, best = st["baseline"], st["best"]
    refs = {n: r["dev"] for n, r in (st.get("references") or {}).items() if r.get("dev") is not None}
    known = min([start, *refs.values()], key=lambda x: sign * x)

    def gain(new, old):
        return 100.0 * sign * (old - new) / abs(old) if old else None
    gains = {"start": gain(best, start), "known": gain(best, known)}
    holdout = []
    for e in led:
        if e.get("type") == "finding" and e.get("holdout_comparison"):
            hc = e["holdout_comparison"]
            if hc.get("rel") is not None:
                holdout.append(100.0 * hc["rel"])
    confirmed = any(e.get("type") == "finding" and e.get("holdout_confirmed") for e in led)
    # A finding's candidate and its reference, as measured on the held-out data, are true numbers too.
    also = {"start": [], "known": [], "best": []}
    samples = lab / ".honestlab" / "samples"
    for e in led:
        if e.get("type") == "finding" and e.get("holdout_reference"):
            ref = e["holdout_reference"]
            for key, name in (("best", f"{e['id']}-holdout"), ("known", f"{e['id']}-reference-holdout"),
                              ("known", "baseline-holdout" if ref == "baseline" else f"ref-{ref}-holdout")):
                f = samples / f"{name}.json"
                if f.exists():
                    also[key].append(json.loads(f.read_text())["score"])
            exp = next((x for x in led if x.get("type") == "experiment" and x.get("id") == e.get("best_id")), None)
            if exp and exp.get("score") is not None:
                also["best"].append(exp["score"])
    return {"verdict": verdict, "start": start, "known": known, "best": best, "gains": gains, "also": also,
            "holdout_gains": holdout, "confirmed": confirmed, "direction": cfg.get("direction"),
            "metric": cfg.get("metric")}


def results_tsv(lab: Path) -> str:
    """What autoresearch leaves behind: one row per attempt, nothing else."""
    _, st, led = load(lab)
    rows = ["commit\tscore\tstatus\tdescription", f"baseline\t{st['baseline']:.6g}\tkeep\tbaseline"]
    for e in led:
        if e.get("type") == "experiment":
            score = e.get("score")
            status = "crash" if e.get("error") else ("keep" if e.get("decision") == "keep" else "discard")
            rows.append(f"{e['id']}\t{'' if score is None else format(score, '.6g')}\t{status}\t"
                        f"{(e.get('hypothesis') or '').strip()}")
    return "\n".join(rows)


def claude(prompt: str, model: str, schema=None) -> str:
    cmd = ["claude", *EXTRA, "-p", prompt, "--model", model, "--max-turns", "1", "--allowedTools", "",
           "--output-format", "json"]
    if schema:
        cmd += ["--json-schema", json.dumps(schema)]
    r = subprocess.run(cmd, capture_output=True, text=True, env=ENV, timeout=600)
    j = json.loads(r.stdout)
    if schema and isinstance(j.get("structured_output"), dict):
        return json.dumps(j["structured_output"])
    return j.get("result", "")


def near(a, b, rel=0.02, abs_=1e-9):
    return a is not None and b is not None and abs(a - b) <= max(abs_, rel * abs(b))


def check(claims: dict, t: dict) -> dict:
    out = {"verdict_ok": claims.get("verdict") == t["verdict"]}
    wrong = []
    for k in ("start", "known", "best"):
        v = claims.get(f"{k}_value")
        ok_values = [t[k], *t.get("also", {}).get(k, [])]
        if v is not None and not any(near(v, x) for x in ok_values):
            wrong.append(f"{k}: said {v}, true {t[k]:.4g}")
    g = claims.get("gain_percent")
    if g is not None:
        allowed = [x for x in (*t["gains"].values(), *t["holdout_gains"]) if x is not None]
        if not any(abs(g - x) <= 2.0 for x in allowed):
            wrong.append(f"gain: said {g}%, true one of {', '.join(f'{x:.1f}%' for x in allowed)}")
    out["numbers_wrong"] = wrong
    out["numbers_ok"] = not wrong
    over = []
    if t["verdict"] != "found" and claims.get("verdict") == "found":
        over.append("says it beat the best known method")
    if claims.get("confirmed_on_new_data") == "yes" and not t["confirmed"]:
        over.append("says it was confirmed on new data")
    if claims.get("novelty") == "proven_new":
        over.append("says it is certainly new")
    out["overclaims"] = over
    out["next_step_ok"] = bool(claims.get("next_step"))
    out["pass"] = out["verdict_ok"] and out["numbers_ok"] and not over
    return out


def one(lab: Path, kind: str, i: int, t: dict) -> dict:
    doc = (lab / "REPORT.md").read_text(encoding="utf-8") if kind == "report" else results_tsv(lab)
    name = "REPORT.md" if kind == "report" else "results.tsv"
    text = claude(READER.format(name=name, doc=doc), READER_MODEL).strip()
    raw = claude(EXTRACT.format(text=text), EXTRACT_MODEL, SCHEMA)
    m = re.search(r"\{.*\}", raw, re.S)
    claims = json.loads(m.group(0)) if m else {}
    return {"lab": lab.name, "kind": kind, "sample": i, "explanation": text, "claims": claims,
            "check": check(claims, t)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--labs", nargs="+", required=True)
    ap.add_argument("--samples", type=int, default=3)
    ap.add_argument("--kinds", nargs="+", default=["report", "log"])
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    labs = [Path(x).resolve() for x in a.labs]
    truths = {lab.name: truth(lab) for lab in labs}
    jobs = [(lab, k, i) for lab in labs for k in a.kinds for i in range(a.samples)]
    rows = []
    with cf.ThreadPoolExecutor(a.workers) as ex:
        futs = {ex.submit(one, lab, k, i, truths[lab.name]): (lab.name, k, i) for lab, k, i in jobs}
        for f in cf.as_completed(futs):
            try:
                rows.append(f.result())
            except Exception as e:  # keep going; a failed call is reported, not hidden
                lab, k, i = futs[f]
                rows.append({"lab": lab, "kind": k, "sample": i, "error": repr(e)[:300]})
            r = rows[-1]
            print(r["lab"], r["kind"], r["sample"], "ERROR" if "error" in r else
                  ("pass" if r["check"]["pass"] else f"FAIL {r['check']}"), flush=True)
    rows.sort(key=lambda r: (r["lab"], r["kind"], r["sample"]))
    summary = {}
    for k in a.kinds:
        rs = [r for r in rows if r["kind"] == k and "error" not in r]
        summary[k] = {"n": len(rs), "errors": sum(1 for r in rows if r["kind"] == k and "error" in r)}
        for key in ("pass", "verdict_ok", "numbers_ok", "next_step_ok"):
            summary[k][key] = sum(1 for r in rs if r["check"][key])
        summary[k]["overclaim"] = sum(1 for r in rs if r["check"]["overclaims"])
    res = {"reader_model": READER_MODEL, "extractor_model": EXTRACT_MODEL, "truth": truths,
           "summary": summary, "rows": rows}
    Path(a.out).write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
