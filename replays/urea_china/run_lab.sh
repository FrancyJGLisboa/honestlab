#!/bin/bash
# Step 5 end to end: a simulated market analyst asks honestlab (Claude Code plugin, Sonnet) whether China's
# October 2021 export checks raised the urea price beyond what gas explains. No data is given: the agent must
# find it. Work folder outside $HOME and outside this repository (see stress/run_public_data.sh).
cd "$(dirname "$0")"; HERE=$PWD; REPO=$(cd ../.. && pwd); U=$REPO/usability
W=$(mktemp -d -t honestlab-urea)/ureia_china; mkdir -p "$W"
TAG=${1:-lab}; echo "$W" > runs/workdir_$TAG.txt
export HONESTLAB_SIM_CLAUDE_ARGS="--setting-sources project --strict-mcp-config --model sonnet --plugin-dir $REPO"
export HONESTLAB_SIM_TURN_TIMEOUT=7200
python3 "$U/novice_sim.py" --scenario ureia_china --version-label step5 --guide "$U/guide_plugin.md" \
  --work "$W" --first "Use honestlab: {idea}." --out "$HERE/runs/$TAG.json" --max-human-turns 12 \
  > "$HERE/runs/$TAG.out" 2>&1
echo LAB_DONE
