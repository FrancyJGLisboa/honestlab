#!/bin/bash
# Stress: a person who has sales but no weather data. Does the agent fetch public weather data correctly?
# The agent runs isolated from the tester's own settings, with honestlab loaded from this folder.
# The work folder must be outside the home folder (else Claude Code reads ~/.claude/CLAUDE.md as a parent
# project file) and outside this repository (else it is inside the plugin folder, which is write-protected).
cd "$(dirname "$0")"; S=$PWD; U=$S/../usability; R=$S/runs
N=${1:-clima_publico}   # name of the recorded run
W=$(mktemp -d -t honestlab-public)/clima_publico; mkdir -p "$W"
cp fixtures/vendas_sp.csv "$W/vendas.csv"
export HONESTLAB_SIM_CLAUDE_ARGS="--setting-sources project --strict-mcp-config --plugin-dir $(cd "$S/.." && pwd)"
python3 "$U/novice_sim.py" --scenario clima_publico --version-label stress --guide "$U/guide_plugin.md" \
  --work "$W" --first "Use honestlab: {idea}. As vendas estão em vendas.csv nesta pasta." \
  --out "$R/$N.json" --max-human-turns 12 > "$R/$N.out" 2>&1
rm -rf "$R/$N"; cp -R "$W" "$R/$N"; rm -rf "$R/$N/.git" "$R/$N/.venv"
echo PUBLIC_DATA_DONE
