def predict(history, today):
    """Average of the last 8 same weekdays (no weather)."""
    v = [h["vendas"] for h in history if h["dia_semana"] == today["dia_semana"]][-8:]
    return sum(v) / len(v)
