#!/bin/bash
# Replay 2: the same task (autoresearch-tabular, UCI Adult Income) run by plain autoresearch and by honestlab.
# Both agents use Sonnet, up to 15 experiments, and the same goal: beat the best known approach.
# Work folders are outside $HOME and outside this repository (see stress/run_public_data.sh).
# Usage: run_pair.sh <path to a clone of github.com/saikatkumardey/autoresearch-tabular> [honestlab]
# With "honestlab" as the second argument, only the honestlab run happens (recorded as honestlab_after_fix,
# or as the third argument).
cd "$(dirname "$0")"; HERE=$PWD; REPO=$(cd ../.. && pwd); U=$REPO/usability; SRC=$1; ONLY=${2:-}; TAG=honestlab; [ "$ONLY" = honestlab ] && TAG=${3:-honestlab_after_fix}
BASE=$(mktemp -d -t honestlab-adult); mkdir -p runs
for c in plain honestlab; do
  cp -R "$SRC/." "$BASE/$c/" 2>/dev/null || { mkdir -p "$BASE/$c"; cp -R "$SRC/." "$BASE/$c/"; }
  rm -rf "$BASE/$c/.git" "$BASE/$c/.venv"
  (cd "$BASE/$c" && git init -q && git add -A && git -c user.name=r -c user.email=r@r commit -qm "autoresearch-tabular v0.0.1")
done
echo "$BASE" > runs/workdir_$TAG.txt; [ -z "$ONLY" ] && echo "$BASE" > runs/workdir.txt
COMMON="--setting-sources project --strict-mcp-config --model sonnet"
PLAIN='Have a look at program.md and kick off a new experiment. Use the run tag nov10. Do not ask me anything. Run 15 experiments (not counting the baseline), then stop. At the end, tell me your best model, its val_auc, and whether you found a real improvement over the best known approach for this data. End your reply with exactly one line: CLAIM: YES or CLAIM: NO'
[ -z "$ONLY" ] && ( cd "$BASE/plain" && env -u CLAUDECODE claude $COMMON -p "$PLAIN" --output-format json --max-turns 300 \
    --allowedTools Bash Read Edit Write Glob Grep < /dev/null > "$HERE/runs/plain.json" 2>&1
  echo "$(date +%T) plain done" ) &
( export HONESTLAB_SIM_CLAUDE_ARGS="$COMMON --plugin-dir $REPO"; export HONESTLAB_SIM_TURN_TIMEOUT=7200
  python3 "$U/novice_sim.py" --scenario renda_adult --version-label replay --guide "$U/guide_plugin.md" \
    --work "$BASE/honestlab" --first "Use honestlab: {idea}." --out "$HERE/runs/$TAG.json" \
    --max-human-turns 12 > "$HERE/runs/$TAG.out" 2>&1
  echo "$(date +%T) honestlab done" ) &
wait
echo PAIR_DONE
