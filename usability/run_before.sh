#!/bin/bash
export PATH=/home/claude/lb032/bin:$PATH
cd /home/claude/honestlab/usability
python3 novice_sim.py --scenario vendas --version-label before --guide guide_before.md --work /home/claude/honestlab/usability/runs/before-vendas   --pre "honestlab init ." --first "Use the honestlab-frame skill. My idea: {idea}. Os dados estão no arquivo vendas.csv desta pasta." --out /home/claude/honestlab/usability/runs/before-vendas.json &
python3 novice_sim.py --scenario cropcast --version-label before --guide guide_before.md --work /home/claude/honestlab/usability/runs/before-cropcast   --pre "honestlab init --here" --first "Use the honestlab-scout skill." --out /home/claude/honestlab/usability/runs/before-cropcast.json &
wait
echo BEFORE_DONE
