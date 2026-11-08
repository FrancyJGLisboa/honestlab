def predict(history, today):
    v = [r["vendas"] for r in history][-28:]
    return sum(v) / len(v) if v else 0.0
