def predict(history, today):
    v = [d["vendas"] for d in history][-28:]
    return sum(v) / len(v)
