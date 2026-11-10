"""One training run of a MLP_AutoResearch config, with a fixed seed. Saves test accuracy and per-image correctness.
python replay_run.py <commit> <variant: as_is|no_cosine|no_softmax> <seed> <out.json>"""
import json, random, runpy, subprocess, sys, tempfile, os
from pathlib import Path
commit, variant, seed, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), os.path.abspath(sys.argv[4])
repo = Path(__file__).resolve().parent / "MLP_AutoResearch"  # git clone https://github.com/HuangShengZeBlueSky/MLP_AutoResearch
src = subprocess.run(["git", "-C", str(repo), "show", f"{commit}:train.py"], capture_output=True, text=True, check=True).stdout
if variant == "no_cosine":
    assert "LR_SCHEDULE = 'cosine'" in src; src = src.replace("LR_SCHEDULE = 'cosine'", "LR_SCHEDULE = 'none'")
elif variant == "no_softmax":
    assert "logits = self.classify(self.mlp(X))" in src; src = src.replace("logits = self.classify(self.mlp(X))", "logits = self.mlp(X)")
tmp = Path(tempfile.mkdtemp()) / "train.py"; tmp.write_text(src)
os.chdir(repo); sys.path.insert(0, str(repo))
import numpy as np, torch
random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
g = runpy.run_path(str(tmp), run_name="__main__")
model = g["model"]; model.eval()
from prepare import load_data
_, test_loader = load_data()
correct = []
with torch.no_grad():
    for X, y in test_loader:
        correct += (model(X).argmax(1) == y).int().tolist()
json.dump({"commit": commit, "variant": variant, "seed": seed, "test_accuracy": sum(correct) / len(correct),
           "reported_final": g.get("results", {}).get("final_test_accuracy"), "correct": correct}, open(out, "w"))
print(commit, variant, seed, sum(correct) / len(correct), flush=True)
