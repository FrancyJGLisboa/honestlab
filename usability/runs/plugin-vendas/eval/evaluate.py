"""Evaluator: previsão diária de vendas, validação "andando no tempo".

Para cada dia avaliado, o código em src/predict.py recebe só os dias ANTERIORES
(com vendas) e as características do próprio dia (dia da semana, feriado, tempo),
sem as vendas dele. Métrica: erro absoluto médio (unidades/dia), menor é melhor.
Última linha: JSON {"score": mae, "per_unit": [erro por dia]}.
"""
import argparse, csv, importlib.util, json, math, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FORBIDDEN = re.compile(r"\b(open|os|sys|subprocess|pathlib|csv|glob|shutil|socket|urllib|requests|inspect|gc|importlib|__import__|eval|exec|compile|globals|locals|getattr)\b")


def load_rows(split):
    path = os.path.join(ROOT, "data", split, "vendas.csv")
    rows = []
    with open(path, newline="") as f:
        for r in csv.DictReader(f):
            rows.append({
                "data": r["data"], "dia_semana": r["dia_semana"],
                "feriado": int(r["feriado"]), "temp_max_c": float(r["temp_max_c"]),
                "chuva_mm": float(r["chuva_mm"]), "vendas": float(r["vendas"]),
                "avaliar": int(r["avaliar"]),
            })
    rows.sort(key=lambda x: x["data"])
    return rows


def check_source():
    src = os.path.join(ROOT, "src")
    for name in os.listdir(src):
        if name.endswith(".py"):
            text = open(os.path.join(src, name)).read()
            code = re.sub(r"#.*", "", re.sub(r'"""[\s\S]*?"""', "", text))
            m = FORBIDDEN.search(code)
            if m:
                sys.exit(f"INVALID: src/{name} usa '{m.group(0)}' (proibido: a solução não pode ler arquivos nem o ambiente)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    a = ap.parse_args()
    check_source()
    sys.path.insert(0, os.path.join(ROOT, "src"))
    spec = importlib.util.spec_from_file_location("predict", os.path.join(ROOT, "src", "predict.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    rows = load_rows(a.split)
    errs = []
    for i, r in enumerate(rows):
        if not r["avaliar"]:
            continue
        hist = [{k: v for k, v in h.items() if k != "avaliar"} for h in rows[:i]]
        today = {k: r[k] for k in ("data", "dia_semana", "feriado", "temp_max_c", "chuva_mm")}
        p = mod.predict(hist, today)
        if isinstance(p, bool) or not isinstance(p, (int, float)) or not math.isfinite(p) or p < 0 or p > 2000:
            sys.exit(f"INVALID: previsão inválida para {r['data']}: {p!r}")
        errs.append(abs(p - r["vendas"]))
    if len(errs) < 30:
        sys.exit("INVALID: poucos dias avaliados")
    print(json.dumps({"score": sum(errs) / len(errs), "per_unit": errs}))


if __name__ == "__main__":
    main()
