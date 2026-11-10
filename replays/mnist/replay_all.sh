#!/bin/bash
cd "$(dirname "$0")"; mkdir -p runs
run() { f=runs/$1_$2_$3.json; [ -f $f ] || .venv/bin/python replay_run.py $1 $2 $3 $f > runs/$1_$2_$3.log 2>&1; tail -1 runs/$1_$2_$3.log; }
for s in 0 1 2 3 4; do run b3d24d4 as_is $s; run 5769834 as_is $s; run 8baab10 as_is $s; done
for s in 0 1; do run 5769834 no_cosine $s; done
for s in 0 1 2 3 4; do run 8baab10 no_softmax $s; done
echo REPLAY_DONE
