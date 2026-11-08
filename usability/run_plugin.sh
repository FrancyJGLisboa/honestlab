#!/bin/bash
# 0.5 usability run: the honestlab Claude Code plugin is installed; nothing else is.
set -e
cd "$(dirname "$0")"; R=$PWD/runs
rm -rf "$R/plugin-vendas" "$R/plugin-cropcast"; mkdir -p "$R/plugin-vendas"
cp fixtures/vendas.csv "$R/plugin-vendas/"
bash fixtures/make_cropcast.sh "$R/plugin-cropcast" >/dev/null
python3 novice_sim.py --scenario vendas --version-label plugin --guide guide_plugin.md --work "$R/plugin-vendas" \
  --first "Use honestlab: {idea}. Os dados estão no arquivo vendas.csv desta pasta." --out "$R/plugin-vendas.json" &
python3 novice_sim.py --scenario cropcast --version-label plugin --guide guide_plugin.md --work "$R/plugin-cropcast" \
  --first "Use honestlab: {idea}" --out "$R/plugin-cropcast.json" &
wait
echo PLUGIN_DONE
