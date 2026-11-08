"""Build the data files for the stress scenarios (deterministic)."""
import csv, math, random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent / "fixtures"
OUT.mkdir(exist_ok=True)
rng = random.Random(7)
days = [date(2024, 1, 1) + timedelta(d) for d in range(730)]

# noise: ad spend and clicks have NO relation to sales beyond weekday
with open(OUT / "campanha.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["data", "dia_semana", "gasto_anuncio", "cliques", "vendas"])
    for d in days:
        wd = d.weekday(); base = 120 + (25 if wd >= 5 else 0)
        gasto = round(rng.uniform(50, 400), 2); cliques = int(gasto * rng.uniform(1.5, 3.5))
        w.writerow([d.isoformat(), wd, gasto, cliques, max(0, int(rng.gauss(base, 18)))])

# Brazilian Excel export: semicolon separator, comma decimals, real signal (distance, rain, rush hour)
with open(OUT / "entregas.csv", "w", newline="", encoding="utf-8") as f:
    f.write("pedido;data;hora;distancia_km;chuva_mm;tempo_entrega_min\n")
    for i in range(4000):
        d = days[i % 730]; h = rng.randint(10, 22); dist = rng.uniform(0.5, 12); chuva = max(0, rng.gauss(0, 6))
        t = 12 + 3.1 * dist + 0.9 * chuva + (9 if h in (12, 13, 19, 20) else 0) + rng.gauss(0, 6)
        f.write(f"{i+1};{d.strftime('%d/%m/%Y')};{h};{dist:.1f}".replace(".", ",") + f";{chuva:.1f}".replace(".", ",") + f";{t:.0f}\n")

# English: daily support tickets driven by release days and weekday
with open(OUT / "tickets.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["date", "weekday", "release_day", "active_users", "tickets"])
    users = 5000
    for d in days:
        users += rng.randint(-20, 40); rel = 1 if rng.random() < 0.08 else 0; wd = d.weekday()
        lam = users / 120 * (0.55 if wd >= 5 else 1.0) * (1.9 if rel else 1.0)
        w.writerow([d.isoformat(), wd, rel, users, max(0, int(rng.gauss(lam, math.sqrt(lam) + 3)))])
print("fixtures in", OUT)
