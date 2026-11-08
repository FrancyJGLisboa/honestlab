"""Método conhecido: modelo aditivo simples (regressão com efeito de hora, distância e chuva).

tempo = base + b*distancia + efeito_da_hora + c*chuva, ajustado em poucas rodadas
(backfitting) com médias por hora; sem bibliotecas.
"""


def _lin(xs, ys):
    n = len(xs)
    mx, my = sum(xs) / n, sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs) or 1.0
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    return my - b * mx, b


def fit(train):
    d = [r["distancia_km"] for r in train]
    c = [r["chuva_mm"] for r in train]
    y = [r["tempo_entrega_min"] for r in train]
    hour = {r["hora"] for r in train}
    eh = {h: 0.0 for h in hour}
    a = b = cb = 0.0
    for _ in range(10):
        a, b = _lin(d, [yi - eh[r["hora"]] - cb * ci for yi, r, ci in zip(y, train, c)])
        _, cb = _lin(c, [yi - a - b * di - eh[r["hora"]] for yi, r, di in zip(y, train, d)])
        res = {h: [] for h in hour}
        for yi, r, di, ci in zip(y, train, d, c):
            res[r["hora"]].append(yi - a - b * di - cb * ci)
        eh = {h: sum(v) / len(v) for h, v in res.items()}
    return {"a": a, "b": b, "c": cb, "eh": eh}


def predict(m, rows):
    return [max(1.0, m["a"] + m["b"] * r["distancia_km"] + m["c"] * r["chuva_mm"]
                + m["eh"].get(r["hora"], 0.0)) for r in rows]
