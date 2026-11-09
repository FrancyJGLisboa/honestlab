#!/bin/bash
# Live check of remeasure_best on the charlm example (10-second training budget).
set -u
S=$SCRATCH
R=$REPO
export PATH=$S/pipbin:$PATH
W=$S/drift_live; rm -rf $W; mkdir -p $W
load_on() { for i in 1 2 3 4 5 6 7 8; do yes > /dev/null & done; }
load_off() { pkill -f "^yes$" ; sleep 3; }
for n in plain again; do
  cd $W && honestlab init $n --example charlm > /dev/null && cd $n
  sed -i '' 's/^BUDGET_SEC = 60.0/BUDGET_SEC = 10.0/' eval/evaluate.py
  python3 - "$n" <<'PY'
import json,sys; c=json.load(open("lab.json")); c["remeasure_best"]= sys.argv[1]=="again"; json.dump(c,open("lab.json","w"),indent=2)
PY
  git add -A >/dev/null; git commit -qm "10 s budget" >/dev/null
done
echo "== baselines while the computer is busy (8 busy processes)"
load_on
for n in plain again; do (cd $W/$n && honestlab baseline | grep -i "baseline\|refer" | head -3); done
load_off
for n in plain again; do
  (cd $W/$n && env -u CLAUDECODE python3 $R/tests/tty_run.py "$PWD" $n honestlab freeze | grep -o "Frozen")
done
echo "== the same model, computer idle"
for n in plain again; do
  cd $W/$n && echo "# unchanged model, comment only" >> src/model.py
  echo "-- $n (remeasure_best $( [ $n = again ] && echo true || echo false ))"
  honestlab run -m "unchanged model, only a comment added to the code" | grep -E "KEEP|DISCARD|ERROR"
done
