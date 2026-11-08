"""Suavização exponencial simples por dia da semana (alfa 0.15)."""


def predict(history, today):
    level = None
    for r in history:
        if r["dia_semana"] == today["dia_semana"]:
            level = r["vendas"] if level is None else level + 0.15 * (r["vendas"] - level)
    return level
