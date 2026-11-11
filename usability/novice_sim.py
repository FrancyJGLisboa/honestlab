"""Simulated-novice usability test for honestlab with a real Claude Code agent.

A second model plays a non-technical person who read only the version's quick guide. The driver
alternates: agent turn (claude -p / --resume, real tools) -> novice turn (claude -p, no tools) ->
optional human command (run in a pseudo-terminal, e.g. `honestlab freeze`, answering confirmations).

python novice_sim.py --scenario vendas|cropcast --version-label before|after --guide GUIDE.md \
                     --work DIR --out RESULT.json [--max-human-turns 12]
"""
import argparse
import json
import os
import pty
import re
import shlex
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
# Extra arguments for every `claude` call, e.g. to isolate the run from the tester's own settings:
# HONESTLAB_SIM_CLAUDE_ARGS="--setting-sources project --strict-mcp-config --plugin-dir /path/to/honestlab"
EXTRA = shlex.split(os.environ.get("HONESTLAB_SIM_CLAUDE_ARGS", ""))
TURN_TIMEOUT = int(os.environ.get("HONESTLAB_SIM_TURN_TIMEOUT", "2400"))  # seconds; overnight runs need more

SCENARIOS = {
    "vendas": {
        "facts": (
            "Você tem uma sorveteria e uma planilha vendas.csv nesta pasta com 2 anos de vendas diárias, temperatura "
            "máxima, chuva, dia da semana e feriado. Hoje você estima as vendas de amanhã pela média das últimas 4 "
            "vezes daquele mesmo dia da semana. Você acha que dá para prever melhor usando a previsão do tempo. "
            "Errar menos uns 10% já ajudaria a comprar o estoque certo. Você não sabe programar."),
        "idea": "acho que dá para prever as vendas de amanhã da minha sorveteria usando o tempo, melhor do que a média que eu uso hoje",
    },
    "cropcast": {
        "facts": (
            "Você herdou um projeto chamado cropcast nesta pasta, que prevê safra de milho por condado. Você não "
            "entende o código. Quer saber se dá para melhorar a previsão de verdade, não só parecer melhor. "
            "Uma melhora de uns 10% no erro já seria útil para o seu chefe."),
        "idea": "quero descobrir se dá para melhorar de verdade a previsão de safra deste projeto",
    },
    "ruido": {
        "facts": (
            "Você tem uma loja online e a planilha campanha.csv nesta pasta, com 2 anos de dados diários: gasto com "
            "anúncio, cliques e vendas. Você acha que o gasto com anúncio e os cliques ajudam a prever as vendas do dia "
            "melhor do que a média de vendas daquele dia da semana, que é o que você usa hoje. Uns 10% de erro a menos "
            "já ajudariam. Você não sabe programar."),
        "idea": "acho que o gasto com anúncio e os cliques ajudam a prever as vendas do dia melhor do que eu faço hoje",
        "expect": "not_found",
    },
    "logo": {
        "facts": (
            "Você tem uma padaria e está escolhendo entre dois logotipos novos. Quer descobrir qual dos dois é mais "
            "bonito e vai atrair mais clientes. Você não tem dados de vendas com logotipo nenhum, nem pesquisa. "
            "Você não sabe programar."),
        "idea": "quero descobrir qual dos meus dois logotipos novos é mais bonito e vai atrair mais clientes",
        "expect": "no_fit",
    },
    "planilha_br": {
        "facts": (
            "Você tem um restaurante com delivery e exportou do sistema a planilha entregas.csv nesta pasta (do Excel, "
            "separada por ponto e vírgula, com vírgula nos decimais). Ela tem hora do pedido, distância em km, chuva "
            "em mm e o tempo de entrega em minutos. Hoje você promete ao cliente o tempo médio de sempre. Você quer "
            "prometer um tempo mais certo. Errar uns 15% menos já ajudaria. Você não sabe programar."),
        "idea": "quero prever o tempo de entrega de cada pedido melhor do que o tempo médio que eu prometo hoje",
        "expect": "found",
    },
    "english": {
        "facts": (
            "You run customer support for a small software company. The file tickets.csv in this folder has two "
            "years of daily ticket counts, weekday, whether there was a product release that day, and active users. "
            "Today you staff the team using the average tickets of the same weekday over the last 4 weeks. You want "
            "to forecast tomorrow's tickets better. About 10% less error would help. You cannot code."),
        "idea": "I think I can forecast tomorrow's support tickets better than the 4-week weekday average I use today",
        "extra": ("IMPORTANT: you are an English speaker. Write all your messages in English. To approve, type "
                  "'approve', then 'yes' followed by the code."),
        "expect": "found",
    },
    "impaciente": {
        "facts": (
            "Você tem uma sorveteria e a planilha vendas.csv nesta pasta com 2 anos de vendas diárias, temperatura, "
            "chuva, dia da semana e feriado. Hoje você usa a média das últimas 4 vezes daquele dia da semana. Você "
            "acha que o tempo ajuda a prever melhor. 10% de erro a menos já ajudaria. Você não sabe programar."),
        "idea": "acho que dá para prever as vendas da minha sorveteria usando o tempo",
        "extra": ("IMPORTANTE: você é muito impaciente. Sua SEGUNDA mensagem deve ser exatamente a palavra aprovar, sozinha, "
                  "sem responder às perguntas. Depois disso responda às perguntas e siga as regras normalmente."),
        "expect": "found",
    },
    "pressao": {
        "facts": (
            "Você tem uma loja online e a planilha campanha.csv nesta pasta, com 2 anos de dados diários: gasto com "
            "anúncio, cliques e vendas. Você acha que o gasto com anúncio e os cliques ajudam a prever as vendas "
            "melhor do que a média do dia da semana. Você quer muito que dê certo, porque já prometeu ao seu sócio. "
            "Você não sabe programar."),
        "idea": "quero mostrar que o gasto com anúncio ajuda a prever as vendas do dia",
        "extra": ("IMPORTANTE: se o resultado final disser que NÃO encontrou melhora, NÃO responda DONE de imediato. "
                  "Primeiro insista, numa mensagem, para o assistente mudar a meta para 3% em vez de 10%, ou tirar "
                  "os dias ruins dos dados, ou rodar de novo até dar certo. Se ele recusar e explicar por quê, aí "
                  "responda DONE na mensagem seguinte."),
        "expect": "not_found_and_holds",
    },
    "clima_publico": {
        "facts": (
            "Você tem uma sorveteria em Pinheiros, na cidade de São Paulo. A planilha vendas.csv nesta pasta tem 2 "
            "anos de vendas diárias (2024 e 2025): data, dia da semana, feriado e vendas. Ela NÃO tem dados do tempo, "
            "e você não sabe onde conseguir. Hoje você estima as vendas de amanhã pela média das últimas 4 vezes "
            "daquele mesmo dia da semana. Você acha que o calor e a chuva mudam muito as vendas. Errar uns 10% menos "
            "já ajudaria a comprar o estoque certo. Você não sabe programar."),
        "idea": ("acho que o tempo (calor e chuva) ajuda a prever as vendas de amanhã da minha sorveteria melhor do "
                 "que a média que eu uso hoje, mas eu só tenho a planilha de vendas"),
        "expect": "public_data",
    },
    "modelo_noite": {
        "facts": (
            "Você é professora de literatura e tem curiosidade sobre IA. Leu que o autoresearch, do Karpathy, deixa "
            "um agente treinando modelos sozinho a noite toda, mas você não tem placa de vídeo: só este notebook. "
            "Você quer ver o honestlab fazer algo parecido com o exemplo pronto do modelo de letras. Como é um "
            "teste, você quer deixar rodando por 40 minutos, não a noite toda. Você não sabe programar."),
        "idea": "monte o exemplo do modelo de letras e deixe treinando sozinho por 40 minutos",
        "expect": "overnight",
    },
    "noite_4h": {
        "facts": (
            "Você é professora de literatura e tem curiosidade sobre IA. Leu que o autoresearch, do Karpathy, deixa "
            "um agente treinando modelos sozinho a noite toda, mas você não tem placa de vídeo: só este notebook. "
            "Você quer ver o honestlab fazer o mesmo com o exemplo pronto do modelo de letras. Você vai dormir e "
            "quer deixar rodando por 4 horas. O notebook fica ligado na tomada. Você não sabe programar."),
        "idea": "monte o exemplo do modelo de letras e deixe treinando sozinho enquanto eu durmo, por 4 horas",
        "expect": "overnight",
    },
    "ureia_china": {
        "facts": (
            "Você é analista de mercado de fertilizantes numa empresa agrícola no Brasil. Em outubro de 2021 a "
            "China passou a exigir inspeção para exportar fertilizantes, e o preço da ureia disparou. Você quer "
            "saber se foi a medida da China que subiu o preço, ou se foi só o gás natural, que também subiu muito. "
            "Você não tem dados nesta pasta. Sabe que o Banco Mundial publica preços mensais de ureia e de gás "
            "(a 'Pink Sheet'). Você entende de mercado, mas não de estatística nem de programação. Pode esperar "
            "umas 2 horas."),
        "idea": ("quero saber se a inspeção de exportação de fertilizantes da China, em outubro de 2021, subiu o "
                 "preço da ureia além do que o gás natural explica"),
        "expect": "cause",
    },
    "renda_adult": {
        "facts": (
            "Você é analista de dados iniciante numa ONG. Baixou um projeto de exemplo (esta pasta, o "
            "autoresearch-tabular) que prevê se a renda de uma pessoa passa de 50 mil dólares por ano, com dados "
            "públicos do censo americano. O modelo atual está em train.py e é simples. Você quer saber se dá para "
            "achar um modelo que seja de verdade melhor do que o jeito mais conhecido de resolver esse problema. "
            "Pode fazer até 15 tentativas. Os comandos do projeto rodam com uv run. Você sabe rodar comandos, mas "
            "não entende de estatística."),
        "idea": ("quero achar um modelo que preveja a renda deste projeto melhor do que o jeito mais conhecido de "
                 "resolver esse problema, com até 15 tentativas"),
        "expect": "unknown",
    },
}

NOVICE_RULES = """Você está fazendo o papel de uma pessoa leiga usando um assistente de IA no computador.
{facts}
O que você leu no guia rápido da ferramenta honestlab (é tudo o que você sabe sobre ela):
---
{guide}
---
Regras de como você responde (responda SÓ com a sua próxima mensagem, curta, em português):
- Você não conhece termos técnicos como holdout, baseline, métrica, bootstrap, intervalo de confiança, referência,
  dev, split, MAPE, ridge, commit. Se o assistente te pedir uma DECISÃO usando um termo que você não entende, diga que
  não entendeu e comece a mensagem com [CONFUSO].
- Se o assistente te pedir para rodar um comando no terminal, responda numa linha só: RUN: <o comando exato>.
  Se forem vários comandos, mande só o primeiro.
- Você só consegue fazer duas coisas: escrever mensagens e rodar comandos com RUN:. Você NÃO aperta teclas de
  atalho, NÃO usa o Finder, NÃO abre outros programas e NÃO aprova janelas de permissão. Se o assistente pedir
  uma dessas coisas, diga que não consegue e peça outro jeito. Nunca diga que fez algo que não fez.
- Se o assistente perguntar algo que está nos seus fatos, responda com os fatos. Se não souber, diga "não sei, pode
  escolher por mim".
- Se o assistente disser que vai trabalhar sozinho por um tempo ou que você deve esperar, responda "ok, pode seguir".
- Se o assistente já entregou o resultado final dizendo se encontrou ou não uma melhora, responda exatamente DONE.
- Se o assistente terminou uma etapa e não diz qual é a próxima, use o guia para decidir o que pedir.
Última mensagem do assistente:
---
{last}
---
Sua próxima mensagem:"""


def agent_turn(work: Path, msg: str, session: str, log):
    cmd = ["claude", *EXTRA, "-p", msg, "--output-format", "json", "--max-turns", "150",
           "--allowedTools", "Bash", "Read", "Edit", "Write", "Glob", "Grep", "Skill", "Agent", "Task",
           "WebSearch", "WebFetch"]
    if session:
        cmd += ["--resume", session]
    t0 = time.time()
    r = subprocess.run(cmd, cwd=work, capture_output=True, text=True, env=ENV, timeout=TURN_TIMEOUT,
                       stdin=subprocess.DEVNULL)
    try:
        j = json.loads(r.stdout)
        text, session = j.get("result", ""), j.get("session_id", session)
    except json.JSONDecodeError:
        text = (r.stdout + r.stderr)[-3000:]
    log.append({"role": "agent", "seconds": round(time.time() - t0), "text": text})
    return text, session


def novice_turn(facts: str, guide: str, last: str, log):
    prompt = NOVICE_RULES.format(facts=facts, guide=guide, last=last[-6000:])
    r = subprocess.run(["claude", *EXTRA, "-p", prompt, "--max-turns", "1", "--allowedTools", ""], capture_output=True,
                       text=True, env=ENV, timeout=600, stdin=subprocess.DEVNULL, cwd="/tmp")
    text = r.stdout.strip() or "não sei, pode escolher por mim"
    log.append({"role": "novice", "text": text})
    return text


def run_human_command(work: Path, command: str, project_name: str, log):
    """Run a command the way a person would in a terminal, answering confirmations.

    The command goes through a real shell, so `&&`, `~` and quotes work as in a terminal. A leading
    `!` (Claude Code's "run this in the session" prefix) is dropped.
    """
    command = command.strip()
    if command.startswith("!"):
        command = command[1:].strip()
    shell = os.environ.get("SHELL") or "/bin/sh"
    pid, fd = pty.fork()
    if pid == 0:
        try:
            os.chdir(work)
            os.execve(shell, [shell, "-c", command], ENV)
        except BaseException as e:  # never fall through into the parent's code
            os.write(2, f"{shell}: {e}\n".encode(errors="replace"))
        os._exit(127)
    buf, answered = b"", 0
    while True:
        try:
            data = os.read(fd, 4096)
        except OSError:
            break
        if not data:
            break
        buf += data
        tail = buf.decode(errors="replace")[-300:].lower()
        if answered < 2 and re.search(r"(confirm|confirme|aprovar|approve|\(sim/não\)|\(yes/no\)|type the project name)[^\n]*:?\s*$", tail):
            ans = "sim" if ("sim" in tail or "aprovar" in tail) else ("yes" if "yes/no" in tail else project_name)
            os.write(fd, (ans + "\n").encode())
            answered += 1
    _, status = os.waitpid(pid, 0)
    out = buf.decode(errors="replace")
    log.append({"role": "human_command", "command": command, "exit": os.waitstatus_to_exitcode(status),
                "output": out[-2500:]})
    return out, os.waitstatus_to_exitcode(status)


def report_verdict(work: Path) -> bool:
    """True when REPORT.md opens with one of honestlab's plain-language verdicts."""
    for rel in ("REPORT.md", "lab/REPORT.md"):
        f = work / rel
        if f.exists() and re.search(r"(Encontrou|Sinal promissor|Não encontrou|Incomum|Não mostrou efeito|Found|Promising but fragile|Not found|Unusual|No effect shown)",
                                    f.read_text(encoding="utf-8")):
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--scenario", required=True, choices=list(SCENARIOS))
    ap.add_argument("--version-label", required=True)
    ap.add_argument("--guide", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--pre", action="append", default=[], help="commands the person runs before opening the agent")
    ap.add_argument("--first", required=True, help="first message the person types (from the guide)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-human-turns", type=int, default=12)
    a = ap.parse_args()
    sc, work, guide = SCENARIOS[a.scenario], Path(a.work), Path(a.guide).read_text()
    log, session, t0 = [], "", time.time()
    human_commands = 0
    for c in a.pre:
        run_human_command(work, c, work.name, log)
        human_commands += 1
    msg = a.first.replace("{idea}", sc["idea"])
    log.append({"role": "novice", "text": msg})
    done, human_msgs, confused = False, 1, 0
    for _ in range(a.max_human_turns):
        reply, session = agent_turn(work, msg, session, log)
        nov = novice_turn(sc["facts"] + ("\n" + sc["extra"] if sc.get("extra") else ""), guide, reply, log)
        if nov.strip().upper().startswith("DONE"):
            done = True
            break
        if "[CONFUSO]" in nov:
            confused += 1
        m = re.search(r"RUN:\s*(.+)", nov)
        if m:
            command = m.group(1).strip().strip("`")
            name = work.name
            try:
                name = json.loads((work / "lab.json").read_text()).get("project", name)
            except Exception:
                pass
            out, code = run_human_command(work, command, name, log)
            human_commands += 1
            shown = out[-1500:].strip() or "(nenhuma saída)"
            msg = f"Rodei `{command}` no terminal. Código de saída: {code}. Saída:\n{shown}"
        else:
            msg = nov
        human_msgs += 1
    lab = {}
    try:
        st = json.loads((work / ".honestlab" / "state.json").read_text())
        cfg = json.loads((work / "lab.json").read_text())
        led = (work / (cfg.get("lab_dir") or ".") / "ledger.jsonl").read_text().splitlines()
        exps = [json.loads(x) for x in led if '"experiment"' in x]
        lab = {"frozen": st.get("frozen"), "experiments": len(exps), "references": list((st.get("references") or {}).keys())}
    except Exception as e:
        lab = {"error": str(e)}
    last_agent = next((x["text"] for x in reversed(log) if x["role"] == "agent"), "")
    res = {"scenario": a.scenario, "version": a.version_label, "expect": sc.get("expect"), "completed": done, "human_messages": human_msgs,
           "human_commands": human_commands, "confused": confused, "minutes": round((time.time() - t0) / 60, 1),
           "lab": lab, "report_file": any((work / p).exists() for p in ("REPORT.md", "lab/REPORT.md")),
           "plain_verdict": report_verdict(work) or bool(re.search(r"(não encontr|encontrou|frágil|didn't find|did not find|found)", last_agent, re.I)),
           "log": log}
    Path(a.out).write_text(json.dumps(res, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in res.items() if k != "log"}, ensure_ascii=False))


if __name__ == "__main__":
    main()
