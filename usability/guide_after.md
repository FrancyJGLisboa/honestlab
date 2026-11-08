## Start in 3 steps / Comece em 3 passos

**1. Install once / Instale uma vez** (needs Python 3.9+ and git):

```bash
pipx install labloop     # or: pipx install ./labloop-kit
labloop setup            # teaches Claude Code, Codex and Copilot the labloop skill
```

**2. Open your agent in a folder / Abra o agente numa pasta**: an empty folder with
your data file (a spreadsheet, a CSV), or a project you already have.

**3. Say what you want to find out / Diga o que quer descobrir:**

> Use labloop: I think I can predict next week's sales from the weather better than I do today.
>
> Use labloop: acho que dá para prever as vendas de amanhã usando o tempo, melhor do que faço hoje.
>
> Use labloop: what could we discover in this project? / o que dá para descobrir neste projeto?

What happens next / O que acontece depois:

1. The agent asks you up to five simple questions. / O agente faz até cinco perguntas simples.
2. It prepares everything and shows you **one page**: the question, how it will be
   measured, what it will be compared with, and what counts as success. You approve
   it by opening a terminal in the folder and typing `labloop freeze`, then `yes`
   (or `sim`). / Ele prepara tudo e mostra **uma página**. Você aprova digitando
   `labloop freeze` num terminal na pasta, e depois `sim`.
3. The agent runs the experiments by itself, each one measured and recorded.
4. You get `REPORT.md` with a one-line verdict: **found**, **promising but fragile**,
   or **not found**, how sure it is, what was tried, the next step, and how each step
   matches what the AI labs do. / Você recebe o `REPORT.md` com o veredito em uma frase.

"Not found" is a normal, useful answer: it means the best known method held up against
an honest search. labloop never lets the agent call something a discovery unless it
held up on data kept for the end and passed an independent review.

Why you, and not the agent, approve the page: once you approve, nobody (not even the
agent) can change the question, the measure, the data or the success rule halfway
through. That is what keeps the result honest.

---
