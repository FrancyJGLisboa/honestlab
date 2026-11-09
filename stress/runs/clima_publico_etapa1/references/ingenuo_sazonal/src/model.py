"""Seasonal naive: sales of the same weekday one week earlier (standard benchmark)."""


def predict(history, target):
    same = [h["vendas"] for h in history if h["dia_semana"] == target["dia_semana"]]
    return float(same[-1]) if same else float(history[-1]["vendas"])
