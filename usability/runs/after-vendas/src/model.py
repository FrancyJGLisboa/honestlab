"""Forecast sales: least squares on weekday, holiday, temperature, rain.
Window = last WIN days; prediction shifted to the 2/3 quantile of residuals
(missing ice cream costs twice as much as leftovers)."""
WIN = 120
DAYS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]


def feats(d):
    x = [1.0 if d["dia_semana"] == k else 0.0 for k in DAYS]
    x += [float(d["feriado"]), d["temp_max_c"], d["chuva_mm"]]
    return x


def solve(A, b):
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for i in range(n):
        p = max(range(i, n), key=lambda r: abs(M[r][i]))
        M[i], M[p] = M[p], M[i]
        for r in range(n):
            if r != i:
                f = M[r][i] / M[i][i]
                for c in range(i, n + 1):
                    M[r][c] -= f * M[i][c]
    return [M[i][n] / M[i][i] for i in range(n)]


def fit(rows, lam=1.0):
    X = [feats(d) for d in rows]
    y = [d["vendas"] for d in rows]
    k = len(X[0])
    A = [[sum(x[i] * x[j] for x in X) + (lam if i == j and i >= 7 else 1e-6 if i == j else 0) for j in range(k)] for i in range(k)]
    b = [sum(x[i] * t for x, t in zip(X, y)) for i in range(k)]
    return solve(A, b)


def predict(history, today):
    rows = history[-WIN:]
    w = fit(rows)
    pr = lambda d: sum(a * b for a, b in zip(w, feats(d)))
    res = sorted(d["vendas"] - pr(d) for d in rows)
    q = res[int(len(res) * 2 / 3)]
    return max(0.0, pr(today) + q)
