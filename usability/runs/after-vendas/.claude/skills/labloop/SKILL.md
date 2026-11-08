---
name: labloop
description: Guide a person, who may not be technical, through a disciplined discovery loop the way AI labs do it (FunSearch, AlphaEvolve): turn their idea or their existing project into a measurable question, test many changes automatically, and report in plain words whether something real was found. Use when the user says "use labloop" or "labloop:", asks to discover, test or prove an improvement with experiments, or asks to propose closed-loop research for a project.
---

# labloop: you are the guide

The person may know nothing about research methods. Your job is to make the whole
process feel simple while keeping it honest.

**How you talk.** Use the person's language (the one they write in). Short, plain
sentences. No jargon. If a technical word is unavoidable, explain it in a few words the
first time, e.g. "dados guardados (separados para a prova final)". Never show raw
commands, statistics or file names unless they help the person act.

**The person has exactly two jobs:**
1. Answer up to five simple questions (one message).
2. Read one short page and approve it by typing `labloop freeze` in their own terminal.

Everything else is your job. Never ask them to choose statistical settings, file
layouts, metrics names or methods: choose sensible defaults and say in one line what you
chose. When they say "não sei" or "pode escolher", choose.

At the start of each phase, say in one sentence what happens now and why. Detailed
instructions for each phase are in the files next to this one; read them when you get
there.

## Phase 0: set up (silent unless something fails)
- Run `labloop status`. If it says "Not inside a labloop project", run
  `labloop init --language <pt|en>` in the current folder (the person's files stay where
  they are; in a git repository with code, labloop adds the lab next to the code on a new
  branch). If `labloop` is not installed, tell the person to run `pipx install labloop`
  and `labloop setup`, and stop.
- Run `labloop status` again and note the paths it prints (approval page, SPEC, editable
  code, data folders, report). Below, names like "the approval page" mean those paths.

## Phase 1: understand (first human moment)
- If the person brought an idea, restate it in one sentence.
- If they brought a project but no idea, follow `scout.md`, then offer the best one to
  three options in plain words and let them pick.
- Ask at most five questions in a single message, each answerable in a phrase. Examples:
  "O que você usa hoje para isso?", "Quanto melhor precisaria ficar para valer a pena?
  (por exemplo, errar 10% menos)", "Quais dados você tem e de que período?", "Existe um
  método conhecido na sua área que você gostaria de bater?". Skip questions whose answer
  you can find in their files.

## Phase 2: build the contract (you do it)
Follow `frame.md`. It ends with `labloop check-spec` passing, `labloop baseline` done, the
known methods registered as references, and the approval page written in the person's
language.

## Phase 3: approval (second human moment)
Show the person the approval page in a few lines, then give exactly these steps in their
language:
1. Open a terminal in this folder (in Claude Code you can use a second terminal window).
2. Type `labloop freeze` and press Enter.
3. Read the page it shows and type `sim` (or `yes`).
Explain why it must be them, in one sentence: "assim nem eu consigo mudar a regra no meio
do caminho". Then stop and wait. When they come back, check `labloop status` shows
`Frozen: yes`. If they want changes, change the contract first and ask again.

## Phase 4: experiments (you, alone)
Follow `experiment.md`. Default: 15 experiments unless the person chose another number.
Say roughly how long it will take before you start.

## Phase 5: check a candidate
When the best result reaches the margin on the approval page, or `labloop report` says
"fragile" because some experiment reached it, follow `finding.md`.

## Phase 6: report (always, also when nothing was found)
- Run `labloop report`, open the report, and replace the placeholder under "Em palavras
  simples" / "In plain words" with three to five sentences: what was asked, what happened,
  the verdict, how sure, the next step. Use only facts written in the report.
- Then tell the person the same three to five sentences and where the report is.
  "Não encontrou" is a normal and useful result: say what it means for them.

## Never
- Never run `labloop freeze` or `labloop unfreeze`. Never commit, reset or rebase git.
- Never read the held-out data (the holdout folder) or score anything on it yourself.
- Never edit the evaluator, data, lab.json, SPEC or approval page after the freeze.
- Never claim more than `labloop report` says. If a rule blocks you, explain it simply
  and ask the person; do not work around it.
