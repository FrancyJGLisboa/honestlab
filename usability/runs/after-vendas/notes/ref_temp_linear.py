def predict(history, today):
    """Plain weather method: weekday level (last 8 same days) + slope on temperature
    fitted over the last 90 days by least squares on residuals from weekday means."""
    h = history[-90:]
    by = {}
    for d in history:
        by.setdefault(d["dia_semana"], []).append(d["vendas"])
    lvl = {k: sum(v[-8:]) / len(v[-8:]) for k, v in by.items()}
    xs = [d["temp_max_c"] for d in h]
    ys = [d["vendas"] - lvl[d["dia_semana"]] for d in h]
    mx, my = sum(xs) / len(xs), sum(ys) / len(ys)
    vx = sum((x - mx) ** 2 for x in xs) or 1.0
    b = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / vx
    return max(0.0, lvl[today["dia_semana"]] + b * (today["temp_max_c"] - mx))
