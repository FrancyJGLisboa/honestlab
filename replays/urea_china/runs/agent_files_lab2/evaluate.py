"""Avaliador do teste de evento (ureia, inspecao chinesa de out/2021).

  python eval/evaluate.py --split dev|holdout
Sem HONESTLAB_EVENT_DATE: erro do modelo em meses normais (origens 2010-01..2021-06,
janelas de 3 meses, so dados de desenvolvimento).
Com HONESTLAB_EVENT_DATE=AAAA-MM: ajusta o modelo so com dados ANTES da data e imprime a
diferenca media (real menos normal, em log) dos 3 meses que comecam na data.
Datas de 2021-10 em diante leem tambem os dados guardados (uma vez, no teste final).
"""
import argparse, csv, json, os, sys, math

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "src"))
from model import predict_normal

WINDOW = 3


def load(path):
    with open(path) as f:
        return [{"month": r["month"], **{k: float(r[k]) for k in ("urea", "gas_eu", "gas_us")}}
                for r in csv.DictReader(f)]


def gaps(rows, i):
    """log(real) - log(normal) dos WINDOW meses a partir do indice i; o modelo ve so rows[:i]."""
    win = rows[i:i + WINDOW]
    if len(win) < WINDOW or i < 60:
        raise SystemExit("janela invalida")
    fut = [{"gas_eu": r["gas_eu"], "gas_us": r["gas_us"]} for r in win]
    pred = predict_normal([dict(r) for r in rows[:i]], fut)
    if len(pred) != WINDOW or any(not math.isfinite(p) for p in pred):
        raise SystemExit("saida invalida do modelo")
    return [math.log(r["urea"]) - p for r, p in zip(win, pred)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    ap.parse_args()
    rows = load(os.path.join(ROOT, "data", "dev", "dev.csv"))
    ev = os.environ.get("HONESTLAB_EVENT_DATE")
    if ev and ev >= "2021-10":
        rows += load(os.path.join(ROOT, "data", "holdout", "holdout.csv"))
    idx = {r["month"]: k for k, r in enumerate(rows)}
    if ev:
        g = gaps(rows, idx[ev])
        gap = sum(g) / len(g)
        print(json.dumps({"score": gap, "gap": gap, "gap_pct": 100 * (math.exp(gap) - 1), "per_unit": g}))
        return
    errs = []
    for k in range(idx["2010-01"], idx["2021-06"] + 1):
        g = gaps(rows, k)
        errs.append(sum(abs(x) for x in g) / len(g))
    print(json.dumps({"score": sum(errs) / len(errs), "per_unit": errs}))


if __name__ == "__main__":
    main()
