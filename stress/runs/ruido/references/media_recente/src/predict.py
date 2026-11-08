"""Média das últimas 8 ocorrências do mesmo dia da semana."""


def predict(history, today):
    same = [r["vendas"] for r in history if r["dia_semana"] == today["dia_semana"]][-8:]
    return sum(same) / len(same)
