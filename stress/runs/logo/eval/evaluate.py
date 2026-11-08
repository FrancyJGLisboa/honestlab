"""Evaluator for this honestlab project.

Contract (honestlab relies on it):
  * called as:  python eval/evaluate.py --split dev|holdout
  * reads ONLY the data of that split (data/dev or data/holdout)
  * validates the solution in src/ strictly; exit non-zero on invalid output
  * prints, as the LAST line of stdout, a JSON object containing the metric
    key named in lab.json, e.g. {"score": 0.42}
  * strongly recommended: also print "per_unit", the per-instance scores whose
    mean is the metric, e.g. {"score": 0.42, "per_unit": [0.4, 0.5, 0.36]}.
    honestlab then decides keep/discard and findings with a paired bootstrap
    instead of a bare point estimate
  * if the evaluation is random (training, sampling), seed it from the
    HONESTLAB_SEED environment variable and set "repeats" in lab.json

The honestlab skill writes the real evaluator with you.
"""
import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--split", choices=["dev", "holdout"], default="dev")
    ap.parse_args()
    raise SystemExit("TODO: implement the evaluator (ask your agent: "Use honestlab: <idea>")")


if __name__ == "__main__":
    main()
