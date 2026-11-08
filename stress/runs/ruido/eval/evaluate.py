"""Avaliador: previsão das vendas do dia, feita de manhã, andando no tempo.

Uso: python eval/evaluate.py --split dev|holdout
Para cada dia depois do período de aquecimento (WARMUP dias), chama
src/predict.py: predict(history, today) e mede o erro absoluto em vendas.
 - history: cópia das linhas de TODOS os dias anteriores (com cliques e vendas).
 - today: so data, dia_semana e gasto_anuncio (sem cliques e sem vendas do dia).
Última linha impressa: {"mae": ..., "per_unit": [...]}
"""
import argparse, copy, csv, glob, importlib.util, json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WARMUP = 90
NUM = {"dia_semana": int, "gasto_anuncio": float, "cliques": float, "vendas": float}


def load(split):
    lab = json.load(open(os.path.join(ROOT, "lab.json")))
    folder = os.path.join(ROOT, lab["holdout_dir"] if split == "holdout" else "data/dev")
    rows = []
    for p in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        for r in csv.DictReader(open(p)):
            rows.append({k: (NUM[k](v) if k in NUM else v) for k, v in r.items()})
    rows.sort(key=lambda r: r["data"])
    dates = [r["data"] for r in rows]
    if len(set(dates)) != len(dates):
        sys.exit("datas repetidas nos dados")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    split = ap.parse_args().split
    rows = load(split)
    spec = importlib.util.spec_from_file_location("predict_mod", os.path.join(ROOT, "src", "predict.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    errs = []
    for i in range(WARMUP, len(rows)):
        hist = copy.deepcopy(rows[:i])
        t = rows[i]
        today = {"data": t["data"], "dia_semana": t["dia_semana"], "gasto_anuncio": t["gasto_anuncio"]}
        y = mod.predict(hist, today)
        try:
            y = float(y)
        except Exception:
            sys.exit(f"previsão inválida em {t['data']}: {y!r}")
        if not math.isfinite(y) or y < 0 or y > 10000:
            sys.exit(f"previsão fora do aceitável em {t['data']}: {y}")
        errs.append(abs(y - t["vendas"]))
    print(json.dumps({"mae": sum(errs) / len(errs), "n": len(errs), "per_unit": errs}))


if __name__ == "__main__":
    main()
