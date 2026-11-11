"""Plain-language final report (REPORT.md), built only from honestlab's own records."""

from __future__ import annotations

import re

from . import core, stats

PLACEHOLDER = "<!-- honestlab: the agent replaces this line with 3 to 5 plain sentences for the person -->"

T = {
    "pt": {
        "title": "Relatório do honestlab",
        "verdict_h": "Veredito",
        "v_found": "Encontrou: uma melhora real sobre o melhor método conhecido, confirmada em dados novos e por uma revisão independente.",
        "v_fragile": "Sinal promissor, mas frágil: há indícios de melhora, mas eles não se confirmaram com segurança.",
        "v_not_found": "Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.",
        "v_not_started": "Ainda não começou: o contrato não foi aprovado.",
        "v_event_unusual": "Incomum: na data do evento o número mudou mais do que em quase todas as datas comuns. Isso sozinho não prova que o evento foi a causa.",
        "v_event_normal": "Não mostrou efeito: mudanças desse tamanho também acontecem em datas comuns.",
        "v_event_pending": "Aprovado, ainda não medido: o teste de evento não rodou.",
        "conf_h": "Confiança",
        "plain_h": "Em palavras simples",
        "numbers_h": "Os números",
        "measure": "Medida",
        "lower": "menor é melhor", "higher": "maior é melhor",
        "start": "Ponto de partida (o que já existia)",
        "known": "Melhor método conhecido registrado",
        "best": "Melhor resultado do agente",
        "bar": "Margem combinada para contar como achado",
        "mode": "Modo",
        "mode_point": "exploração (guardou toda tentativa que pareceu melhor, mesmo sem prova; só o achado exige prova)",
        "mode_sig": "prova (só guardou tentativas cuja melhora é improvável de ser sorte)",
        "newdata": "Em dados novos (trancados até o fim)",
        "placebo_ok": "Testes falsos de {fid} (versões do teste em que um efeito real some): {names}: nenhum mostrou ganho",
        "event_ok": "Teste de evento em {date}: diferença {gap}; {k} de {n} datas falsas deram uma diferença igual ou maior (chance {p:.3g}, limite {alpha:g}). PASSOU: a mudança é incomum. Isso não prova a causa: outro fato na mesma janela também pode explicá-la",
        "event_small": "Teste de evento em {date}: diferença {gap}; {k} de {n} datas falsas deram uma diferença igual ou maior (chance {p:.3g}, limite {alpha:g}). NÃO PASSOU: a mudança é incomum, mas menor que a margem aprovada ({need})",
        "event_bad": "Teste de evento em {date}: diferença {gap}; {k} de {n} datas falsas deram uma diferença igual ou maior (chance {p:.3g}, limite {alpha:g}). NÃO PASSOU: mudanças desse tamanho também acontecem em datas comuns",
        "placebo_bad": "Teste falso '{name}' derrubou {cand}: o ganho apareceu também onde não deveria, então não veio da causa alegada",
        "newdata_line": "{cand} ({fid}) {c} contra {r} de {ref}: {pct}{better}",
        "better_w": " melhor", "worse_w": " pior",
        "ci_units": "; faixa provável da diferença: {lo} a {hi} em `{metric}`",
        "not_tested": "Atenção: o melhor resultado ({best}) é diferente do achado testado em dados novos ({cand}). {best} não foi testado em dados novos.",
        "tried_h": "O que foi tentado",
        "tried": "{n} tentativa(s): {k} guardadas (melhoraram), {d} desfeitas, {e} com erro. Todas ficam registradas.",
        "top": "Melhores ideias", "fails": "Ideias que não funcionaram (exemplos)",
        "findings_h": "Candidatos a achado",
        "next_h": "Próximo passo",
        "n_found": "Peça a alguém da área para conferir o método e teste no próximo período de dados antes de usar em decisões importantes.",
        "n_fragile": "Faça um teste para a frente: congele a previsão do próximo período e compare quando o resultado real sair. Mais dados também ajudam a decidir.",
        "n_not_found": "O melhor método conhecido continua sendo o melhor. Opções: trazer dados ou variáveis diferentes, mudar a pergunta, ou ficar com o método atual com mais confiança.",
        "n_untested": "Ainda falta a checagem: testar o melhor candidato nos dados guardados e passar pela revisão independente (o agente faz isso).",
        "n_event_unusual": "Liste os outros fatos da mesma janela e procure um dado que só o evento atinge (outro produto, outra região). Só isso separa as causas.",
        "n_event_normal": "Com estes dados não dá para ver um efeito do evento. Opções: dados mais frequentes (semanais), outra janela aprovada antes, ou aceitar que o efeito, se existe, é pequeno.",
        "n_event_pending": "Peça ao agente para rodar o teste de evento (`honestlab event`).",
        "n_not_started": "Leia a página de aprovação e, se concordar, digite `aprovar` na conversa do Claude Code (ou `honestlab freeze` num terminal nesta pasta).",
        "c_found": "Alta: passou nos dados novos com margem estatística e na revisão independente.",
        "c_found_point": "Média: passou nos dados novos, mas sem teste estatístico (o avaliador não deu resultados por item).",
        "c_frag_review": "Baixa: confirmou em dados novos, mas a revisão independente rejeitou ({why}).",
        "c_frag_untested": "Baixa: a melhora apareceu nos dados de desenvolvimento, mas não foi confirmada em dados novos.",
        "c_frag_pending": "Baixa: confirmado em dados novos, mas a revisão independente ainda não foi feita.",
        "c_found_size": "Alta de que a melhora é real (confirmada em dados novos e pela revisão). O tamanho estimado alcançou a meta, mas a faixa de incerteza começa em {low}: a melhora verdadeira pode ser um pouco menor que a meta.",
        "c_nf_holdout": "Média: {n} candidato(s) passaram nos dados de desenvolvimento, mas não se confirmaram nos dados guardados para o fim. Isso costuma ser sorte nos dados de desenvolvimento.",
        "c_appr": "Baixa: o resultado passou, mas não foi possível confirmar que foi você quem aprovou a página ({why}).",
        "appr_h": "Aprovação",
        "abl_h": "O que fez a diferença",
        "abl_intro": "Cada parte da mudança de {fid} foi desfeita sozinha e medida de novo (só nos dados de desenvolvimento). Efeito positivo quer dizer que a parte ajuda.",
        "abl_words": {"helps": "ajuda", "hurts": "atrapalha (o resultado melhora sem ela)", "no clear effect": "sem efeito claro",
                      "needed: the code fails without it": "necessária (sem ela o código não roda)",
                      "cannot be removed alone": "não dá para tirar sozinha"},
        "nov_h": "É novo?",
        "nov_known": "O método já é conhecido: {work} ({link}). O ganho vale para os seus dados, mas a ideia não é nova.",
        "nov_similar": "Existe trabalho parecido: {work} ({link}). O que este resultado acrescenta está em {path}.",
        "nov_nothing": "Nada parecido foi encontrado. Isso não prova que é novo: peça a alguém da área para conferir.",
        "nov_search": "Busca: {q} buscas em {n} fontes ({sources}), em {date}.",
        "nov_missed": "O revisor independente achou um trabalho que a busca não viu: {missed}.",
        "why_no_evidence": "nenhuma prova foi registrada com a aprovação",
        "why_no_transcript": "o registro da conversa não pôde ser lido",
        "why_no_message": "a sua mensagem de confirmação não está no registro da conversa",
        "appr_chat_verified": "feita por você na conversa (confirmada pela sua própria mensagem).",
        "appr_chat_unverified": "ATENÇÃO: registrada como feita na conversa, mas a sua mensagem de confirmação não foi encontrada.",
        "appr_terminal": "feita por você num terminal.",
        "appr_unknown": "ATENÇÃO: o modo de aprovação não foi registrado.",
        "c_nf_many": "Média: {n} tentativas e nenhuma chegou à margem combinada.",
        "c_nf_few": "Baixa: só {n} tentativas; mais tentativas poderiam encontrar algo.",
        "labs_h": "Como isso se compara ao que os laboratórios de IA fazem",
        "labs": [
            ("Uma pergunta com uma medida que o computador calcula sozinho", "O \"avaliador\" automático do FunSearch e do AlphaEvolve (DeepMind)"),
            ("Métodos conhecidos registrados antes de começar", "Comparar com o melhor resultado já publicado, não com um ponto de partida fraco"),
            ("O agente muda uma coisa por vez e o honestlab mede", "O laço gerar, avaliar e guardar o melhor, com milhares de tentativas"),
            ("Mudanças piores são desfeitas, mas ficam registradas", "O banco de programas com pontuação, inclusive os que falharam"),
            ("Dados trancados, usados só no fim", "Separar desenvolvimento de teste para não se enganar com sorte ou trapaça do avaliador"),
            ("Revisão por alguém que não fez o trabalho", "Verificação independente: especialistas, provadores formais como o Lean"),
        ],
        "labs_cols": ("O que o honestlab fez", "Equivalente nos laboratórios"),
        "integrity": "Registro: {msg}.",
        "none": "nenhum",
    },
    "en": {
        "title": "honestlab report",
        "verdict_h": "Verdict",
        "v_found": "Found: a real improvement over the best known method, confirmed on new data and by an independent review.",
        "v_fragile": "Promising but fragile: there are signs of improvement, but they were not confirmed with confidence.",
        "v_not_found": "Not found: no attempt beat the best known method by the agreed margin.",
        "v_not_started": "Not started: the contract has not been approved.",
        "v_event_unusual": "Unusual: at the event date the number moved more than on almost every ordinary date. This alone does not prove that the event caused it.",
        "v_event_normal": "No effect shown: changes this large also happen on ordinary dates.",
        "v_event_pending": "Approved, not yet measured: the event test has not run.",
        "conf_h": "Confidence",
        "plain_h": "In plain words",
        "numbers_h": "The numbers",
        "measure": "Measure",
        "lower": "lower is better", "higher": "higher is better",
        "start": "Starting point (what already existed)",
        "known": "Best known method registered",
        "best": "Agent's best result",
        "bar": "Agreed margin to count as a finding",
        "mode": "Mode",
        "mode_point": "exploration (kept every attempt that looked better, even without proof; only a finding needs proof)",
        "mode_sig": "proof (kept only attempts whose gain is unlikely to be luck)",
        "newdata": "On new data (locked until the end)",
        "placebo_ok": "Fake tests for {fid} (versions of the test where a real effect vanishes): {names}: none showed a gain",
        "event_ok": "Event test at {date}: gap {gap}; {k} of {n} fake dates gave a gap as large or larger (chance {p:.3g}, bar {alpha:g}). PASSED: the change is unusual. This does not prove the cause: another event in the same window can explain it too",
        "event_small": "Event test at {date}: gap {gap}; {k} of {n} fake dates gave a gap as large or larger (chance {p:.3g}, bar {alpha:g}). NOT PASSED: the change is unusual but smaller than the approved margin ({need})",
        "event_bad": "Event test at {date}: gap {gap}; {k} of {n} fake dates gave a gap as large or larger (chance {p:.3g}, bar {alpha:g}). NOT PASSED: changes this large also happen on ordinary dates",
        "placebo_bad": "Fake test '{name}' sank {cand}: the gain also appeared where it should not, so it did not come from the claimed cause",
        "newdata_line": "{cand} ({fid}) {c} against {r} for {ref}: {pct}{better}",
        "better_w": " better", "worse_w": " worse",
        "ci_units": "; likely range of the difference: {lo} to {hi} in `{metric}`",
        "not_tested": "Note: the best result ({best}) is not the finding tested on new data ({cand}). {best} was not tested on new data.",
        "tried_h": "What was tried",
        "tried": "{n} attempt(s): {k} kept (improved), {d} undone, {e} errors. All of them are recorded.",
        "top": "Best ideas", "fails": "Ideas that did not work (examples)",
        "findings_h": "Finding candidates",
        "next_h": "Next step",
        "n_found": "Ask someone from the field to check the method, and test it on the next period of data before using it for important decisions.",
        "n_fragile": "Run a forward test: freeze the forecast for the next period and compare when the real result is out. More data also helps decide.",
        "n_not_found": "The best known method is still the best. Options: bring different data or variables, change the question, or keep the current method with more confidence.",
        "n_untested": "The check is still missing: test the best candidate on the data kept for the end and get the independent review (the agent does this).",
        "n_event_unusual": "List the other events in the same window and look for data that only the event touches (another product, another region). Only that separates the causes.",
        "n_event_normal": "With this data no effect of the event is visible. Options: more frequent data (weekly), another window approved in advance, or accept that any effect is small.",
        "n_event_pending": "Ask the agent to run the event test (`honestlab event`).",
        "n_not_started": "Read the approval page and, if you agree, type `approve` in the Claude Code chat (or `honestlab freeze` in a terminal in this folder).",
        "c_found": "High: it held on new data with a statistical margin and passed the independent review.",
        "c_found_point": "Medium: it held on new data, but without a statistical test (the evaluator gave no per-item results).",
        "c_frag_review": "Low: confirmed on new data, but the independent review rejected it ({why}).",
        "c_frag_untested": "Low: the improvement showed up on development data but was not confirmed on new data.",
        "c_frag_pending": "Low: confirmed on new data, but the independent review has not been done yet.",
        "c_found_size": "High that the improvement is real (confirmed on new data and by the review). Its estimated size reached the margin, but the uncertainty range starts at {low}: the true improvement may be somewhat smaller than the margin.",
        "c_nf_holdout": "Medium: {n} candidate(s) passed on the development data but did not hold on the data kept for the end. That is usually luck on the development data.",
        "c_appr": "Low: the result passed, but it could not be confirmed that you approved the page ({why}).",
        "appr_h": "Approval",
        "abl_h": "What made the difference",
        "abl_intro": "Each part of {fid}'s change was undone alone and measured again (development data only). A positive effect means the part helps.",
        "abl_words": {"helps": "helps", "hurts": "hurts (the result is better without it)", "no clear effect": "no clear effect",
                      "needed: the code fails without it": "needed (the code does not run without it)",
                      "cannot be removed alone": "cannot be removed alone"},
        "nov_h": "Is it new?",
        "nov_known": "The method is already known: {work} ({link}). The gain holds on your data, but the idea is not new.",
        "nov_similar": "Similar work exists: {work} ({link}). What this result adds is in {path}.",
        "nov_nothing": "Nothing similar was found. That does not prove it is new: ask someone in the field to check.",
        "nov_search": "Search: {q} queries in {n} sources ({sources}), on {date}.",
        "nov_missed": "The independent reviewer found work the search missed: {missed}.",
        "why_no_evidence": "no evidence was recorded with the approval",
        "why_no_transcript": "the session transcript could not be read",
        "why_no_message": "your confirmation message is not in the session transcript",
        "appr_chat_verified": "by you in the chat (confirmed by your own message).",
        "appr_chat_unverified": "WARNING: recorded as done in the chat, but your confirmation message was not found.",
        "appr_terminal": "by you in a terminal.",
        "appr_unknown": "WARNING: how the page was approved was not recorded.",
        "c_nf_many": "Medium: {n} attempts and none reached the agreed margin.",
        "c_nf_few": "Low: only {n} attempts; more attempts could find something.",
        "labs_h": "How this compares with what AI labs do",
        "labs": [
            ("A question with a measure the computer computes by itself", "The automatic \"evaluator\" in FunSearch and AlphaEvolve (DeepMind)"),
            ("Known methods registered before starting", "Comparing with the best published result, not with a weak starting point"),
            ("The agent changes one thing at a time and honestlab measures it", "The generate, evaluate, keep-the-best loop, over thousands of attempts"),
            ("Worse changes are undone but recorded", "The scored program database, failures included"),
            ("Locked data, used only at the end", "Separating development from testing so luck or evaluator tricks do not fool you"),
            ("Review by someone who did not do the work", "Independent verification: experts, formal provers such as Lean"),
        ],
        "labs_cols": ("What honestlab did", "Equivalent in the labs"),
        "integrity": "Record: {msg}.",
        "none": "none",
    },
}


def _fmt(x):
    return "n/a" if x is None else f"{x:.4g}"


def _strongest(cfg, st, split):
    base = st.get("baseline") if split == "dev" else st.get("baseline_holdout")
    cands = [("baseline", base)] + [(n, r.get(split)) for n, r in (st.get("references") or {}).items()]
    cands = [c for c in cands if c[1] is not None]
    if not cands:
        return None, None
    pick = min if cfg["direction"] == "minimize" else max
    return pick(cands, key=lambda c: c[1])


def novelty_text(L, f, path) -> str:
    """One paragraph on prior work, from what `honestlab finding verify` recorded."""
    pw = f.get("prior_work") or {}
    if not pw.get("novelty"):
        return ""
    closest = pw.get("closest") or {}
    key = {"known": "nov_known", "similar": "nov_similar"}.get(pw["novelty"], "nov_nothing")
    parts = [L[key].format(work=closest.get("work", "?"), link=closest.get("link", "?"), path=path),
             L["nov_search"].format(q=pw.get("queries"), n=len(pw.get("sources") or []),
                                    sources=", ".join(pw.get("sources") or []), date=pw.get("date"))]
    rr = f.get("review_rerun") or {}
    if rr.get("found_missed"):
        parts.append(L["nov_missed"].format(missed=rr.get("missed")))
    return " ".join(parts)


def build(root, cfg, st):
    L = T["pt" if core.is_pt(cfg) else "en"]
    led = core.read_ledger(root)
    exps = [e for e in led if e.get("type") == "experiment"]
    finds = {}
    for e in led:
        if e.get("type") == "finding":
            finds.setdefault(e["id"], {}).update({k: v for k, v in e.items() if v is not None})
    fnd = cfg["finding"]
    ref_name, ref_dev = _strongest(cfg, st, "dev")
    pre = "baseline-dev" if ref_name == "baseline" else f"ref-{ref_name}-dev"
    ref_sample = core.load_sample(root, pre)
    meets_dev = []
    for e in exps:
        smp = core.load_sample(root, f"{e['id']}-dev")
        if smp and ref_sample and stats.meets(stats.compare(smp, ref_sample, cfg["direction"], float(fnd["alpha"]),
                                                                  measure=core.measure_fn(root, cfg), block=core.block_size(cfg)), fnd):
            meets_dev.append(e["id"])

    # verdict
    conf, next_key = "", None
    evs = [e for e in led if e.get("type") == "event_test" and e.get("rank")]
    if not st.get("frozen") and not exps and not evs:
        verdict = "not_started"
    elif cfg.get("event") and not exps and not finds:
        verdict = ("event_unusual" if evs[-1].get("passed") else "event_normal") if evs else "event_pending"
    elif any(f.get("status") == "verified" for f in finds.values()):
        verdict = "found"
        f = next(f for f in finds.values() if f.get("status") == "verified")
        hc = f.get("holdout_comparison") or {}
        conf = L["c_found"] if hc.get("lo") is not None else L["c_found_point"]
        # The CI proves the improvement is real (above zero); say so when it does not also guarantee the margin.
        lo, eff, rel = hc.get("lo"), hc.get("effect"), hc.get("rel")
        need = fnd.get("min_effect")
        if lo is not None and need is not None:
            lo_in_bar_units = lo if fnd.get("effect", "absolute") == "absolute" else (lo * rel / eff if eff else None)
            if lo_in_bar_units is not None and lo_in_bar_units < float(need):
                show = (f"{lo_in_bar_units * 100:.1f}%" if fnd.get("effect") == "relative" else f"{lo_in_bar_units:.4g}")
                conf = L["c_found_size"].format(low=show.replace(".", ",") if core.is_pt(cfg) else show)
    elif any(f.get("holdout_confirmed") for f in finds.values()):
        verdict = "fragile"
        f = next(f for f in finds.values() if f.get("holdout_confirmed"))
        if f.get("status") == "rejected":
            why = "review REJECT"
            fid = next(k for k, v in finds.items() if v is f)
            rv = root / core.lab_rel(cfg, "findings", fid, "review.md")
            if rv.exists():
                m = re.search(r"##\s*Strongest objection\s*\n+(.+?)(\n##|\nVerdict:)", rv.read_text(encoding="utf-8"), re.S)
                if m and m.group(1).strip():
                    why = m.group(1).strip().splitlines()[0][:220]
            conf = L["c_frag_review"].format(why=why)
        else:
            conf = L["c_frag_pending"]
    else:
        # candidates already checked on the held-out data and not confirmed there
        failed = [f for f in finds.values()
                  if not f.get("holdout_confirmed") and (f.get("holdout_comparison") or f.get("status") == "failed-holdout")]
        tested = {f.get("best_id") for f in failed}
        untested = [e for e in meets_dev if e not in tested]
        if untested:
            verdict, conf, next_key = "fragile", L["c_frag_untested"], "n_untested"
        elif failed:
            verdict = "not_found"
            conf = L["c_nf_holdout"].format(n=len(failed))
        else:
            verdict = "not_found"
            conf = (L["c_nf_many"] if len(exps) >= 10 else L["c_nf_few"]).format(n=len(exps))

    appr, appr_detail = core.verify_approval(root)
    if verdict == "found" and appr in ("chat-unverified", "unknown"):
        verdict, conf = "fragile", L["c_appr"].format(why=L.get("why_" + appr_detail, appr_detail or "-"))
    lines = [f"# {L['title']}: {cfg.get('project')}", "",
             f"## {L['verdict_h']}", "", f"**{L['v_' + verdict]}**", ""]
    if conf:
        lines += [f"**{L['conf_h']}:** {conf}", ""]
    if appr != "none":
        lines += [f"**{L['appr_h']}:** {L['appr_' + appr.replace('-', '_')]}", ""]
    shown = next((f for f in finds.values() if f.get("status") == "verified"), None) or \
        next((f for f in finds.values() if f.get("prior_work")), None)
    if shown:
        fid = next(k for k, v in finds.items() if v is shown)
        nov = novelty_text(L, shown, core.lab_rel(cfg, "findings", fid, "literature.md"))
        if nov:
            lines += [f"**{L['nov_h']}** {nov}", ""]
    lines += [f"## {L['plain_h']}", "", PLACEHOLDER, ""]

    # numbers
    direction = L["lower"] if cfg["direction"] == "minimize" else L["higher"]
    bar = fnd.get("min_effect")
    bar_txt = (f"{float(bar) * 100:.3g}%" if fnd.get("effect") == "relative" else f"{bar} {cfg['metric']}") if bar is not None else "n/a"
    best = st.get("best")
    gap = ""
    if best is not None and ref_dev:
        g = (ref_dev - best) / abs(ref_dev) if cfg["direction"] == "minimize" else (best - ref_dev) / abs(ref_dev)
        gap = f" ({g * 100:+.1f}% vs {ref_name})"
    lines += [f"## {L['numbers_h']}", "",
              f"- {L['measure']}: `{cfg['metric']}` ({direction})",
              f"- {L['start']}: {_fmt(st.get('baseline'))}",
              f"- {L['known']}: {ref_name or L['none']} = {_fmt(ref_dev)}",
              f"- {L['best']}: {_fmt(best)} ({st.get('best_id')}){gap}",
              f"- {L['bar']}: {bar_txt}",
              f"- {L['mode']}: {L['mode_point'] if cfg.get('keep_rule') == 'point' else L['mode_sig']}"]
    tested = []
    for fid, f in sorted(finds.items()):
        hc = f.get("holdout_comparison")
        if hc:
            ref = f.get("holdout_reference") or f.get("reference") or "baseline"
            mine = core.load_sample(root, f"{fid}-holdout") or {}
            theirs = (core.load_sample(root, f"{fid}-reference-holdout")  # measured again next to the candidate
                      or core.load_sample(root, "baseline-holdout" if ref == "baseline" else f"ref-{ref}-holdout") or {})
            rel = hc.get("rel") or 0
            pct = f"{abs(rel) * 100:.1f}%" + (L["better_w"] if rel >= 0 else L["worse_w"])
            if mine.get("score") is not None and theirs.get("score") is not None:
                txt = L["newdata_line"].format(cand=f.get("best_id"), fid=fid, c=_fmt(mine["score"]),
                                               r=_fmt(theirs["score"]), ref=ref, pct=pct, better="").rstrip()
            else:
                txt = f"{f.get('best_id')} ({fid}) vs {ref}: {pct}"
            if hc.get("lo") is not None:
                txt += L["ci_units"].format(lo=_fmt(hc.get("lo")), hi=_fmt(hc.get("hi")), metric=cfg["metric"])
            lines.append(f"- {L['newdata']}: {txt}")
            tested.append(f.get("best_id"))
    for fid, f in sorted(finds.items()):
        if f.get("placebos"):
            lines.append("- " + L["placebo_ok"].format(fid=fid, names=", ".join(sorted(f["placebos"]))))
    for e in led:
        if e.get("type") == "event_test" and e.get("rank"):
            r = e["rank"]
            key = "event_ok" if e.get("passed") else ("event_small" if e.get("too_small") else "event_bad")
            lines.append("- " + L[key].format(
                date=e.get("date"), gap=_fmt(e.get("gap")), k=r["as_large"], n=r["n_fakes"], p=r["p"],
                alpha=e.get("alpha") or 0.05, need=e.get("min_effect")))
        if e.get("type") == "placebo_failed":
            lines.append("- " + L["placebo_bad"].format(name=e.get("placebo"), cand=e.get("id")))
    if tested and st.get("best_id") not in tested:
        lines.append(f"- {L['not_tested'].format(best=st.get('best_id'), cand=', '.join(tested))}")
    lines.append("")

    # tried
    n = len(exps)
    k = sum(e.get("decision") == "keep" for e in exps)
    d = sum(e.get("decision") == "discard" for e in exps)
    er = sum(e.get("decision") == "error" for e in exps)
    lines += [f"## {L['tried_h']}", "", L["tried"].format(n=n, k=k, d=d, e=er), ""]
    scored = [e for e in exps if e.get("score") is not None]
    rev = cfg["direction"] == "maximize"
    top = sorted(scored, key=lambda e: e["score"], reverse=rev)[:3]
    if top:
        lines.append(f"**{L['top']}:**")
        lines += [f"- {e['id']} ({_fmt(e['score'])}, {e['decision']}): {e.get('hypothesis', '')}" for e in top]
        lines.append("")
    fails = [e for e in scored if e.get("decision") == "discard" and e.get("best_before") is not None]
    fails = sorted(fails, key=lambda e: abs(e["score"] - e["best_before"]), reverse=True)[:3]
    if fails:
        lines.append(f"**{L['fails']}:**")
        lines += [f"- {e['id']} ({_fmt(e['score'])} vs {_fmt(e['best_before'])}): {e.get('hypothesis', '')}" for e in fails]
        lines.append("")
    if finds:
        lines += [f"## {L['findings_h']}", ""]
        lines += [f"- {fid}: {f.get('status')}: {f.get('claim', '')}" for fid, f in sorted(finds.items())]
        lines.append("")
    abl = [e for e in led if e.get("type") == "ablation"]
    if abl:
        e = abl[-1]
        lines += [f"## {L['abl_h']}", "", L["abl_intro"].format(fid=e.get("finding")), ""]
        order = {"helps": 0, "needed: the code fails without it": 1, "hurts": 2, "cannot be removed alone": 3,
                 "no clear effect": 4}
        for r in sorted(e.get("parts", []), key=lambda r: (order.get(r.get("verdict"), 5), -(r.get("effect") or 0))):
            eff = f" ({_fmt(r['effect'])})" if r.get("effect") is not None else ""
            lines.append(f"- {r['part']}: {L['abl_words'].get(r.get('verdict'), r.get('verdict'))}{eff}")
        lines.append("")
    lines += [f"## {L['next_h']}", "", L[next_key or ("n_" + verdict)], ""]
    c1, c2 = L["labs_cols"]
    lines += [f"## {L['labs_h']}", "", f"| {c1} | {c2} |", "|---|---|"]
    lines += [f"| {a} | {b} |" for a, b in L["labs"]]
    ok, msg = core.verify_ledger(root)
    lines += ["", "---", L["integrity"].format(msg=msg), ""]
    return "\n".join(lines), verdict


def keep_plain_words(old: str, new: str) -> str:
    """Carry over the agent's plain-words paragraph, but only if the verdict has not changed."""
    vo = re.search(r"\n\*\*(.+?)\*\*\n", old)
    vn = re.search(r"\n\*\*(.+?)\*\*\n", new)
    if not (vo and vn and vo.group(1) == vn.group(1)):
        return new
    m = re.search(r"## (?:Em palavras simples|In plain words)\n\n(.*?)\n\n## ", old, re.S)
    if m and PLACEHOLDER not in m.group(1) and m.group(1).strip():
        return new.replace(PLACEHOLDER, m.group(1).strip(), 1)
    return new
