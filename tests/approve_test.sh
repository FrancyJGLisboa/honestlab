#!/bin/bash
# Chat approval (Claude Code UserPromptSubmit hook) and plugin mode.
# Usage: bash tests/approve_test.sh   (needs honestlab on PATH)
set -u
T=$(cd "$(dirname "$0")" && pwd); KIT=$(dirname "$T"); W=$(mktemp -d)
pass=0; fail=0
check() { if eval "$2"; then pass=$((pass+1)); else fail=$((fail+1)); echo "FAIL: $1"; fi; }
hook() { python3 -c 'import json,sys; print(json.dumps({"hook_event_name":"UserPromptSubmit","cwd":sys.argv[1],"prompt":sys.argv[2]}))' "$PWD" "$1" | honestlab guard prompt; }
field() { python3 -c 'import json,sys; d=json.loads(sys.stdin.read() or "{}"); print(eval(sys.argv[1]))' "$1" 2>/dev/null; }

cd "$W" && honestlab init demo --example binpack >/dev/null && cd demo
check "an ordinary message is ignored" "[ -z \"\$(hook 'hello there')\" ]"
out=$(hook approve)
check "approve before baseline tells the agent what is missing" "echo \"\$out\" | grep -q 'cannot be approved yet' && echo \"\$out\" | grep -q baseline"
honestlab baseline >/dev/null
out=$(hook approve)
check "approve blocks the message and shows the real page to the person" "[ \"\$(echo \"\$out\" | field 'd.get(\"decision\")')\" = block ] && echo \"\$out\" | grep -q 'Approval page'"
code=$(echo "$out" | field 'd["reason"]' | grep -o 'yes [0-9]\{4\}' | tail -1 | cut -d' ' -f2)
check "the page carries a 4-digit code" "[ \${#code} = 4 ]"
check "the code is not in the agent's context" "! echo \"\$out\" | grep -q additionalContext"
check "the code is not stored in clear" "! grep -q \"\\\"\$code\\\"\" .honestlab/pending_approval.json"
wrong=$(printf '%04d' $(( (10#$code + 1) % 10000 )))
check "a wrong code is refused" "hook \"yes $wrong\" | grep -q 'Wrong code' && ! grep -q '\"frozen\": true' .honestlab/state.json"
echo "extra line" >> SPEC.md
check "a page changed after it was shown is refused" "hook \"yes $code\" | grep -q 'changed after you saw it'"
out=$(hook approve); code=$(echo "$out" | field 'd["reason"]' | grep -o 'yes [0-9]\{4\}' | tail -1 | cut -d' ' -f2)
python3 - <<'PY'
import json, pathlib
p = pathlib.Path(".honestlab/pending_approval.json"); d = json.loads(p.read_text()); d["expires"] = 0; p.write_text(json.dumps(d))
PY
check "an expired code is refused" "hook \"yes $code\" | grep -q 'expired'"
out=$(hook approve); code=$(echo "$out" | field 'd["reason"]' | grep -o 'yes [0-9]\{4\}' | tail -1 | cut -d' ' -f2)
python3 - <<'PY'
import json, pathlib
p = pathlib.Path(".honestlab/pending_approval.json"); d = json.loads(p.read_text()); d["expires"] += 3600; p.write_text(json.dumps(d))
PY
check "editing the expiry in the file voids the code" "hook \"yes $code\" | grep -q 'Wrong code'"
first=$(hook approve | field 'd["reason"]' | grep -o 'yes [0-9]\{4\}' | tail -1 | cut -d' ' -f2)
out=$(hook approve)
check "approve sent twice shows the page again instead of failing" "[ \"\$(echo \"\$out\" | field 'd.get(\"decision\")')\" = block ]"
check "the code is at the top of the message as well" "echo \"\$out\" | field 'd[\"reason\"]' | head -1 | grep -q 'TO APPROVE, SEND  yes [0-9]'"
honestlab baseline >/dev/null 2>&1
check "the pending code never enters git, even after a baseline" "[ -z \"\$(git ls-files .honestlab/pending_approval.json)\" ] && [ -z \"\$(git status --porcelain)\" ]"
out=$(hook approve)
check "approve still works after a baseline ran in between" "[ \"\$(echo \"\$out\" | field 'd.get(\"decision\")')\" = block ]"
code=$(echo "$out" | field 'd["reason"]' | grep -o 'yes [0-9]\{4\}' | tail -1 | cut -d' ' -f2)
if [ "$first" != "$code" ]; then
  check "an older code stops working once a new one is issued" "hook \"yes $first\" | grep -q 'Wrong code'"
  out=$(hook approve); code=$(echo "$out" | field 'd["reason"]' | grep -o 'yes [0-9]\{4\}' | tail -1 | cut -d' ' -f2)
else
  check "an older code stops working once a new one is issued (same code drawn twice; nothing to test)" "true"
fi
out=$(hook "yes $code")
check "the right code freezes the lab" "grep -q '\"frozen\": true' .honestlab/state.json"
check "the agent is told to continue" "echo \"\$out\" | grep -q 'continue with the experiments'"
check "the person sees a confirmation" "echo \"\$out\" | grep -q 'Approved and locked'"
check "the ledger records approval in the chat" "grep -q '\"approved_via\": \"chat\"' ledger.jsonl"
check "the pending code is deleted" "[ ! -e .honestlab/pending_approval.json ]"
check "after freezing, approve is an ordinary message" "[ -z \"\$(hook approve)\" ]"
check "the run loop works after a chat approval" "printf '\n' >> src/heuristic.py && honestlab run -m noop >/dev/null 2>&1; honestlab status | grep -q 'Frozen:    yes'"
g() { echo "$1" | honestlab guard pre >/dev/null 2>&1; echo $?; }
check "the agent cannot call the prompt hook itself" "[ \$(g '{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"echo {} | honestlab guard prompt\"}}') = 2 ]"
check "the agent cannot write the pending file" "[ \$(g '{\"tool_name\":\"Write\",\"tool_input\":{\"file_path\":\".honestlab/pending_approval.json\",\"content\":\"x\"}}') = 2 ]"

cd "$W" && honestlab init pt --example binpack --language pt >/dev/null && cd pt && honestlab baseline >/dev/null
out=$(hook aprovar); code=$(echo "$out" | field 'd["reason"]' | grep -o 'sim [0-9]\{4\}' | tail -1 | cut -d' ' -f2)
check "Portuguese: aprovar shows the page with 'sim CODE'" "[ \${#code} = 4 ] && echo \"\$out\" | field 'd[\"reason\"]' | grep -q 'Página de aprovação'"
hook "sim $code" >/dev/null
check "Portuguese: sim CODE freezes" "grep -q '\"frozen\": true' .honestlab/state.json"

# plugin mode
cd "$W"
check "the plugin's bin runs without installing" "python3 '$KIT/bin/honestlab' --version | grep -q '[0-9]'"
mkdir plug && cd plug && printf 'a,b\n1,2\n' > d.csv
python3 "$KIT/bin/honestlab" init >/dev/null
check "plugin init writes no Claude hooks or skill copies (the plugin brings them)" "[ ! -e .claude/settings.json ] && [ ! -e .claude/skills ] && [ -f CLAUDE.md ]"
check "plugin init targets Claude only" "[ ! -e .codex ] && [ ! -e .github/hooks ]"
cd "$W/demo"
deny='{"tool_name":"Edit","tool_input":{"file_path":"eval/evaluate.py","old_string":"a","new_string":"b"}}'
check "project hooks deny protected edits" "[ \$(g \"\$deny\") = 2 ]"
check "the plugin's hooks stand down when the project has its own (no double run)" "[ \$(echo \"\$deny\" | HONESTLAB_VIA_PLUGIN=1 honestlab guard pre >/dev/null 2>&1; echo \$?) = 0 ]"
cd "$W/plug"
check "the plugin's hooks act when the project has none" "[ \$(echo '{\"tool_name\":\"Read\",\"tool_input\":{\"file_path\":\"data/holdout/x.csv\"}}' | HONESTLAB_VIA_PLUGIN=1 honestlab guard pre >/dev/null 2>&1; echo \$?) = 2 ]"

# approval evidence: a verified chat approval keeps "found"; a self-approval (no message from the person) does not
mk_lab() {
  cd "$W" && mkdir "$1" && cd "$1" && printf 'dia,vendas\n1,10\n' > vendas.csv && honestlab init --language pt >/dev/null
  python3 - <<'PY'
import json
from pathlib import Path
c = json.loads(Path("lab.json").read_text()); c["finding"]["min_effect"] = 0.2; Path("lab.json").write_text(json.dumps(c, indent=2))
for f in ("SPEC.md", "APPROVAL.md"):
    Path(f).write_text(Path(f).read_text().replace("TODO", "ok"))
Path("eval/evaluate.py").write_text("import json, sys\nsys.path.insert(0, 'src')\nimport modelo\n"
    "u = [modelo.ERRO + 0.01 * ((i * 7) % 5 - 2) for i in range(40)]\nprint(json.dumps({'score': sum(u) / len(u), 'per_unit': u}))\n")
Path("src/modelo.py").write_text("ERRO = 10.0\n"); Path("notes/ref.py").write_text("ERRO = 9.0\n")
PY
  honestlab data add vendas.csv --split dev >/dev/null; honestlab data add vendas.csv --split holdout >/dev/null
  honestlab baseline >/dev/null; honestlab reference add conhecido --from notes/ref.py -m ref >/dev/null
}
finish_found() {
  printf 'ERRO = 7.0\n' > src/modelo.py; honestlab run -m "erro menor" >/dev/null
  honestlab finding new -m "erra menos" >/dev/null; perl -pi -e 's/TODO/ok/g' findings/F001/literature.md
  printf '# review\nok\nVerdict: ACCEPT\n' > findings/F001/review.md; honestlab finding verify F001 >/dev/null; honestlab report >/dev/null
}
TR="$W/transcript.jsonl"; : > "$TR"
hookt() { python3 -c 'import json,sys; print(json.dumps({"hook_event_name":"UserPromptSubmit","cwd":sys.argv[1],"prompt":sys.argv[2],"transcript_path":sys.argv[3],"session_id":"s1"}))' "$PWD" "$1" "$TR" | honestlab guard prompt; }
said() { python3 -c 'import json,sys; print(json.dumps({"type":"user","sessionId":"s1","timestamp":"2026-11-08T12:00:00Z","message":{"role":"user","content":sys.argv[1]}}))' "$1" >> "$TR"; }
mk_lab real
code=$(hookt aprovar | field 'd["reason"]' | grep -o 'sim [0-9]\{4\}' | tail -1 | cut -d' ' -f2)
said "sim $code"; hookt "sim $code" >/dev/null
check "status confirms a chat approval from the person's own message" "honestlab status | grep -q \"confirmed by the person's own message\""
finish_found
check "a verified chat approval keeps the verdict Encontrou" "grep -q '^\*\*Encontrou' REPORT.md && grep -q 'feita por você na conversa' REPORT.md"
mk_lab fake
python3 -c "import sys; sys.path.insert(0, '$KIT'); from honestlab import cli, core; r = core.find_root(); cli.freeze_lock(r, core.load_config(r), core.load_state(r), 'chat')"
check "status warns when a chat approval has no message from the person" "honestlab status | grep -q 'WARNING: recorded as chat'"
finish_found
check "an unconfirmed approval downgrades Encontrou to fragile" "grep -q '^\*\*Sinal promissor' REPORT.md && grep -q 'ATENÇÃO' REPORT.md"
mk_lab forged
code=$(hookt aprovar | field 'd["reason"]' | grep -o 'sim [0-9]\{4\}' | tail -1 | cut -d' ' -f2)
python3 -c 'import json,sys; print(json.dumps({"type":"user","isSidechain":True,"sessionId":"s1","message":{"role":"user","content":sys.argv[1]}}))' "sim $code" >> "$TR"
hookt "sim $code" >/dev/null
perl -i -ne 'print unless eof' "$TR"; python3 -c 'import json,sys; print(json.dumps({"type":"user","sessionId":"s1","message":{"role":"user","content":[{"type":"tool_result","content":sys.argv[1]}]}}))' "sim $code" >> "$TR"
check "a subagent message or tool result does not count as the person's approval" "honestlab status | grep -q 'WARNING: recorded as chat'"

chmod -R u+w "$W"; rm -rf "$W"
echo "$pass passed, $fail failed"
[ "$fail" = 0 ]
