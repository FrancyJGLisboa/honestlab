"""Referência: 'naive sazonal' = vendas do mesmo dia da semana passada (método padrão de comparação em previsão)."""


def predict(history, day):
    same = [r["vendas"] for r in history if r["dia_semana"] == day["dia_semana"]]
    return same[-1] if same else history[-1]["vendas"]
