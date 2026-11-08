def predict(history, future):
    m = sum(r["vendas"] for r in history) / len(history)
    return [m for _ in future]
