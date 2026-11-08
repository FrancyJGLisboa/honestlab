#!/bin/bash
export PATH=/root/.local/bin:$PATH
cd /home/claude/honestlab/usability
python3 novice_sim.py --scenario vendas --version-label after --guide guide_after.md --work /home/claude/honestlab/usability/runs/after-vendas   --first "Use honestlab: {idea}. Os dados estão no arquivo vendas.csv desta pasta." --out /home/claude/honestlab/usability/runs/after-vendas.json &
python3 novice_sim.py --scenario cropcast --version-label after --guide guide_after.md --work /home/claude/honestlab/usability/runs/after-cropcast   --first "Use honestlab: {idea}" --out /home/claude/honestlab/usability/runs/after-cropcast.json &
wait
echo AFTER_DONE
