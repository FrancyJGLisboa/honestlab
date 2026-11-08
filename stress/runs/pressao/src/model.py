"""Starting point = what the person does today: mean sales of the same weekday."""


def predict(history, future):
    sums, cnt = {}, {}
    for r in history:
        d = r["dia_semana"]
        sums[d] = sums.get(d, 0) + r["vendas"]
        cnt[d] = cnt.get(d, 0) + 1
    overall = sum(r["vendas"] for r in history) / len(history)
    return [sums[f["dia_semana"]] / cnt[f["dia_semana"]] if f["dia_semana"] in cnt else overall for f in future]
