"""Baixa a previsão do tempo feita NA VÉSPERA para cada dia de vendas e junta à planilha.

Fonte: Open-Meteo "Previous Runs API" (https://open-meteo.com/en/docs/previous-runs-api),
modelo GFS (NOAA). A variável *_previous_day1 é o valor que o modelo previa ~24 h antes,
ou seja, o que se sabia na véspera. Local: Pinheiros, São Paulo (-23.5629, -46.6919).

Uso:  python3 notes/fetch_weather.py vendas.csv notes/tmp
Escreve dois arquivos em notes/tmp: dev.csv (2024) e final.csv (2025, guardado para a
prova final; o script não imprime nada dele). Depois cada um entra com `honestlab data add`.
"""
import csv
import json
import os
import sys
import urllib.request

LAT, LON = -23.5629, -46.6919
MODEL = "gfs_seamless"
URL = (
    "https://previous-runs-api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
    "&hourly=temperature_2m_previous_day1,precipitation_previous_day1"
    "&start_date={start}&end_date={end}&timezone=America/Sao_Paulo&models={model}"
)
OPEN_HOURS = range(11, 22)  # horário típico de sorveteria: 11h às 21h
EMPTY = {"prev_tmax": "", "prev_tmedia": "", "prev_chuva_mm": "", "prev_horas_chuva_aberto": ""}


def fetch(start, end):
    url = URL.format(lat=LAT, lon=LON, start=start, end=end, model=MODEL)
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)["hourly"]


def daily(h):
    out = {}
    for t, temp, rain in zip(h["time"], h["temperature_2m_previous_day1"], h["precipitation_previous_day1"]):
        d, hour = t[:10], int(t[11:13])
        o = out.setdefault(d, {"temps": [], "rains": [], "open_rain_h": 0})
        if temp is None or rain is None:
            continue
        o["temps"].append(temp)
        o["rains"].append(rain)
        if hour in OPEN_HOURS and rain >= 0.1:
            o["open_rain_h"] += 1
    res = {}
    for d, o in out.items():
        if len(o["temps"]) < 24:  # previsão incompleta para o dia: deixa vazio
            res[d] = dict(EMPTY)
        else:
            res[d] = {
                "prev_tmax": round(max(o["temps"]), 1),
                "prev_tmedia": round(sum(o["temps"]) / len(o["temps"]), 1),
                "prev_chuva_mm": round(sum(o["rains"]), 1),
                "prev_horas_chuva_aberto": o["open_rain_h"],
            }
    return res


def main():
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    with open(src, newline="") as f:
        rows = list(csv.DictReader(f))
    dates = [r["data"] for r in rows]
    w = daily(fetch(min(dates), max(dates)))
    cols = ["data", "dia_semana", "feriado", "vendas"] + list(EMPTY)
    names = {"dev": "dev.csv", "final": "final.csv"}
    files = {k: open(os.path.join(outdir, v), "w", newline="") for k, v in names.items()}
    writers = {k: csv.DictWriter(v, fieldnames=cols) for k, v in files.items()}
    for wr in writers.values():
        wr.writeheader()
    n_dev = n_missing_dev = 0
    for r in rows:
        part = "dev" if r["data"] < "2025-01-01" else "final"
        wx = w.get(r["data"], dict(EMPTY))
        writers[part].writerow({**r, **wx})
        if part == "dev":
            n_dev += 1
            n_missing_dev += wx["prev_tmax"] == ""
    for f in files.values():
        f.close()
    print(f"dev: {n_dev} dias, {n_missing_dev} sem previsão; parte final escrita sem inspeção")


if __name__ == "__main__":
    main()
