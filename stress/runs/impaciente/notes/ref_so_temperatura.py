def predict(history, today):
    """Textbook idea: straight line of sales on max temperature, last 90 days (no weekday)."""
    h = history[-90:]
    xs = [r["temp_max_c"] for r in h]; ys = [r["vendas"] for r in h]
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx if sxx else 0.0
    return max(0.0, my + b * (today["temp_max_c"] - mx))
