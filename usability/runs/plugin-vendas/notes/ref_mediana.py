def predict(history, today):
    same = [r["vendas"] for r in history if r["dia_semana"] == today["dia_semana"]][-4:]
    if not same:
        same = [r["vendas"] for r in history]
    same = sorted(same)
    if not same:
        return 0.0
    n = len(same)
    return same[n // 2] if n % 2 else (same[n // 2 - 1] + same[n // 2]) / 2
