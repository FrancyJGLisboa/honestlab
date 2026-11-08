def predict(history, today):
    """Same weekday, last 8 weeks, median; no weather (strong no-weather method)."""
    same = sorted(d["vendas"] for d in history if d["dia_semana"] == today["dia_semana"])
    same = sorted([d["vendas"] for d in history if d["dia_semana"] == today["dia_semana"]][-8:])
    n = len(same)
    return same[n // 2] if n % 2 else (same[n // 2 - 1] + same[n // 2]) / 2
