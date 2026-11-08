"""Previsão de vendas de amanhã: regressão ridge em janela móvel (só biblioteca padrão)."""

DIAS = ["seg", "ter", "qua", "qui", "sex", "sab", "dom"]
JANELA = 90
LAMBDA = 1.0


def _feat(d):
    x = [1.0, d["temp_max_c"], d["chuva_mm"], float(d["feriado"])]
    x += [1.0 if d["dia_semana"] == k else 0.0 for k in DIAS[1:]]
    return x


def _resolver(A, b):
    n = len(b)
    M = [A[i][:] + [b[i]] for i in range(n)]
    for c in range(n):
        p = max(range(c, n), key=lambda r: abs(M[r][c]))
        M[c], M[p] = M[p], M[c]
        for r in range(c + 1, n):
            f = M[r][c] / M[c][c]
            for k in range(c, n + 1):
                M[r][k] -= f * M[c][k]
    w = [0.0] * n
    for i in range(n - 1, -1, -1):
        w[i] = (M[i][n] - sum(M[i][k] * w[k] for k in range(i + 1, n))) / M[i][i]
    return w


def predict(historico, amanha):
    h = historico[-JANELA:]
    X = [_feat(d) for d in h]
    y = [d["vendas"] for d in h]
    n = len(X[0])
    A = [[sum(r[i] * r[j] for r in X) + (LAMBDA if i == j and i > 0 else 0.0) for j in range(n)] for i in range(n)]
    b = [sum(r[i] * t for r, t in zip(X, y)) for i in range(n)]
    w = _resolver(A, b)
    p = sum(a * c for a, c in zip(w, _feat(amanha)))
    return max(0.0, p)
