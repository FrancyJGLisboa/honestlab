"""Evaluator: erro médio da previsão de vendas de amanhã, dia a dia, sem olhar o futuro.

  python eval/evaluate.py --split dev|holdout

* dev: pontua os dias de data/dev a partir de 2024-01-29 (4 semanas de histórico).
* holdout: o histórico começa com data/dev (passado conhecido) e pontua cada dia da
  pasta final. Os dias do holdout entram no histórico só DEPOIS de serem previstos.
* Para cada dia D chama src/model.py: predict(history, day), onde
    history = lista de dicts de todos os dias < D (com "vendas"),
    day     = dict do dia D SEM "vendas" (data, dia_semana, feriado, previsão do tempo
              feita na véspera: prev_tmax, prev_tmedia, prev_chuva_mm,
              prev_horas_chuva_aberto; vazios viram None).
* A saída tem de ser um número finito entre 0 e 10000, senão o evaluator falha.
* Métrica: mae = erro absoluto médio (em unidades de venda da planilha) por dia.
  Só semanas completas (seg-dom) são pontuadas; os outros dias entram só no histórico.
  per_unit = erro médio de cada semana pontuada (média de per_unit = mae).
"""
import argparse
import copy
import datetime as dt
import csv
import glob
import json
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "src"))
import model  # noqa: E402

FIRST_SCORED_DEV = "2024-01-29"
NUM = ["feriado", "vendas", "prev_tmax", "prev_tmedia", "prev_chuva_mm", "prev_horas_chuva_aberto"]


def load(folder):
    rows = []
    for path in sorted(glob.glob(os.path.join(ROOT, "data", folder, "*.csv"))):
        with open(path, newline="") as f:
            for r in csv.DictReader(f):
                for k in NUM:
                    r[k] = None if r.get(k, "") == "" else float(r[k])
                rows.append(r)
    rows.sort(key=lambda r: r["data"])
    if not rows:
        raise SystemExit(f"no data in data/{folder}")
    return rows


def monday_of(date):
    d = dt.date.fromisoformat(date)
    return (d - dt.timedelta(days=d.weekday())).isoformat()


def full_week(date, rows):
    m = monday_of(date)
    return sum(1 for r in rows if monday_of(r["data"]) == m) == 7


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    split = ap.parse_args().split

    dev = load("dev")
    if split == "dev":
        history = [r for r in dev if r["data"] < FIRST_SCORED_DEV]
        scored = [r for r in dev if r["data"] >= FIRST_SCORED_DEV]
    else:
        history = list(dev)
        scored = load("holdout")
        if scored[0]["data"] <= dev[-1]["data"]:
            raise SystemExit("holdout must come after dev")

    weeks = {}
    errors = []
    for r in scored:
        if not full_week(r["data"], scored):
            history.append(r)  # dia de semana incompleta: só entra no histórico
            continue
        day = {k: v for k, v in r.items() if k != "vendas"}
        pred = model.predict(copy.deepcopy(history), day)
        try:
            pred = float(pred)
        except (TypeError, ValueError):
            raise SystemExit(f"invalid prediction for {r['data']}: {pred!r}")
        if not math.isfinite(pred) or pred < 0 or pred > 10000:
            raise SystemExit(f"invalid prediction for {r['data']}: {pred!r}")
        err = abs(pred - r["vendas"])
        errors.append(err)
        weeks.setdefault(monday_of(r["data"]), []).append(err)
        history.append(r)

    # sem arredondar: a média de per_unit tem de ser exatamente o mae
    per_unit = [sum(v) / len(v) for _, v in sorted(weeks.items())]
    mae = sum(per_unit) / len(per_unit)  # semanas completas: igual ao erro médio por dia
    print(json.dumps({"mae": mae, "n_days": len(errors), "per_unit": per_unit}))


if __name__ == "__main__":
    main()
