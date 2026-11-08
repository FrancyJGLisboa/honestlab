"""Previsão de vendas do dia seguinte.

predict(history, today) -> número (vendas previstas, em unidades)
"""

WINDOW = 120
RIDGE = 1.0


def _x(r):
    return [1.0, r["temp_max_c"], r["chuva_mm"], float(r["feriado"]),
            1.0 if r["dia_semana"] in ("sab", "dom") else 0.0]


def _solve(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for c in range(n):
        p = max(range(c, n), key=lambda i: abs(M[i][c]))
        M[c], M[p] = M[p], M[c]
        if abs(M[c][c]) < 1e-12:
            continue
        for i in range(n):
            if i != c:
                f = M[i][c] / M[c][c]
                for j in range(c, n + 1):
                    M[i][j] -= f * M[c][j]
    return [M[i][n] / M[i][i] if abs(M[i][i]) > 1e-12 else 0.0 for i in range(n)]


def predict(history, today):
    h = history[-WINDOW:]
    if len(h) < 14:
        v = [r["vendas"] for r in history]
        return sum(v) / len(v) if v else 0.0
    X = [_x(r) for r in h]
    y = [r["vendas"] for r in h]
    k = len(X[0])
    A = [[sum(x[i] * x[j] for x in X) + (RIDGE if i == j and i > 0 else 0.0) for j in range(k)] for i in range(k)]
    b = [sum(x[i] * yy for x, yy in zip(X, y)) for i in range(k)]
    w = _solve(A, b)
    p = sum(wi * xi for wi, xi in zip(w, _x(today)))
    return max(0.0, p)
