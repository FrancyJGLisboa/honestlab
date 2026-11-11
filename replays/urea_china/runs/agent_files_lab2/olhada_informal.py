"""OLHADA INFORMAL (indicio, nao prova): ureia, DAP, TSP e potassio apos out/2021.

Nao faz parte do contrato aprovado. Foi pedida depois do resultado do teste da ureia e feita
sem dados guardados nem aprovacao propria. Serve so para orientar a conversa.

Leitura combinada ANTES de rodar (para nao ajustar depois):
  Para cada adubo: desvio medio (log real - log normal) em out-dez/2021 e a fracao das 137 datas falsas
  (2010-01..2021-05) com desvio igual ou maior. "Incomum" = fracao <= 0.05.
  A) potassio comum e ureia incomum -> indicio de algo especifico da ureia (compativel com China, mas nao prova).
  B) potassio tambem incomum        -> indicio de choque geral dos adubos: nao separa China de outros fatores.
  C) DAP/TSP incomuns e potassio comum -> compativel com restricao chinesa a fosfatos (mesma ressalva).

Uso: python -I notes/olhada_informal.py <planilha.xlsx> <pasta_do_modelo_src>
O modelo do 'preco normal' e o mesmo do teste aprovado (log do adubo ~ log do mes anterior + log gas EU + log gas US).
"""
import sys, math, openpyxl

xlsx, srcdir = sys.argv[1], sys.argv[2]
sys.path.insert(0, srcdir)
from model import predict_normal  # versao com argumento `key`

rows = list(openpyxl.load_workbook(xlsx, read_only=True)["Monthly Prices"].iter_rows(values_only=True))
h = [str(c).strip() if c else "" for c in rows[4]]
f = lambda p: [i for i, c in enumerate(h) if c.startswith(p)][0]
cols = {"urea": f("Urea"), "dap": f("DAP"), "tsp": f("TSP"), "potassio": f("Potassium chloride"),
        "gas_eu": f("Natural gas, Europe"), "gas_us": f("Natural gas, US")}


def num(v):
    try:
        return float(v)
    except Exception:
        return None


data = []
for r in rows[6:]:
    if not r[0] or "M" not in str(r[0]):
        continue
    y, m = str(r[0]).split("M")
    d = f"{y}-{m}"
    v = {k: num(r[c]) for k, c in cols.items()}
    if None in v.values() or d < "1990-01" or d > "2021-12":
        continue
    data.append({"month": d, **v})
idx = {r["month"]: i for i, r in enumerate(data)}


def gap(key, i):
    win = data[i:i + 3]
    fut = [{"gas_eu": r["gas_eu"], "gas_us": r["gas_us"]} for r in win]
    p = predict_normal([dict(r) for r in data[:i]], fut, key)
    return sum(math.log(r[key]) - q for r, q in zip(win, p)) / 3


ev = idx["2021-10"]
fakes = range(idx["2010-01"], idx["2021-05"] + 1)
print(f"datas falsas: {len(fakes)}")
print(f"{'adubo':10s} {'desvio':>8s} {'acima do normal':>16s} {'fracao de datas falsas >= evento':>34s}")
for k in ("urea", "dap", "tsp", "potassio"):
    g = gap(k, ev)
    fk = [gap(k, i) for i in fakes]
    frac = sum(1 for x in fk if x >= g) / len(fk)
    print(f"{k:10s} {g:8.3f} {100*(math.exp(g)-1):15.0f}% {frac:34.3f}")
