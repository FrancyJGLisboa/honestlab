"""The honestlab skill follows Anthropic's "Skill authoring best practices"
(https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices). Each rule below is one
measurable line of that guide.

Usage: python3 tests/skill_lint_test.py
"""
import re
import sys
from pathlib import Path

SKILL = Path(__file__).resolve().parent.parent / "honestlab" / "skill"
passed = failed = 0


def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1
        print(f"ok   {name}")
    else:
        failed += 1
        print(f"FAIL {name}" + (f"\n     {detail.strip()[:500]}" if detail else ""))


main = (SKILL / "SKILL.md").read_text(encoding="utf-8")
m = re.match(r"---\n(.*?)\n---\n(.*)", main, re.S)
front, body = (m.group(1), m.group(2)) if m else ("", main)
fields = dict(re.findall(r"^(\w+):\s*(.*)$", front, re.M))
name, desc = fields.get("name", ""), fields.get("description", "")

check("frontmatter has name and description", bool(name and desc), front)
check("name: at most 64 characters, lowercase letters, digits and hyphens",
      len(name) <= 64 and re.fullmatch(r"[a-z0-9-]+", name) is not None, name)
check("name: no reserved word (anthropic, claude)", not re.search(r"anthropic|claude", name), name)
check("description: at most 1,024 characters", 0 < len(desc) <= 1024, str(len(desc)))
check("description: no XML tags", not re.search(r"<[^>]+>", desc + name), desc[:200])
first = desc.split()[0] if desc else ""
check("description: third person (\"Guides ...\", not \"Guide ...\" or \"I/You can ...\")",
      first.endswith("s") and not re.match(r"(I|You)\b", desc), first)
check("description: says what it does and when to use it", "Use when" in desc, desc[-200:])
check("SKILL.md body under 500 lines", body.count("\n") < 500, str(body.count("\n")))

others = sorted(p.name for p in SKILL.glob("*.md") if p.name != "SKILL.md")
missing = [n for n in others if f"`{n}`" not in body]
check("every reference file is linked directly from SKILL.md (one level deep)", not missing, ", ".join(missing))
for p in sorted(SKILL.glob("*.md")):
    text = p.read_text(encoding="utf-8")
    if p.name != "SKILL.md" and text.count("\n") > 100:
        check(f"{p.name}: longer than 100 lines, so it starts with a table of contents",
              "## Contents" in text[:1500], text[:300])
    check(f"{p.name}: no Windows-style paths", not re.search(r"\b\w+\\\w+\.(py|md|json)\b", text))

print(f"{passed} passed, {failed} failed")
sys.exit(1 if failed else 0)
