"""Método conhecido: prometer sempre a mediana (a versão robusta da média de hoje)."""


def fit(train):
    t = sorted(r["tempo_entrega_min"] for r in train)
    n = len(t)
    return t[n // 2] if n % 2 else (t[n // 2 - 1] + t[n // 2]) / 2


def predict(model, rows):
    return [model for _ in rows]
