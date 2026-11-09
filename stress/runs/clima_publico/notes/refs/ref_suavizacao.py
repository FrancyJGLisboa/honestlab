"""Referência: suavização exponencial com perfil do dia da semana e ajuste de feriado
(família Holt-Winters, sem tempo). Nível = média ponderada recente das vendas
dessazonalizadas; previsão = nível x fator do dia da semana (x fator de feriado)."""

ALPHA = 0.1


def predict(history, day):
    wd = {}
    for r in history[-84:]:
        if not r["feriado"]:
            wd.setdefault(r["dia_semana"], []).append(r["vendas"])
    overall = sum(sum(v) for v in wd.values()) / sum(len(v) for v in wd.values())
    factor = {k: (sum(v) / len(v)) / overall for k, v in wd.items()}
    hol = [r["vendas"] / (overall * factor.get(r["dia_semana"], 1)) for r in history if r["feriado"]]
    hol_f = sum(hol) / len(hol) if hol else 1.0
    level = None
    for r in history:
        x = r["vendas"] / factor.get(r["dia_semana"], 1) / (hol_f if r["feriado"] else 1)
        level = x if level is None else ALPHA * x + (1 - ALPHA) * level
    p = level * factor.get(day["dia_semana"], 1)
    return p * hol_f if day["feriado"] else p
