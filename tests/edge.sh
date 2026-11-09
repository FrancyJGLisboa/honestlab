#!/bin/bash
# Edge-case battery for honestlab. Usage: edge.sh <honestlab-binary>
L="$1"; S=$(cd "$(dirname "$0")" && pwd); W="$(mktemp -d)/edge work"; TTY="$S/tty_run.py"
PY=$(head -1 "$L" | sed 's/^#!//')
pass=0; fail=0
check() { if eval "$2"; then echo "ok   $1"; pass=$((pass+1)); else echo "FAIL $1"; fail=$((fail+1)); fi; }
freeze() { env -u CLAUDECODE python3 "$TTY" "$1" "$2" env PATH="$(dirname "$L"):$PATH" honestlab freeze; }
unfreeze() { env -u CLAUDECODE python3 "$TTY" "$1" "$2" env PATH="$(dirname "$L"):$PATH" honestlab unfreeze; }
chmod -R u+w "$W" 2>/dev/null; rm -rf "$W"; mkdir -p "$W"; cd "$W"
echo "python: $($PY --version)"

# 1. path with spaces + only one agent
"$L" init "my proj" --example binpack --agents claude >/dev/null
check "init in path with spaces" "[ -f 'my proj/lab.json' ]"
check "--agents claude writes no codex/copilot files" "[ ! -e 'my proj/.codex' ] && [ ! -e 'my proj/.github' ] && [ -f 'my proj/.claude/settings.json' ]"
check "example registers the best_fit reference" "(cd 'my proj' && \"$L\" reference list | grep -q best_fit)"
cd "my proj"
python3 -c "
import json; from pathlib import Path
c = json.loads(Path('lab.json').read_text()); c['finding']['min_effect'] = 0.5
Path('lab.json').write_text(json.dumps(c, indent=2))"
"$L" baseline >/dev/null; freeze "$PWD" "my proj" >/dev/null
check "freeze works in path with spaces" "\"$L\" status | grep -q 'Frozen:    yes'"

# 2. the finding bar is checked against the strongest reference, before spending holdout
cat > src/heuristic.py <<'PYCODE'
def choose_bin(item, loads, capacity):
    best, bl = -1, -1
    for i, l in enumerate(loads):
        if l + item <= capacity and l > bl:
            best, bl = i, l
    return best
PYCODE
check "re-implementing the reference is kept vs weak baseline" "\"$L\" run -m 'best fit beats next fit' | grep -q KEEP"
out=$("$L" finding new -m "best fit is a finding (it is just the reference)" 2>&1)
check "finding refused: no effect over strongest reference" "echo \"\$out\" | grep -q 'does not reach the pre-registered bar'"
check "refused finding spent no holdout run" "\"$L\" status | grep -q 'Holdout:   0/3'"

# 3. holdout NOT confirmed: beats best fit on dev, collapses on longer holdout sequences
cat > src/heuristic.py <<'PYCODE'
_count = [0]
def choose_bin(item, loads, capacity):
    _count[0] += 1
    if _count[0] > 150:          # dev instances have 150 items; afterwards: one bin per item
        return -1
    best, bs = -1, None
    for i, l in enumerate(loads):
        gap = capacity - l - item
        if gap < 0:
            continue
        sc = gap if (gap == 0 or gap >= 20) else gap + 100
        if bs is None or sc < bs:
            best, bs = i, sc
    return best
PYCODE
"$L" run -m "gap rule tuned to dev-length sequences" >/dev/null
out=$("$L" finding new -m "dev-length rule generalizes to longer sequences" 2>&1)
check "holdout rejects a dev-only improvement (paired CI)" "echo \"\$out\" | grep -q 'does NOT confirm'"
"$L" report >/dev/null 2>&1
check "report: a candidate that failed on the holdout reads 'not found', not 'untested'" "grep -q '^\*\*Not found' REPORT.md && grep -q 'did not hold' REPORT.md && grep -q '\"failed-holdout\"' ledger.jsonl"
check "claim.md records reference, CI and experiments tried" "grep -q 'best_fit' findings/F001/claim.md && grep -q 'CI' findings/F001/claim.md && grep -q 'Experiments tried' findings/F001/claim.md"

# 3b. holdout budget exhausted
"$L" finding new -m "second holdout look at same candidate" >/dev/null 2>&1
"$L" finding new -m "third holdout look at same candidate" >/dev/null 2>&1
out=$("$L" finding new -m "fourth look should be refused by budget" 2>&1)
check "holdout budget enforced" "echo \"\$out\" | grep -q 'budget exhausted'"
cd "$W"

# 3c. statistics: noise is not an improvement; per_unit consistency; repeats
"$L" init stat >/dev/null; cd stat
python3 -c "
import json; from pathlib import Path
c = json.loads(Path('lab.json').read_text()); c['finding']['min_effect'] = 0.1
Path('lab.json').write_text(json.dumps(c, indent=2))
Path('SPEC.md').write_text(Path('SPEC.md').read_text().replace('TODO', 'filled')); Path('APPROVAL.md').write_text(Path('APPROVAL.md').read_text().replace('TODO', 'filled'))
Path('eval/evaluate.py').write_text('''import argparse, json, random, sys
sys.path.insert(0, \"src\")
ap = argparse.ArgumentParser(); ap.add_argument(\"--split\"); a = ap.parse_args()
import sol
rng = random.Random(sol.PARAM + a.split)
units = [10.0 - sol.EFFECT + rng.gauss(0, 1) for _ in range(30)]
score = sum(units) / len(units) + getattr(sol, \"SKEW\", 0.0)
print(json.dumps({\"score\": score, \"per_unit\": units}))
''')
Path('src/sol.py').write_text('PARAM = \"a\"\nEFFECT = 0.0\n')
Path('data/holdout/h.txt').write_text('x')"
"$L" baseline >/dev/null; freeze "$PWD" stat >/dev/null
P=$(python3 -c "
import random
r0 = random.Random('adev'); b = [10 + r0.gauss(0, 1) for _ in range(30)]
for k in range(2000):
    r = random.Random(f'p{k}dev'); c = [10 + r.gauss(0, 1) for _ in range(30)]
    d = sum(b) / 30 - sum(c) / 30
    if 0.05 < d < 0.15:
        print(f'p{k}'); break")
printf 'PARAM = "%s"\nEFFECT = 0.0\n' "$P" > src/sol.py
out=$("$L" run -m "a different random draw, no real effect")
check "noise that is better on average is discarded as not significant" "echo \"\$out\" | grep -q 'not significant'"
printf 'PARAM = "a"\nEFFECT = 1.0\n' > src/sol.py
check "a real effect is kept with a CI" "\"$L\" run -m 'real improvement of one unit' | grep -q 'KEEP.*CI'"
printf 'PARAM = "a"\nEFFECT = 2.0\nSKEW = 5.0\n' > src/sol.py
check "per_unit inconsistent with metric triggers a warning" "\"$L\" run -m 'metric no longer the mean of per_unit' | grep -q 'per_unit ignored'"
cd "$W"
"$L" init rep >/dev/null; cd rep
python3 -c "
import json; from pathlib import Path
c = json.loads(Path('lab.json').read_text()); c['finding']['min_effect'] = 0.1; c['repeats'] = 5
Path('lab.json').write_text(json.dumps(c, indent=2))
Path('SPEC.md').write_text(Path('SPEC.md').read_text().replace('TODO', 'filled')); Path('APPROVAL.md').write_text(Path('APPROVAL.md').read_text().replace('TODO', 'filled'))
Path('eval/evaluate.py').write_text('''import argparse, json, os, random, sys
sys.path.insert(0, \"src\")
ap = argparse.ArgumentParser(); ap.add_argument(\"--split\"); a = ap.parse_args()
import sol
rng = random.Random(int(os.environ[\"HONESTLAB_SEED\"]) * 7919 + sol.SALT)
print(json.dumps({\"score\": 10.0 - sol.EFFECT + rng.gauss(0, 0.3)}))
''')
Path('src/sol.py').write_text('SALT = 1\nEFFECT = 0.0\n')
Path('data/holdout/h.txt').write_text('x')"
"$L" baseline >/dev/null; freeze "$PWD" rep >/dev/null
printf 'SALT = 1\nEFFECT = 1.0\n' > src/sol.py
check "repeats: stochastic evaluator compared by bootstrap over repeats" "\"$L\" run -m 'one unit better with seeds varying' | grep -q 'bootstrap over repeats'"
check "baseline records the environment in the ledger" "grep -q '\"platform\"' ledger.jsonl"
cd "$W"; cd "my proj"

# 3d. a reference that looks weak on dev but is strongest on holdout must be the holdout bar
cd "$W"; "$L" init flip >/dev/null; cd flip
cat > /tmp/flip_setup.py <<'PYSETUP'
import json
from pathlib import Path
c = json.loads(Path("lab.json").read_text()); c["finding"]["min_effect"] = 1.0; c["finding"]["effect"] = "absolute"
Path("lab.json").write_text(json.dumps(c, indent=2))
Path("SPEC.md").write_text(Path("SPEC.md").read_text().replace("TODO", "filled")); Path("APPROVAL.md").write_text(Path("APPROVAL.md").read_text().replace("TODO", "filled"))
Path("eval/evaluate.py").write_text(
    "import argparse, json, sys\n"
    "sys.path.insert(0, 'src')\n"
    "ap = argparse.ArgumentParser(); ap.add_argument('--split'); a = ap.parse_args()\n"
    "import sol\n"
    "v = sol.DEV if a.split == 'dev' else sol.HOLD\n"
    "units = [v + 0.01 * ((i * 7) % 5 - 2) for i in range(30)]\n"
    "print(json.dumps({'score': sum(units) / len(units), 'per_unit': units}))\n")
Path("src/sol.py").write_text("DEV = 10.0\nHOLD = 10.0\n")
Path("data/holdout/h.txt").write_text("x")
PYSETUP
python3 /tmp/flip_setup.py
"$L" baseline >/dev/null
printf 'DEV = 11.0\nHOLD = 6.0\n' > src/sol.py
"$L" reference add known -m "weak on dev, strong on new data" >/dev/null
freeze "$PWD" flip >/dev/null
check "reference list marks the holdout-strongest method" "\"$L\" reference list | grep -q 'known.*strongest on holdout'"
printf 'DEV = 8.0\nHOLD = 7.0\n' > src/sol.py
"$L" run -m "better on dev than everything registered" >/dev/null
out=$("$L" finding new -m "beats every known method" 2>&1)
check "finding rejected against the reference that is strongest on holdout" "echo \"\$out\" | grep -q \"NOT confirm against 'known'\""
cd "$W"; cd "my proj"

# 4. unfreeze / refreeze resets the baseline
unfreeze "$PWD" "my proj" >/dev/null
check "unfreeze resets baseline" "\"$L\" status | grep -q 'Baseline:  n/a'"
check "unfreeze restores write permission" "[ -w lab.json ]"
"$L" baseline >/dev/null; freeze "$PWD" "my proj" >/dev/null
check "refreeze after unfreeze" "\"$L\" status | grep -q 'Frozen:    yes'"
check "ledger still intact after cycle" "\"$L\" status | grep -q 'hash chain intact'"
cd "$W"

# 5. maximize direction, evaluator timeout, evaluator without JSON
"$L" init maxproj >/dev/null; cd maxproj
python3 - <<'EOF'
import json, re
from pathlib import Path
cfg = json.loads(Path("lab.json").read_text()); cfg.update(direction="maximize", metric="acc", timeout_sec=3); cfg["finding"]["min_effect"] = 0.01
Path("lab.json").write_text(json.dumps(cfg, indent=2))
Path("APPROVAL.md").write_text(Path("APPROVAL.md").read_text().replace("TODO", "filled"))
s = Path("SPEC.md").read_text().replace("TODO", "filled")
Path("SPEC.md").write_text(s)
Path("eval/evaluate.py").write_text('''import argparse, json, sys
sys.path.insert(0, "src")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); a = ap.parse_args()
import solve
print("some log line")
print(json.dumps({"acc": solve.acc(a.split)}))
''')
Path("src/solve.py").write_text("def acc(split):\n    return 0.5\n")
Path("data/holdout/h.txt").write_text("x")
EOF
"$L" baseline >/dev/null 2>&1; freeze "$PWD" maxproj >/dev/null
printf "def acc(split):\n    return 0.4\n" > src/solve.py
check "maximize: lower score discarded" "\"$L\" run -m 'lower accuracy should be discarded' | grep -q DISCARD"
printf "def acc(split):\n    return 0.7\n" > src/solve.py
check "maximize: higher score kept" "\"$L\" run -m 'higher accuracy should be kept' | grep -q KEEP"
printf "import time\ndef acc(split):\n    time.sleep(10)\n    return 0.9\n" > src/solve.py
check "evaluator timeout recorded as error" "\"$L\" run -m 'slow solution should time out' | grep -q 'timed out'"
check "timeout change was reverted" "grep -q 0.7 src/solve.py"
printf "def acc(split):\n    return 'high'\n" > src/solve.py
check "non-numeric metric recorded as error" "\"$L\" run -m 'string metric should be an error' | grep -q ERROR"
cd "$W"

# 6. init into a dirty git repo is refused
mkdir dirty && cd dirty && git init -q && echo x > f.txt
check "init refuses dirty repo" "! \"$L\" init . >/dev/null 2>&1"
cd "$W"

# 7. stop hook payload variants
cd "my proj"; echo "# pending" >> src/heuristic.py
check "stop blocks (Claude/Codex field names)" "echo '{\"stop_hook_active\": false}' | \"$L\" guard stop | grep -q block"
check "stop blocks (Copilot camelCase, no flag)" "echo '{\"sessionId\": \"x\"}' | \"$L\" guard stop | grep -q block"
check "stop allows when already continuing" "echo '{\"stop_hook_active\": true}' | \"$L\" guard stop | grep -qv block"
check "guard tolerates garbage input" "echo 'not json' | \"$L\" guard pre; [ \$? -eq 0 ]"
git checkout -q -- src
cd "$W"

# 8. init --here inside an existing repository
mkdir repo && cd repo && git init -q && git config user.name t && git config user.email t@t
mkdir -p pkg data .claude
printf "# Team rules\n- be careful\n" > CLAUDE.md
printf '{"permissions": {"allow": ["Bash(make test)"]}}\n' > .claude/settings.json
printf "big.bin\n" > .gitignore
printf "def f(x):\n    return x\n" > pkg/model.py
printf "1,2\n" > data/raw.csv
git add -A && git commit -qm init
check "--here refuses a missing editable path" "! \"$L\" init --here --editable nope.py >/dev/null 2>&1"
"$L" init --here --editable pkg/model.py >/dev/null
check "--here creates its own branch" "[ \"\$(git rev-parse --abbrev-ref HEAD)\" = honestlab/repo ]"
check "--here keeps team CLAUDE.md and imports AGENTS.md" "grep -q 'Team rules' CLAUDE.md && grep -q '@AGENTS.md' CLAUDE.md"
check "--here merges hooks without dropping permissions" "python3 -c \"import json; d=json.load(open('.claude/settings.json')); assert d['permissions']['allow']==['Bash(make test)']; assert 'honestlab guard pre' in json.dumps(d['hooks'])\""
check "--here keeps existing .gitignore lines" "grep -q big.bin .gitignore && grep -q '.honestlab/local.json' .gitignore"
check "--here does not touch the repo's data/ folder" "[ \"\$(cat data/raw.csv)\" = '1,2' ] && [ -d lab/data/holdout ]"
check "--here sets editable from the flag" "grep -q 'pkg/model.py' lab.json"
check "--here status shows lab paths" "\"$L\" status | grep -q 'SPEC:       lab/SPEC.md'"
"$L" init --here >/dev/null 2>&1; check "--here refuses a second lab on the same branch" "[ \$? -ne 0 ]"
check "--here master branch untouched" "[ -z \"\$(git ls-tree -r --name-only master | grep -E '^(lab|lab.json|AGENTS.md)')\" ]"
python3 - <<'EOF'
import json
from pathlib import Path
s = Path("lab/SPEC.md").read_text().replace("TODO", "filled"); Path("lab/SPEC.md").write_text(s)
Path("lab/APPROVAL.md").write_text(Path("lab/APPROVAL.md").read_text().replace("TODO", "filled"))
c = json.loads(Path("lab.json").read_text()); c["finding"]["min_effect"] = 0.1; Path("lab.json").write_text(json.dumps(c, indent=2))
Path("lab/eval/evaluate.py").write_text('''import argparse, json, sys
sys.path.insert(0, ".")
ap = argparse.ArgumentParser(); ap.add_argument("--split"); ap.parse_args()
from pkg.model import f
print(json.dumps({"score": float(f(3))}))
''')
Path("lab/data/holdout/h.csv").write_text("x\n")
EOF
"$L" baseline >/dev/null; freeze "$PWD" repo >/dev/null
check "--here freeze" "\"$L\" status | grep -q 'Frozen:    yes'"
printf "def f(x):\n    return x - 1\n" > pkg/model.py
check "--here run keeps an improvement in the repo's own file" "\"$L\" run -m 'subtract one to lower the score' | grep -q KEEP"
check "--here experiment patch stored under lab/" "[ -f lab/experiments/E0001.patch ]"
echo "x" > pkg/other.py
check "--here run refuses changes outside editable" "\"$L\" run -m 'stray file must be refused' 2>&1 | grep -q 'Unexpected changes: pkg/other.py'"
rm pkg/other.py
g() { echo "$1" | "$L" guard pre >/dev/null 2>&1; echo $?; }
check "--here guard blocks lab/eval edit" "[ \$(g '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"lab/eval/evaluate.py\"}}') = 2 ]"
check "--here guard blocks holdout read" "[ \$(g '{\"tool_name\":\"Read\",\"tool_input\":{\"file_path\":\"lab/data/holdout/h.csv\"}}') = 2 ]"
check "--here guard blocks lab/ledger edit" "[ \$(g '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"lab/ledger.jsonl\"}}') = 2 ]"
check "--here guard allows editing the repo's data/" "[ \$(g '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"data/raw.csv\"}}') = 0 ]"
check "--here guard allows editable file" "[ \$(g '{\"tool_name\":\"Edit\",\"tool_input\":{\"file_path\":\"pkg/model.py\"}}') = 0 ]"
cd "$W"

# 9. honestlab 0.4: novice flow (init in a data folder, data add, reference --from, text edits, sim, report, setup)
cd "$W"; mkdir sorvete && cd sorvete && printf 'dia,vendas\n1,10\n' > vendas.csv
"$L" init --language pt >/dev/null
check "init keeps the person's data file" "[ -f vendas.csv ] && [ -f lab.json ]"
check "init writes the approval page in Portuguese" "grep -q 'Página de aprovação' APPROVAL.md"
check "init installs the single honestlab skill" "[ -f .claude/skills/honestlab/SKILL.md ] && [ -f .claude/skills/honestlab/frame.md ] && [ ! -e .claude/skills/honestlab-frame ]"
check "lab.json hides the statistics knobs" "! grep -q keep_alpha lab.json && grep -q '\"language\": \"pt\"' lab.json"
check "check-spec requires a filled approval page" "\"$L\" check-spec 2>&1 | grep -q 'APPROVAL.md still contains TODO'"
cat > /tmp/v04_setup.py <<'PYSETUP'
import json
from pathlib import Path
c = json.loads(Path("lab.json").read_text()); c["finding"]["min_effect"] = 0.2; Path("lab.json").write_text(json.dumps(c, indent=2))
for f in ("SPEC.md", "APPROVAL.md"):
    Path(f).write_text(Path(f).read_text().replace("TODO", "ok"))
Path("eval/evaluate.py").write_text(
    "import json, sys\n"
    "sys.path.insert(0, 'src')\n"
    "import modelo\n"
    "u = [modelo.ERRO + 0.01 * ((i * 7) % 5 - 2) for i in range(40)]\n"
    "print(json.dumps({'score': sum(u) / len(u), 'per_unit': u}))\n")
Path("src/modelo.py").write_text("ERRO = 10.0\n")
Path("notes/ref.py").write_text("ERRO = 9.0\n")
Path("notes/same.py").write_text("ERRO = 10.0  # same value, different file\n")
PYSETUP
python3 /tmp/v04_setup.py
"$L" data add vendas.csv --split dev >/dev/null
"$L" data add vendas.csv --split holdout >/dev/null
check "data add copies into dev and holdout" "[ -f data/dev/vendas.csv ] && [ -f data/holdout/vendas.csv ]"
g() { echo "$1" | "$L" guard pre >/dev/null 2>&1; echo $?; }
check "guard allows honestlab data add to holdout before freeze" "[ \$(g '{\"tool_name\":\"Bash\",\"tool_input\":{\"command\":\"honestlab data add x.csv --split holdout\"}}') = 0 ]"
check "guard blocks reading holdout before freeze" "[ \$(g '{\"tool_name\":\"Read\",\"tool_input\":{\"file_path\":\"data/holdout/vendas.csv\"}}') = 2 ]"
"$L" baseline >/dev/null
check "reference --from replaces the single code file" "\"$L\" reference add conhecido --from notes/ref.py -m 'metodo conhecido' | grep -q 'score = 9'"
check "reference identical to the start triggers a warning" "\"$L\" reference add igual --from notes/same.py | grep -q WARNING"
check "code restored after reference add" "grep -q 'ERRO = 10.0' src/modelo.py"
echo "texto novo" >> SPEC.md; echo "nota" >> APPROVAL.md
out=$(env -u CLAUDECODE python3 "$TTY" "$PWD" sim env PATH="$(dirname "$L"):$PATH" honestlab freeze)
check "freeze shows the approval page and accepts after text-only edits" "echo \"\$out\" | grep -q 'Página de aprovação' && echo \"\$out\" | grep -q 'Frozen\.'"
check "data add refused after freeze" "! \"$L\" data add vendas.csv --split dev >/dev/null 2>&1"
"$L" report >/dev/null
check "report: not found yet before any experiment" "grep -q 'Não encontrou' REPORT.md"
printf 'ERRO = 7.0\n' > src/modelo.py
"$L" run -m "erro menor de verdade" >/dev/null
"$L" report >/dev/null
check "report: fragile (untested) when the best reaches the bar but is unconfirmed" "grep -q 'Sinal promissor' REPORT.md && grep -q 'Ainda falta a checagem' REPORT.md"
"$L" finding new -m "o modelo novo erra menos que o metodo conhecido" >/dev/null
. "$S/prior_work.sh"
vf() { "$L" finding verify F001 2>&1; }
perl -pi -e 's/TODO/ok/g' findings/F001/literature.md
printf '# review\nok\nVerdict: ACCEPT\n' > findings/F001/review.md
check "verify refuses free text without a checkable search" "vf | grep -q 'search date' && vf | grep -q 'has no link' && vf | grep -q 'Prior work re-check'"
fill_prior_work findings/F001
perl -0pi -e 's/\| temperature retail[^\n]*\n//' findings/F001/literature.md
check "verify refuses only 2 searches" "vf | grep -q 'at least 3 searches (query and source), found 2'"
fill_prior_work findings/F001
perl -pi -e 's/\| (arXiv|GitHub) \|/| Google Scholar |/' findings/F001/literature.md
check "verify refuses a single source" "vf | grep -q 'at least 2 different sources'"
fill_prior_work findings/F001
perl -pi -e 's#https://example.org/paper#(no link)#' findings/F001/literature.md
check "verify refuses a listed work without a link" "vf | grep -q 'has no link'"
fill_prior_work findings/F001
perl -pi -e 's/^Novelty: .*/Novelty: maybe/' findings/F001/literature.md
check "verify refuses a missing novelty line" "vf | grep -q \"'Novelty: known'\""
fill_prior_work findings/F001
perl -pi -e 's/^Missed: none/Missed: maybe something/' findings/F001/review.md
check "verify refuses a re-check without 'none' or a link" "vf | grep -q \"'Missed:' must be\""
fill_prior_work findings/F001
check "the ledger has no verdict after refused verifies" "! grep -q '\"verified\"' ledger.jsonl"
"$L" finding verify F001 >/dev/null
"$L" report >/dev/null
check "report: found after holdout and independent review" "grep -q 'Encontrou' REPORT.md && grep -q 'Alta' REPORT.md"
check "report shows the prior-work search next to the verdict" "grep -q 'É novo?' REPORT.md && grep -q 'Existe trabalho parecido' REPORT.md && grep -q '3 buscas em 3 fontes' REPORT.md"
check "the ledger records the search and the reviewer's re-check" "grep -q '\"novelty\": \"similar\"' ledger.jsonl && grep -q 'Semantic Scholar' ledger.jsonl"
check "report has the AI-labs comparison table" "grep -q 'AlphaEvolve' REPORT.md"
python3 - <<'PYPLAIN'
from pathlib import Path
p = Path("REPORT.md"); s = p.read_text()
s = s.replace("<!-- honestlab: the agent replaces this line with 3 to 5 plain sentences for the person -->", "Texto simples do agente.")
p.write_text(s)
PYPLAIN
"$L" report >/dev/null
check "report keeps the agent's plain words when the verdict is unchanged" "grep -q 'Texto simples do agente' REPORT.md"
check "report also writes PROGRESS.html, in the lab's language, with the verdict" "grep -q 'Progresso' PROGRESS.html && grep -q 'Encontrou' PROGRESS.html"
check "PROGRESS.html has one mark per attempt and a table view" "[ \$(grep -o 'class=\"hit\"' PROGRESS.html | wc -l) -eq \$(grep -c '\"type\": \"experiment\"' ledger.jsonl) ] && grep -q '<table>' PROGRESS.html"
check "PROGRESS.html loads nothing from the network" "! grep -Eq '(src|href)=\"(https?:)?//' PROGRESS.html"
cd "$W"
mkdir velho && cd velho && git init -q && git config user.name t && git config user.email t@t && echo 'print(1)' > app.py && git add -A && git commit -qm init
"$L" init >/dev/null
check "init in an existing repo adds the lab beside the code" "[ -f lab/APPROVAL.md ] && [ \"\$(git rev-parse --abbrev-ref HEAD)\" = honestlab/velho ]"
cd "$W"
HOME="$W/fakehome" "$L" setup --agents claude,codex >/dev/null
check "setup installs the skill for the user" "[ -f '$W/fakehome/.claude/skills/honestlab/SKILL.md' ] && [ -f '$W/fakehome/.agents/skills/honestlab/finding.md' ]"
cd "$W"

echo; echo "$pass passed, $fail failed"
