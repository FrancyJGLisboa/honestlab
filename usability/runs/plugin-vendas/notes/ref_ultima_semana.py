def predict(history, today):
    same = [r["vendas"] for r in history if r["dia_semana"] == today["dia_semana"]]
    if same:
        return same[-1]
    return history[-1]["vendas"] if history else 0.0
