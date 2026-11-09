"""PROGRESS.html: one self-contained page with the experiment history as a chart.

Written by `honestlab report` next to REPORT.md, from honestlab's own records only. No
network: no external scripts, fonts or styles. Opens in any browser by double-click.
"""
from __future__ import annotations

import html
import math

from . import core

W, H = 760, 340
PAD_L, PAD_R, PAD_T, PAD_B = 56, 112, 20, 44

TEXT = {
    "pt": {
        "title": "Progresso", "lower": "menor é melhor", "higher": "maior é melhor",
        "attempt": "Tentativa", "kept": "guardada (melhorou)", "discarded": "desfeita",
        "error": "deu erro", "best": "melhor até agora", "start": "ponto de partida",
        "known": "melhor método conhecido", "bar": "meta para contar como achado",
        "s_start": "partida", "s_known": "conhecido", "s_bar": "meta", "s_best": "melhor",
        "table": "Ver todas as tentativas em tabela", "id": "Tentativa", "result": "Resultado",
        "decision": "Decisão", "idea": "Ideia testada", "none": "Nenhuma tentativa ainda.",
        "verdict": "Veredito", "note": "Pontos azuis cheios: guardadas. Pontos cinza vazados: desfeitas. "
        "A linha azul é o melhor resultado até cada tentativa. Passe o mouse sobre um ponto para ver a ideia.",
        "dec": {"keep": "guardada", "discard": "desfeita", "error": "erro"},
        "from": "Gerado pelo honestlab a partir do registro do laboratório. Detalhes em REPORT.md.",
    },
    "en": {
        "title": "Progress", "lower": "lower is better", "higher": "higher is better",
        "attempt": "Attempt", "kept": "kept (improved)", "discarded": "undone",
        "error": "error", "best": "best so far", "start": "starting point",
        "known": "best known method", "bar": "bar to count as a finding",
        "s_start": "start", "s_known": "known", "s_bar": "bar", "s_best": "best",
        "table": "See every attempt as a table", "id": "Attempt", "result": "Result",
        "decision": "Decision", "idea": "Idea tested", "none": "No attempts yet.",
        "verdict": "Verdict", "note": "Filled blue dots: kept. Hollow gray dots: undone. "
        "The blue line is the best result up to each attempt. Hover a dot to see the idea.",
        "dec": {"keep": "kept", "discard": "undone", "error": "error"},
        "from": "Written by honestlab from the lab's records. Details in REPORT.md.",
    },
}

CSS = """
.viz-root{color-scheme:light;--surface-1:#fcfcfb;--page:#f9f9f7;--text-primary:#0b0b0b;--text-secondary:#52514e;
--muted:#898781;--grid:#e1e0d9;--axis:#c3c2b7;--series-1:#2a78d6;--series-2:#eb6834;--border:rgba(11,11,11,.10)}
@media (prefers-color-scheme:dark){:root:where(:not([data-theme="light"])) .viz-root{color-scheme:dark;
--surface-1:#1a1a19;--page:#0d0d0d;--text-primary:#f0efec;--text-secondary:#c3c2b7;--muted:#898781;--grid:#2c2c2a;
--axis:#383835;--series-1:#3987e5;--series-2:#d95926;--border:rgba(255,255,255,.10)}}
:root[data-theme="dark"] .viz-root{color-scheme:dark;--surface-1:#1a1a19;--page:#0d0d0d;--text-primary:#f0efec;
--text-secondary:#c3c2b7;--muted:#898781;--grid:#2c2c2a;--axis:#383835;--series-1:#3987e5;--series-2:#d95926;
--border:rgba(255,255,255,.10)}
html,body{margin:0}
body.viz-root{background:var(--page);color:var(--text-primary);font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif}
main{max-width:860px;margin:0 auto;padding:24px 16px 48px}
h1{font-size:22px;margin:0 0 4px}
.sub{color:var(--text-secondary);margin:0 0 16px}
.verdict{background:var(--surface-1);border:1px solid var(--border);border-radius:8px;padding:12px 14px;margin:0 0 16px}
.card{background:var(--surface-1);border:1px solid var(--border);border-radius:8px;padding:12px;position:relative}
.legend{display:flex;flex-wrap:wrap;gap:6px 18px;margin:0 0 8px;color:var(--text-secondary);font-size:13px}
.legend span{display:inline-flex;align-items:center;gap:6px}
svg{width:100%;height:auto;display:block}
.legend svg{width:auto;display:inline-block;flex:none}
svg text{fill:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}
svg .lab{fill:var(--text-secondary)}
.note{color:var(--text-secondary);font-size:13px;margin:8px 0 0}
#tip{position:absolute;pointer-events:none;background:var(--surface-1);color:var(--text-primary);border:1px solid var(--border);
border-radius:6px;padding:6px 8px;font-size:13px;max-width:280px;box-shadow:0 2px 8px rgba(0,0,0,.12);display:none}
details{margin-top:16px}
.scroll{overflow-x:auto}
.verdict,.note,td{overflow-wrap:anywhere}
table{border-collapse:collapse;width:100%;font-size:13px;margin-top:8px}
th,td{text-align:left;padding:6px 8px;border-bottom:1px solid var(--border);vertical-align:top}
td.n{font-variant-numeric:tabular-nums;white-space:nowrap}
footer{color:var(--muted);font-size:12px;margin-top:24px}
.hit{fill:transparent;cursor:pointer}
"""

JS = """
(function(){var tip=document.getElementById('tip'),card=document.querySelector('.card');
function show(e){var t=e.target;if(!t.dataset||!t.dataset.tip)return;tip.textContent='';
t.dataset.tip.split('\\n').forEach(function(l,i){var d=document.createElement('div');d.textContent=l;
if(i===0)d.style.fontWeight='600';tip.appendChild(d)});tip.style.display='block';
var r=card.getBoundingClientRect(),x=e.clientX-r.left+12,y=e.clientY-r.top+12;
if(x+290>r.width)x=Math.max(4,x-300);tip.style.left=x+'px';tip.style.top=y+'px'}
function hide(){tip.style.display='none'}
document.querySelectorAll('.hit').forEach(function(c){c.addEventListener('mousemove',show);
c.addEventListener('mouseleave',hide);c.addEventListener('focus',function(e){var b=e.target.getBoundingClientRect(),
r=card.getBoundingClientRect();show({target:e.target,clientX:b.left+b.width/2,clientY:b.top});});
c.addEventListener('blur',hide)})})();
"""


def _num(x) -> str:
    return "n/a" if x is None else f"{x:.4g}"


def _tick(x) -> str:
    return f"{x:.6g}"


def build(root, cfg, st, verdict_line: str = "") -> str:
    lang = "pt" if core.is_pt(cfg) else "en"
    L = TEXT[lang]
    exps = [e for e in core.read_ledger(root) if e.get("type") == "experiment"]
    minimize = cfg["direction"] == "minimize"
    base = st.get("baseline")
    refs = st.get("references") or {}
    known_name, known = None, None
    for n, r in refs.items():
        v = r.get("dev")
        if v is not None and (known is None or (v < known if minimize else v > known)):
            known_name, known = n, v
    fnd = cfg.get("finding") or {}
    strongest = known if known is not None and base is not None and ((known < base) if minimize else (known > base)) else base
    bar = None
    if fnd.get("min_effect") is not None and strongest is not None:
        need = float(fnd["min_effect"])
        delta = need * abs(strongest) if fnd.get("effect") == "relative" else need
        bar = strongest - delta if minimize else strongest + delta

    scored = [e for e in exps if isinstance(e.get("score"), (int, float))]
    values = [e["score"] for e in scored] + [v for v in (base, known, bar) if v is not None]
    title = html.escape(f"{L['title']}: {cfg.get('project', '')}")
    head = (f"<!doctype html><html lang=\"{'pt-BR' if lang == 'pt' else 'en'}\"><head><meta charset=\"utf-8\">"
            f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><title>{title}</title>"
            f"<style>{CSS}</style></head><body class=\"viz-root\"><main>")
    sub = f"{html.escape(cfg['metric'])}: {L['lower'] if minimize else L['higher']}"
    parts = [head, f"<h1>{title}</h1>", f"<p class=\"sub\">{sub}</p>"]
    if verdict_line:
        parts.append(f"<div class=\"verdict\"><strong>{L['verdict']}:</strong> {html.escape(verdict_line)}</div>")
    if not values:
        parts.append(f"<p>{L['none']}</p></main></body></html>")
        return "".join(parts)

    lo, hi = min(values), max(values)
    span = (hi - lo) or abs(hi) or 1.0
    raw = span * 1.16 / 4
    mag = 10 ** math.floor(math.log10(raw))
    tick = next(m * mag for m in (1, 2, 2.5, 5, 10) if m * mag >= raw)
    lo, hi = math.floor((lo - span * 0.04) / tick) * tick, math.ceil((hi + span * 0.04) / tick) * tick
    nticks = int(round((hi - lo) / tick))
    n = max(len(exps), 1)
    pw, ph = W - PAD_L - PAD_R, H - PAD_T - PAD_B

    def X(i):  # attempt number 1..n
        return PAD_L + (pw * (i - 0.5) / n)

    def Y(v):
        return PAD_T + ph * (hi - v) / (hi - lo)

    svg = [f"<svg viewBox=\"0 0 {W} {H}\" role=\"img\" aria-label=\"{html.escape(L['title'])}\">"]
    for k in range(nticks + 1):  # recessive grid on round values
        v = lo + tick * k
        y = Y(v)
        svg.append(f"<line x1=\"{PAD_L}\" x2=\"{PAD_L + pw}\" y1=\"{y:.1f}\" y2=\"{y:.1f}\" stroke=\"var(--grid)\"/>")
        svg.append(f"<text x=\"{PAD_L - 8}\" y=\"{y + 4:.1f}\" text-anchor=\"end\">{_tick(v)}</text>")
    svg.append(f"<line x1=\"{PAD_L}\" x2=\"{PAD_L + pw}\" y1=\"{PAD_T + ph}\" y2=\"{PAD_T + ph}\" stroke=\"var(--axis)\"/>")
    step = max(1, n // 10)
    for i in range(1, n + 1):
        if i == 1 or i == n or i % step == 0:
            svg.append(f"<text x=\"{X(i):.1f}\" y=\"{PAD_T + ph + 18}\" text-anchor=\"middle\">{i}</text>")
    svg.append(f"<text x=\"{PAD_L + pw / 2:.1f}\" y=\"{H - 6}\" text-anchor=\"middle\">{L['attempt']}</text>")

    labels = []

    def hline(v, text, color, dash):
        if v is None:
            return
        y = Y(v)
        svg.append(f"<line x1=\"{PAD_L}\" x2=\"{PAD_L + pw}\" y1=\"{y:.1f}\" y2=\"{y:.1f}\" stroke=\"{color}\" "
                   f"stroke-width=\"2\"{' stroke-dasharray=\"6 4\"' if dash else ''}/>")
        labels.append([y, f"{text} {_num(v)}"])

    hline(base, L["s_start"], "var(--muted)", True)
    if known is not None:
        hline(known, L["s_known"], "var(--series-2)", False)
    hline(bar, L["s_bar"], "var(--series-2)", True)

    # best-so-far step line
    best, pts = base, []
    for i, e in enumerate(exps, 1):
        if e.get("decision") == "keep" and isinstance(e.get("score"), (int, float)):
            best = e["score"]
        if best is not None:
            pts.append((X(i) - pw / n / 2, Y(best)))
            pts.append((X(i) + pw / n / 2, Y(best)))
    if pts:
        d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        svg.append(f"<path d=\"{d}\" fill=\"none\" stroke=\"var(--series-1)\" stroke-width=\"2\"/>")
        labels.append([pts[-1][1], f"{L['s_best']} {_num(best)}"])

    for i, e in enumerate(exps, 1):
        idea = (e.get("hypothesis") or "")[:200]
        dec = L["dec"].get(e.get("decision"), e.get("decision") or "")
        if isinstance(e.get("score"), (int, float)):
            x, y = X(i), Y(e["score"])
            if e.get("decision") == "keep":
                svg.append(f"<circle cx=\"{x:.1f}\" cy=\"{y:.1f}\" r=\"5\" fill=\"var(--series-1)\" "
                           f"stroke=\"var(--surface-1)\" stroke-width=\"2\"/>")
            else:
                svg.append(f"<circle cx=\"{x:.1f}\" cy=\"{y:.1f}\" r=\"4.5\" fill=\"var(--surface-1)\" "
                           f"stroke=\"var(--muted)\" stroke-width=\"2\"/>")
            tip = f"{e.get('id')}: {_num(e['score'])} ({dec})\n{idea}"
        else:
            x, y = X(i), PAD_T + ph - 8
            svg.append(f"<text x=\"{x:.1f}\" y=\"{y + 4:.1f}\" text-anchor=\"middle\" class=\"lab\">×</text>")
            tip = f"{e.get('id')}: {L['error']}\n{idea}"
        svg.append(f"<circle class=\"hit\" tabindex=\"0\" cx=\"{x:.1f}\" cy=\"{y:.1f}\" r=\"12\" "
                   f"data-tip=\"{html.escape(tip, quote=True)}\"><title>{html.escape(tip)}</title></circle>")

    labels.sort()
    for k in range(1, len(labels)):  # keep right-hand labels from overlapping
        if labels[k][0] - labels[k - 1][0] < 15:
            labels[k][0] = labels[k - 1][0] + 15
    for y, text in labels:
        svg.append(f"<text x=\"{PAD_L + pw + 8}\" y=\"{y + 4:.1f}\" class=\"lab\">{html.escape(text)}</text>")
    svg.append("</svg>")

    legend = (f"<div class=\"legend\"><span><svg width=\"14\" height=\"14\"><circle cx=\"7\" cy=\"7\" r=\"5\" "
              f"fill=\"var(--series-1)\"/></svg>{L['kept']}</span><span><svg width=\"14\" height=\"14\"><circle "
              f"cx=\"7\" cy=\"7\" r=\"4.5\" fill=\"none\" stroke=\"var(--muted)\" stroke-width=\"2\"/></svg>"
              f"{L['discarded']}</span><span><svg width=\"22\" height=\"14\"><line x1=\"0\" x2=\"22\" y1=\"7\" "
              f"y2=\"7\" stroke=\"var(--series-1)\" stroke-width=\"2\"/></svg>{L['best']}</span><span><svg "
              f"width=\"22\" height=\"14\"><line x1=\"0\" x2=\"22\" y1=\"7\" y2=\"7\" stroke=\"var(--series-2)\" "
              f"stroke-width=\"2\"/></svg>{L['known']}</span><span><svg width=\"22\" height=\"14\"><line x1=\"0\" "
              f"x2=\"22\" y1=\"7\" y2=\"7\" stroke=\"var(--series-2)\" stroke-width=\"2\" stroke-dasharray=\"6 4\"/>"
              f"</svg>{L['bar']}</span></div>")
    parts.append(f"<div class=\"card\">{legend}{''.join(svg)}<div id=\"tip\"></div></div>")
    parts.append(f"<p class=\"note\">{L['note']}</p>")
    rows = "".join(
        f"<tr><td class=\"n\">{html.escape(str(e.get('id')))}</td><td class=\"n\">{_num(e.get('score'))}</td>"
        f"<td>{html.escape(L['dec'].get(e.get('decision'), str(e.get('decision'))))}</td>"
        f"<td>{html.escape(e.get('hypothesis') or '')}</td></tr>" for e in exps)
    parts.append(f"<details><summary>{L['table']}</summary><div class=\"scroll\"><table><thead><tr><th>{L['id']}</th><th>{L['result']}"
                 f"</th><th>{L['decision']}</th><th>{L['idea']}</th></tr></thead><tbody>{rows}</tbody></table></div>"
                 f"</details>")
    parts.append(f"<footer>{L['from']}</footer></main><script>{JS}</script></body></html>")
    return "".join(parts)


def data_summary(page: str) -> dict:
    """For tests: counts of marks in a built page."""
    return {"kept": page.count('fill="var(--series-1)" stroke="var(--surface-1)"'),
            "undone": page.count('fill="var(--surface-1)" stroke="var(--muted)"'),
            "tips": page.count('class="hit"')}
