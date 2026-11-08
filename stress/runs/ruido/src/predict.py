"""Média separada para dias úteis (seg-sex) e fim de semana (sáb-dom)."""
def predict(history, today):
    wk = lambda d: d >= 5
    v = [r["vendas"] for r in history if wk(r["dia_semana"]) == wk(today["dia_semana"])]
    return sum(v) / len(v)
