#!/bin/bash
cd "$(dirname "$0")"; U=$PWD/../usability; R=$PWD/runs
for n in planilha_br english impaciente; do rm -rf "$R/$n" "$R/$n.json"; mkdir -p "$R/$n"; done
cp fixtures/entregas.csv "$R/planilha_br/"; cp fixtures/tickets.csv "$R/english/"; cp "$U/fixtures/vendas.csv" "$R/impaciente/"
run() { python3 "$U/novice_sim.py" --scenario "$1" --version-label stress --guide "$U/$2" --work "$R/$1" --first "$3" --out "$R/$1.json" --max-human-turns 12 > "$R/$1.out" 2>&1; }
run planilha_br guide_plugin.md "Use honestlab: {idea}. A planilha é entregas.csv." &
run english guide_plugin_en.md "Use honestlab: {idea}. The data is in tickets.csv." &
run impaciente guide_plugin.md "Use honestlab: {idea}. Os dados estão em vendas.csv." &
wait; echo RERUN_DONE
