"""Modelo do preco 'normal' da ureia: o que ela custaria sem o evento, dado o gas.

predict_normal(train, gas_future) -> lista de log(preco normal) para cada mes futuro.
  train: linhas ANTES da data do evento, cada uma {"urea","gas_eu","gas_us"} (precos em US$).
  gas_future: gas dos meses da janela (o gas realizado e a explicacao permitida).
O preco real da ureia na janela nunca chega aqui.
"""
import math


def _ols(X, y):
    n = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) for j in range(n)] for i in range(n)]
    b = [sum(r[i] * yy for r, yy in zip(X, y)) for i in range(n)]
    for i in range(n):
        A[i][i] += 1e-9
    for i in range(n):
        p = max(range(i, n), key=lambda k: abs(A[k][i]))
        A[i], A[p] = A[p], A[i]
        b[i], b[p] = b[p], b[i]
        for k in range(i + 1, n):
            f = A[k][i] / A[i][i]
            for j in range(i, n):
                A[k][j] -= f * A[i][j]
            b[k] -= f * b[i]
    w = [0.0] * n
    for i in reversed(range(n)):
        w[i] = (b[i] - sum(A[i][j] * w[j] for j in range(i + 1, n))) / A[i][i]
    return w


def predict_normal(train, gas_future):
    lu = [math.log(r["urea"]) for r in train]
    le = [math.log(r["gas_eu"]) for r in train]
    ls = [math.log(r["gas_us"]) for r in train]
    X = [[1.0, lu[t - 1], le[t], ls[t]] for t in range(1, len(train))]
    w = _ols(X, lu[1:])
    prev, out = lu[-1], []
    for g in gas_future:
        prev = w[0] + w[1] * prev + w[2] * math.log(g["gas_eu"]) + w[3] * math.log(g["gas_us"])
        out.append(prev)
    return out
