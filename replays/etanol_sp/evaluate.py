"""Teste de evento: ICMS do etanol hidratado em São Paulo (9,57% -> 12%, a partir de 1/7/2023).

Com HONESTLAB_EVENT_DATE (início de uma semana da ANP, AAAA-MM-DD): imprime a diferença, em log, entre a
média das 4 semanas a partir dessa data e o preço normal (src/model.py, só com semanas anteriores).
HONESTLAB_EVENT_SERIES escolhe a série: treated = São Paulo, mg = Minas Gerais (controle).
Sem a data: imprime menos o erro, em log, da previsão de uma semana à frente (medida inicial do modelo).
"""
import argparse, csv, json, math, os, sys
sys.path.insert(0, "src")
import model

ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
rows = list(csv.DictReader(open("data/dev/prices.csv")))
if a.split == "holdout":
    rows += list(csv.DictReader(open("data/holdout/prices.csv")))
col = {"treated": "sp", "mg": "mg"}[os.environ.get("HONESTLAB_EVENT_SERIES", "treated")]
weeks = [r["w"] for r in rows]
price = {r["w"]: float(r[col]) for r in rows}
date = os.environ.get("HONESTLAB_EVENT_DATE")
if not date:
    u = [-abs(math.log(price[weeks[i]]) - math.log(model.normal([price[w] for w in weeks[:i]])))
         for i in range(1, len(weeks))]
    print(json.dumps({"gap": sum(u) / len(u), "per_unit": u}))
    sys.exit()
i = weeks.index(date)
window = weeks[i:i + 4]
before = [price[w] for w in weeks[:i]]
assert len(window) == 4, "window incomplete"
gap = sum(math.log(price[w]) for w in window) / 4 - math.log(model.normal(before))
print(json.dumps({"gap": gap}))
