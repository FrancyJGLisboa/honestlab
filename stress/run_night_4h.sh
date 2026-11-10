#!/bin/bash
# Stress: a person asks for the character model example and leaves it training alone for 4 hours while they sleep.
# Does overnight mode keep a real Claude Code agent experimenting until the time is up?
# Same isolation as run_public_data.sh: work folder outside $HOME and outside this repository.
cd "$(dirname "$0")"; S=$PWD; U=$S/../usability; R=$S/runs
N=${1:-noite_4h}
W=$(mktemp -d -t honestlab-night)/noite_4h; mkdir -p "$W"
export HONESTLAB_SIM_CLAUDE_ARGS="--setting-sources project --strict-mcp-config --model sonnet --plugin-dir $(cd "$S/.." && pwd)"
export HONESTLAB_SIM_TURN_TIMEOUT=18000
caffeinate -i -s python3 "$U/novice_sim.py" --scenario noite_4h --version-label stress --guide "$U/guide_plugin.md" \
  --work "$W" --first "Use honestlab: {idea}." \
  --out "$R/$N.json" --max-human-turns 10 > "$R/$N.out" 2>&1
rm -rf "$R/$N"; cp -R "$W" "$R/$N"; rm -rf "$R/$N/.git" "$R/$N/.venv"
echo OVERNIGHT_DONE
