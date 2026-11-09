#!/bin/bash
# Self-test: bash tests/run_all.sh   (needs honestlab on PATH, git, python3; Linux/macOS)
set -u
T=$(cd "$(dirname "$0")" && pwd); W=$(mktemp -d); L=$(command -v honestlab)
cd "$W" && honestlab init demo --example binpack >/dev/null && cd demo && honestlab baseline >/dev/null
env -u CLAUDECODE python3 "$T/tty_run.py" "$PWD" demo honestlab freeze | grep -q "Frozen" || { echo "freeze failed"; exit 1; }
echo "== guard decisions =="; python3 "$T/guard_test.py" "$PWD" | tail -1
echo "== edge cases ==";      bash "$T/edge.sh" "$L" | tail -1
echo "== chat approval and plugin ==";  bash "$T/approve_test.sh" | tail -1
echo "== red-team regressions ==";      bash "$T/redteam_test.sh" | tail -1
echo "== robustness ==";                 python3 "$T/robust_test.py" "$L" | tail -1
echo "== overnight mode ==";             python3 "$T/overnight_test.py" "$L" | tail -1
chmod -R u+w "$W"; rm -rf "$W"
