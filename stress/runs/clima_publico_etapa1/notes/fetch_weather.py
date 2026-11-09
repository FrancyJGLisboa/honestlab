"""Download public weather for Pinheiros (Sao Paulo) and build dev/holdout files.

Usage: python3 -I notes/fetch_weather.py vendas.csv notes/staging

Sources (Open-Meteo, https://open-meteo.com, data CC BY 4.0):
  * Day-ahead forecast ("previous runs" API, variables *_previous_day1): the value the
    weather models predicted about 24 hours before each hour. This is what a shop owner
    could have known the night before. Used for the TARGET day.
  * Observed weather (archive API, ERA5 reanalysis): what actually happened. Only given
    for days BEFORE the target day (history), never for the target day itself.

Split by time: dev = 2024-01-01 .. 2025-06-30; holdout = 2025-07-01 .. 2025-12-31.
The holdout file also contains all earlier days as history (avaliar=0), so models can
look back; only rows with avaliar=1 are scored. The script never prints holdout data.
"""
import csv
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

LAT, LON = -23.566, -46.692  # Pinheiros, Sao Paulo
TZ = "America%2FSao_Paulo"
START, END = "2024-01-01", "2025-12-31"
HOLDOUT_START = "2025-07-01"
DEV_SCORE_START = "2024-03-01"  # first 2 months only serve as history
OPEN_HOURS = range(10, 23)  # 10h-22h, roughly when an ice-cream shop sells


def get(url):
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.load(r)


def daily_from_hourly(hourly, tkey, pkey):
    temps, rain, rain_open = defaultdict(list), defaultdict(float), defaultdict(float)
    for t, temp, p in zip(hourly["time"], hourly[tkey], hourly[pkey]):
        day, hour = t[:10], int(t[11:13])
        if temp is None or p is None:
            if day >= DEV_SCORE_START:
                raise SystemExit(f"missing forecast value at {t}")
            continue  # archive starts 2024-01-19; early days are history only
        temps[day].append(temp)
        rain[day] += p
        if hour in OPEN_HOURS:
            rain_open[day] += p
    out = {}
    for day, ts in temps.items():
        if len(ts) != 24:
            if day >= DEV_SCORE_START:
                raise SystemExit(f"incomplete forecast day {day}")
            continue
        out[day] = {
            "prev_tmax": round(max(ts), 1),
            "prev_tmed": round(sum(ts) / 24, 1),
            "prev_chuva": round(rain[day], 1),
            "prev_chuva_aberto": round(rain_open[day], 1),
        }
    return out


def main():
    sales_path, outdir = Path(sys.argv[1]), Path(sys.argv[2])
    outdir.mkdir(parents=True, exist_ok=True)

    fc = get(
        "https://previous-runs-api.open-meteo.com/v1/forecast"
        f"?latitude={LAT}&longitude={LON}&start_date={START}&end_date={END}"
        "&hourly=temperature_2m_previous_day1,precipitation_previous_day1"
        f"&timezone={TZ}"
    )
    prev = daily_from_hourly(
        fc["hourly"], "temperature_2m_previous_day1", "precipitation_previous_day1"
    )
    ob = get(
        "https://archive-api.open-meteo.com/v1/archive"
        f"?latitude={LAT}&longitude={LON}&start_date={START}&end_date={END}"
        "&daily=temperature_2m_max,temperature_2m_mean,precipitation_sum"
        f"&timezone={TZ}"
    )
    d = ob["daily"]
    obs = {}
    for i, day in enumerate(d["time"]):
        vals = (d["temperature_2m_max"][i], d["temperature_2m_mean"][i], d["precipitation_sum"][i])
        if None in vals:
            raise SystemExit(f"missing observed value at {day}")
        obs[day] = {"obs_tmax": vals[0], "obs_tmed": vals[1], "obs_chuva": vals[2]}

    rows = []
    with open(sales_path, newline="") as f:
        for r in csv.DictReader(f):
            day = r["data"]
            if day not in obs or (day not in prev and day >= DEV_SCORE_START):
                raise SystemExit(f"no weather for {day}")
            blank = dict.fromkeys(["prev_tmax", "prev_tmed", "prev_chuva", "prev_chuva_aberto"], "")
            rows.append({**r, **prev.get(day, blank), **obs[day]})
    rows.sort(key=lambda r: r["data"])
    fields = list(rows[0].keys()) + ["avaliar"]

    def write(name, selected):
        with open(outdir / name, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            w.writerows(selected)

    dev = [dict(r, avaliar=int(r["data"] >= DEV_SCORE_START)) for r in rows if r["data"] < HOLDOUT_START]
    hold = [dict(r, avaliar=int(r["data"] >= HOLDOUT_START)) for r in rows]
    write("dev.csv", dev)
    write("holdout.csv", hold)
    print(f"dev: {len(dev)} rows ({sum(r['avaliar'] for r in dev)} scored); holdout file written")


if __name__ == "__main__":
    main()
