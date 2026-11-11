#!/bin/bash
# Step 6 piece 5: a real agent (Claude Code plugin, Sonnet) coordinates a team on an approved lab built by
# make_lab.py. One message, no human turns. Usage: bash run.sh <lab folder> <tag>
cd "$(dirname "$0")"; HERE=$PWD; REPO=$(cd ../.. && pwd); LAB=$1; TAG=${2:-run1}
MSG="Use honestlab: o laboratório nesta pasta já foi aprovado e tem seis ideias em três grupos. Teste todas com um time, como o honestlab manda para várias ideias. No fim, me diga o resultado em palavras simples."
cd "$LAB" && env -u CLAUDECODE claude --setting-sources project --strict-mcp-config --model sonnet --plugin-dir "$REPO" \
  -p "$MSG" --output-format json --max-turns 250 \
  --allowedTools Bash Read Edit Write Glob Grep Skill Agent Task \
  > "$HERE/runs/$TAG.json" 2> "$HERE/runs/$TAG.err" < /dev/null
echo RUN_DONE
