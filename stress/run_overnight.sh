#!/bin/bash
# Stress: a person asks for the character model example and leaves it training alone for 40 minutes.
# Does overnight mode keep a real Claude Code agent experimenting until the time is up?
# Same isolation as run_public_data.sh: work folder outside $HOME and outside this repository.
cd "$(dirname "$0")"; S=$PWD; U=$S/../usability; R=$S/runs
N=${1:-modelo_noite}
W=$(mktemp -d -t honestlab-night)/modelo_noite; mkdir -p "$W"
export HONESTLAB_SIM_CLAUDE_ARGS="--setting-sources project --strict-mcp-config --plugin-dir $(cd "$S/.." && pwd)"
export HONESTLAB_SIM_TURN_TIMEOUT=5400
python3 "$U/novice_sim.py" --scenario modelo_noite --version-label stress --guide "$U/guide_plugin.md" \
  --work "$W" --first "Use honestlab: {idea}." \
  --out "$R/$N.json" --max-human-turns 10 > "$R/$N.out" 2>&1
rm -rf "$R/$N"; cp -R "$W" "$R/$N"; rm -rf "$R/$N/.git" "$R/$N/.venv"
echo OVERNIGHT_DONE
