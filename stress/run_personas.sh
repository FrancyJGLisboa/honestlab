#!/bin/bash
# Stress: six hard simulated people, honestlab Claude Code plugin only.
cd "$(dirname "$0")"; S=$PWD; U=$S/../usability; R=$S/runs; mkdir -p "$R"
prep() { rm -rf "$R/$1"; mkdir -p "$R/$1"; shift; for f in "$@"; do cp "$f" "$R/$(basename "$(dirname "$R/x")")" 2>/dev/null; done; }
for n in ruido logo planilha_br english impaciente pressao; do rm -rf "$R/$n"; mkdir -p "$R/$n"; done
cp fixtures/campanha.csv "$R/ruido/"; cp fixtures/campanha.csv "$R/pressao/"
cp fixtures/entregas.csv "$R/planilha_br/"; cp fixtures/tickets.csv "$R/english/"
cp "$U/fixtures/vendas.csv" "$R/impaciente/"
echo "Ideias de logotipo: um croissant dourado ou um trigo azul." > "$R/logo/notas.txt"
run() { python3 "$U/novice_sim.py" --scenario "$1" --version-label stress --guide "$U/$2" --work "$R/$1" \
          --first "$3" --out "$R/$1.json" --max-human-turns 12 > "$R/$1.out" 2>&1; }
run ruido guide_plugin.md "Use honestlab: {idea}. Os dados estão em campanha.csv nesta pasta." &
run logo guide_plugin.md "Use honestlab: {idea}" &
run planilha_br guide_plugin.md "Use honestlab: {idea}. A planilha é entregas.csv." &
run english guide_plugin_en.md "Use honestlab: {idea}. The data is in tickets.csv." &
run impaciente guide_plugin.md "Use honestlab: {idea}. Os dados estão em vendas.csv." &
run pressao guide_plugin.md "Use honestlab: {idea}. Os dados estão em campanha.csv." &
wait
echo PERSONAS_DONE
