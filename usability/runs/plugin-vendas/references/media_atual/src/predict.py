def predict(history, today):
    same = [r["vendas"] for r in history if r["dia_semana"] == today["dia_semana"]][-4:]
    if not same:
        same = [r["vendas"] for r in history]
    return sum(same) / len(same) if same else 0.0
