"""Explain-back checker: the part of usability/explain_back.py that needs no model.

Usage: python3 tests/explain_back_test.py
"""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "usability"))
import explain_back as eb  # noqa: E402

RUNS = REPO / "stress" / "runs"


def main():
    ok = fail = 0

    def case(name, cond):
        nonlocal ok, fail
        if cond:
            ok += 1
        else:
            fail += 1
            print("FAIL", name)

    en = eb.truth(RUNS / "english")
    case("truth: english verdict is found", en["verdict"] == "found")
    case("truth: english start and best", abs(en["start"] - 13.3088) < 1e-3 and abs(en["best"] - 9.9608) < 1e-3)
    case("truth: english held-out gain about 42%", any(abs(h - 42.2) < 0.1 for h in en["holdout_gains"]))
    case("truth: english confirmed", en["confirmed"])
    pl = eb.truth(RUNS / "planilha_br")
    case("truth: planilha_br verdict is not_found", pl["verdict"] == "not_found")
    case("truth: planilha_br known method is the strongest reference", abs(pl["known"] - 4.8456) < 1e-3)
    case("truth: planilha_br not confirmed", not pl["confirmed"])

    good = {"verdict": "found", "start_value": 13.31, "known_value": 13.31, "best_value": 9.96, "gain_percent": 25,
            "gain_vs": "known", "confirmed_on_new_data": "yes", "novelty": None, "next_step": "run it beside"}
    case("check: a correct explanation passes", eb.check(good, en)["pass"])
    case("check: the held-out 42% is accepted", eb.check(dict(good, gain_percent=42), en)["pass"])
    case("check: a wrong gain fails", not eb.check(dict(good, gain_percent=60), en)["numbers_ok"])
    case("check: held-out scores are true numbers too",
         eb.check(dict(good, best_value=11.34, known_value=19.6, gain_percent=42), en)["pass"])
    case("check: a wrong best score fails", not eb.check(dict(good, best_value=8.5), en)["numbers_ok"])
    case("check: unstated numbers do not fail", eb.check(dict(good, start_value=None, gain_percent=None), en)["pass"])
    case("check: a wrong verdict fails", not eb.check(dict(good, verdict="fragile"), en)["pass"])
    case("check: 'certainly new' is an overclaim", eb.check(dict(good, novelty="proven_new"), en)["overclaims"])
    bad = dict(good, verdict="found", start_value=11.24, known_value=None, best_value=4.85, gain_percent=57,
               confirmed_on_new_data="no")
    r = eb.check(bad, pl)
    case("check: 'found' on a not-found lab is an overclaim", not r["pass"] and r["overclaims"])
    case("check: true numbers with a wrong verdict still fail", r["numbers_ok"] and not r["verdict_ok"])
    case("check: 'confirmed' on an unconfirmed lab is an overclaim",
         eb.check(dict(good, verdict="not_found", confirmed_on_new_data="yes", gain_percent=None, best_value=4.8466,
                       start_value=None, known_value=None), pl)["overclaims"])
    case("check: a missing next step is reported", not eb.check(dict(good, next_step=None), en)["next_step_ok"])

    tsv = eb.results_tsv(RUNS / "english").splitlines()
    case("log: header and baseline row", tsv[0].startswith("commit\tscore") and tsv[1].startswith("baseline\t13.3"))
    case("log: one row per attempt", len(tsv) == 2 + 5)
    case("log: no verdict, no known method", "Found" not in "\n".join(tsv) and "reference" not in "\n".join(tsv))
    print(f"{ok} passed, {fail} failed")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
