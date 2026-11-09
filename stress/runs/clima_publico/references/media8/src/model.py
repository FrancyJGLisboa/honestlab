"""Referência: média das últimas 8 vendas do mesmo dia da semana (variante mais suave do método atual)."""


def predict(history, day):
    same = [r["vendas"] for r in history if r["dia_semana"] == day["dia_semana"]][-8:]
    return sum(same) / len(same) if same else history[-1]["vendas"]
