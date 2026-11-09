"""Check that a finding's prior-work search can be checked by someone else.

`literature.md` holds a search date, a table of searches (query, source, what was looked at),
a table of the closest work found (each with a link), and a novelty line. `review.md` holds the
reviewer's own re-run of one search. honestlab makes no network calls, so these checks cover
the form of the search, not whether the links are real or the search complete.
"""
from __future__ import annotations

import re

MIN_QUERIES = 3
MIN_SOURCES = 2
NOVELTY = {
    "known": "known", "conhecido": "known", "já conhecido": "known", "ja conhecido": "known",
    "similar": "similar", "parecido": "similar", "semelhante": "similar",
    "nothing found": "nothing found", "nada encontrado": "nothing found",
}
LINK = re.compile(r"(https?://\S+|doi:\s*10\.\S+|arxiv:\s*\d{4}\.\d{4,5})", re.I)


def _section(text: str, title: str) -> str:
    m = re.search(rf"^##\s*{title}\s*$(.*?)(?=^##\s|\Z)", text, re.M | re.S | re.I)
    return m.group(1) if m else ""


def _rows(section: str) -> list:
    """Data rows of the first markdown table in a section, as lists of stripped cells."""
    rows = []
    for line in section.splitlines():
        line = line.strip()
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if all(re.fullmatch(r":?-{2,}:?", c) for c in cells if c):
            continue
        rows.append(cells)
    return rows[1:]  # drop the header row


def _filled(cell: str) -> bool:
    return bool(cell) and cell.upper() not in ("TODO", "-", "N/A", "NA") and "TODO" not in cell


def check_literature(text: str):
    """Return (problems, summary)."""
    problems = []
    m = re.search(r"^\*\*(?:Search date|Data da busca):\*\*\s*(\d{4}-\d{2}-\d{2})\s*$", text, re.M | re.I)
    date = m.group(1) if m else None
    if not date:
        problems.append("literature.md: write the search date as **Search date:** YYYY-MM-DD")
    searches = [r for r in _rows(_section(text, r"(?:Searches|Buscas)")) if len(r) >= 2]
    good = [r for r in searches if _filled(r[0]) and _filled(r[1])]
    if len(good) < MIN_QUERIES:
        problems.append(f"literature.md: list at least {MIN_QUERIES} searches (query and source), found {len(good)}")
    sources = sorted({re.sub(r"\s+", " ", r[1]).strip().lower() for r in good})
    if len(sources) < MIN_SOURCES:
        problems.append(f"literature.md: search at least {MIN_SOURCES} different sources (for example Google Scholar, "
                        f"arXiv, Semantic Scholar, GitHub), found {len(sources)}")
    works = [r for r in _rows(_section(text, r"(?:Closest work found|Trabalhos mais próximos)")) if any(_filled(c) for c in r)]
    for r in works:
        if not any(LINK.search(c) for c in r):
            problems.append(f"literature.md: the work '{r[0][:60]}' has no link (http, doi: or arXiv:)")
        elif len(r) < 3 or not _filled(r[2]):
            problems.append(f"literature.md: say how '{r[0][:60]}' differs from the claim")
    m = re.search(r"^(?:Novelty|Novidade):\s*(.+?)\s*$", text, re.M | re.I)
    novelty = NOVELTY.get(m.group(1).strip().strip("*").lower()) if m else None
    if novelty is None:
        problems.append("literature.md: end the assessment with a line 'Novelty: known', 'Novelty: similar' or "
                        "'Novelty: nothing found'")
    elif novelty in ("known", "similar") and not works:
        problems.append(f"literature.md: novelty is '{novelty}', so list that work under 'Closest work found'")
    closest = None
    if works:
        r = works[0]
        link = next((LINK.search(c).group(1) for c in r if LINK.search(c)), None)
        closest = {"work": r[0][:200], "link": link}
    summary = {"date": date, "queries": len(good), "sources": sources, "works": len(works),
               "novelty": novelty, "closest": closest}
    return problems, summary


def check_review_rerun(text: str):
    """Return (problems, rerun). The reviewer runs one search again on their own."""
    sec = _section(text, r"(?:Prior work re-check|Nova checagem da literatura)")
    fields = {}
    for key, names in (("query", "Query|Busca"), ("source", "Source|Fonte"), ("missed", "Missed|Faltou")):
        m = re.search(rf"^\s*(?:{names}):\s*(.+?)\s*$", sec, re.M | re.I)
        fields[key] = m.group(1).strip() if m and _filled(m.group(1).strip()) else None
    problems = []
    if not sec.strip():
        problems.append("review.md: add the section '## Prior work re-check', where the reviewer runs one search again")
    else:
        for key in ("query", "source", "missed"):
            if not fields[key]:
                problems.append(f"review.md: fill '{key.capitalize()}:' in '## Prior work re-check' "
                                + ("(write 'none' if the search missed nothing)" if key == "missed" else ""))
    missed = fields.get("missed")
    fields["found_missed"] = bool(missed and LINK.search(missed))
    if missed and not fields["found_missed"] and missed.lower() not in ("none", "nada", "nenhum", "nothing"):
        problems.append("review.md: 'Missed:' must be 'none' or name the missed work with its link")
    return problems, fields
