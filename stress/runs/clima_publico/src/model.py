"""Previsão das vendas de amanhã.

Base: suavização exponencial (nível) x fator do dia da semana x fator de feriado.
Ajuste de tempo: regressão linear do log(vendas / base) sobre a previsão do tempo da
véspera, ajustada só com dias do histórico. predict(history, day) -> número.
"""
import math

ALPHA = 0.1
WINDOW = 84          # dias para fatores do dia da semana
FIT_DAYS = 365       # dias do histórico usados para ajustar o efeito do tempo
RIDGE = 1.0
FEATURES = ["prev_tmax", "prev_horas_chuva_aberto"]


def _factors(history):
    wd = {}
    for r in history[-WINDOW:]:
        if not r["feriado"]:
            wd.setdefault(r["dia_semana"], []).append(r["vendas"])
    overall = sum(sum(v) for v in wd.values()) / sum(len(v) for v in wd.values())
    factor = {k: (sum(v) / len(v)) / overall for k, v in wd.items()}
    hol = [r["vendas"] / (overall * factor.get(r["dia_semana"], 1)) for r in history if r["feriado"]]
    hol_f = sum(hol) / len(hol) if hol else 1.0
    return factor, hol_f


def _adj(r, factor, hol_f):
    return factor.get(r["dia_semana"], 1) * (hol_f if r["feriado"] else 1)


def _solve(X, y, ridge):
    k = len(X[0])
    A = [[sum(x[i] * x[j] for x in X) + (ridge if i == j and i > 0 else 0) for j in range(k)] for i in range(k)]
    b = [sum(x[i] * t for x, t in zip(X, y)) for i in range(k)]
    for c in range(k):  # Gauss-Jordan
        p = max(range(c, k), key=lambda i: abs(A[i][c]))
        A[c], A[p], b[c], b[p] = A[p], A[c], b[p], b[c]
        if abs(A[c][c]) < 1e-12:
            return [0.0] * k
        for i in range(k):
            if i != c:
                f = A[i][c] / A[c][c]
                A[i] = [a - f * ac for a, ac in zip(A[i], A[c])]
                b[i] -= f * b[c]
    return [b[i] / A[i][i] for i in range(k)]


def predict(history, day):
    factor, hol_f = _factors(history)
    level = None
    rows = []  # (dia, base prevista antes de ver o dia)
    for r in history:
        a = _adj(r, factor, hol_f)
        if level is not None:
            rows.append((r, level * a))
        x = r["vendas"] / a
        level = x if level is None else ALPHA * x + (1 - ALPHA) * level
    base = level * _adj(day, factor, hol_f)

    if any(day.get(f) is None for f in FEATURES):
        return base
    fit = [(r, b) for r, b in rows[-FIT_DAYS:]
           if b > 0 and r["vendas"] > 0 and all(r.get(f) is not None for f in FEATURES)]
    if len(fit) < 30:
        return base
    means = [sum(r[f] for r, _ in fit) / len(fit) for f in FEATURES]
    sds = [max(1e-6, (sum((r[f] - m) ** 2 for r, _ in fit) / len(fit)) ** 0.5) for f, m in zip(FEATURES, means)]
    X = [[1.0] + [(r[f] - m) / s for f, m, s in zip(FEATURES, means, sds)] for r, _ in fit]
    y = [math.log(r["vendas"] / b) for r, b in fit]
    w = _solve(X, y, RIDGE)
    x = [1.0] + [(day[f] - m) / s for f, m, s in zip(FEATURES, means, sds)]
    return base * math.exp(sum(wi * xi for wi, xi in zip(w, x)))
