"""Referência: média dos últimos 7 dias."""


def predict(historico, amanha):
    u = [d["vendas"] for d in historico[-7:]]
    return sum(u) / len(u)
