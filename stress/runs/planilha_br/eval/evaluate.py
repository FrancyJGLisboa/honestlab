"""Evaluator: erro médio absoluto (minutos) da previsão do tempo de entrega.

--split dev:   treina com pedidos de 2024 e testa em jan-jun/2025 (tudo da pasta dev).
--split <pasta guardada em lab.json>: treina com toda a pasta dev e testa
               nos pedidos guardados para a prova final (jul-dez/2025).
src/model.py precisa ter fit(train_rows) -> modelo e predict(modelo, rows) -> lista de minutos.
O modelo nunca vê o tempo real dos pedidos de teste, e nunca vê o número do pedido.
"""
import argparse, csv, glob, json, math, os, random, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FEATS = ["data", "hora", "distancia_km", "chuva_mm"]
with open(os.path.join(ROOT, "lab.json")) as _f:
    SEALED = os.path.basename(json.load(_f)["holdout_dir"].rstrip("/"))


def load(folder):
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "data", folder, "*.csv"))):
        with open(f, newline="") as fh:
            for r in csv.DictReader(fh):
                rows.append({"data": r["data"], "hora": int(r["hora"]),
                             "distancia_km": float(r["distancia_km"]),
                             "chuva_mm": float(r["chuva_mm"]),
                             "tempo_entrega_min": float(r["tempo_entrega_min"])})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", SEALED], default="dev")
    a = ap.parse_args()
    random.seed(int(os.environ.get("HONESTLAB_SEED", "0")))
    if a.split == "dev":
        rows = load("dev")
        train = [r for r in rows if r["data"] < "2025-01-01"]
        test = [r for r in rows if r["data"] >= "2025-01-01"]
    else:
        train, test = load("dev"), load(SEALED)
    if len(test) < 30 or len(train) < 100:
        sys.exit("dados insuficientes")
    sys.path.insert(0, os.path.join(ROOT, "src"))
    import model as m
    mdl = m.fit([dict(r) for r in train])
    feats = [{k: r[k] for k in FEATS} for r in test]
    pred = m.predict(mdl, feats)
    if not isinstance(pred, (list, tuple)) or len(pred) != len(test):
        sys.exit("predict deve devolver uma lista com um valor por pedido")
    errs = []
    for p, r in zip(pred, test):
        p = float(p)
        if not math.isfinite(p) or p < 0 or p > 300:
            sys.exit("previsão inválida (precisa ser de 0 a 300 minutos)")
        errs.append(abs(p - r["tempo_entrega_min"]))
    print(json.dumps({"score": sum(errs) / len(errs), "per_unit": errs}))


if __name__ == "__main__":
    main()
