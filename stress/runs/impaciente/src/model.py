import numpy as np

DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
WINDOW = 120


def features(r):
    f = [1.0, r["temp_max_c"], r["feriado"], r["chuva_mm"]]
    f += [1.0 if r["dia_semana"] == d else 0.0 for d in DIAS[1:]]
    return f


def predict(history, today):
    h = history[-WINDOW:]
    X = np.array([features(r) for r in h])
    y = np.array([r["vendas"] for r in h])
    beta = np.linalg.lstsq(X, y, rcond=None)[0]
    return float(max(0.0, np.array(features(today)) @ beta))
