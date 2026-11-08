"""Referência: média dos últimos 28 dias."""


def predict(historico, amanha):
    u = [d["vendas"] for d in historico[-28:]]
    return sum(u) / len(u)
