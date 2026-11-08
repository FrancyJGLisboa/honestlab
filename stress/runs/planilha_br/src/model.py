"""Regressão linear por mínimos quadrados com hora (uma coluna por hora), distância e chuva
(linear e 'choveu ou não'). Sem bibliotecas."""

HOURS = list(range(10, 23))


def feats(r):
    h = r["hora"]
    return ([1.0, r["distancia_km"], r["chuva_mm"], 1.0 if r["chuva_mm"] > 0 else 0.0]
            + [1.0 if h == k else 0.0 for k in HOURS[1:]])


def solve(A, b):
    n = len(b)
    M = [row[:] + [bi] for row, bi in zip(A, b)]
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(M[k][i]))
        M[i], M[p] = M[p], M[i]
        piv = M[i][i] or 1e-9
        for k in range(i + 1, n):
            f = M[k][i] / piv
            for j in range(i, n + 1):
                M[k][j] -= f * M[i][j]
    x = [0.0] * n
    for i in range(n - 1, -1, -1):
        x[i] = (M[i][n] - sum(M[i][j] * x[j] for j in range(i + 1, n))) / (M[i][i] or 1e-9)
    return x


def fit(train):
    X = [feats(r) for r in train]
    y = [r["tempo_entrega_min"] for r in train]
    n = len(X[0])
    A = [[sum(x[i] * x[j] for x in X) + (1e-6 if i == j else 0) for j in range(n)] for i in range(n)]
    b = [sum(x[i] * yi for x, yi in zip(X, y)) for i in range(n)]
    return solve(A, b)


def predict(w, rows):
    return [min(300.0, max(1.0, sum(a * b for a, b in zip(w, feats(r))))) for r in rows]
