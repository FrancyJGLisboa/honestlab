"""Referência: média do mesmo dia da semana nas últimas 4 semanas."""


def predict(historico, amanha):
    mesmos = [d["vendas"] for d in historico if d["dia_semana"] == amanha["dia_semana"]][-4:]
    return sum(mesmos) / len(mesmos)
