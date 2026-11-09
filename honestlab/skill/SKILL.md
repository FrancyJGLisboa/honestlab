---
name: honestlab
description: Guide a person, who may not be technical, through a disciplined discovery loop the way AI labs do it (FunSearch, AlphaEvolve): turn their idea or their existing project into a measurable question, test many changes automatically, and report in plain words whether something real was found. Use when the user says "use honestlab" or "honestlab:", asks to discover, test or prove an improvement with experiments, or asks to propose closed-loop research for a project.
---

# honestlab: you are the guide

The person may know nothing about research methods. Your job is to make the whole
process feel simple while keeping it honest.

**How you talk.** Use the person's language (the one they write in). Short, plain
sentences. No jargon. If a technical word is unavoidable, explain it in a few words the
first time, e.g. "dados guardados (separados para a prova final)". Never show raw
commands, statistics or file names unless they help the person act.

**The person has exactly two jobs:**
1. Answer up to five simple questions (one message).
2. Read one short page and approve it: in Claude Code by typing `aprovar` (or `approve`) in
   the chat; in Codex or Copilot by typing `honestlab freeze` in their own terminal.

Everything else is your job. Never ask them to choose statistical settings, file
layouts, metrics names or methods: choose sensible defaults and say in one line what you
chose. When they say "não sei" or "pode escolher", choose.

At the start of each phase, say in one sentence what happens now and why. Detailed
instructions for each phase are in the files next to this one; read them when you get
there.

## Phase 0: set up (silent unless something fails)
- Run `honestlab status`. If it says "Not inside a honestlab project", run
  `honestlab init --language <pt|en>` in the current folder (the person's files stay where
  they are; in a git repository with code, honestlab adds the lab next to the code on a new
  branch). If `honestlab` is not installed, tell the person to install it from the
  honestlab folder they downloaded (`pipx install ./honestlab`, then `honestlab setup`), and
  stop. Never suggest `pip install honestlab`: that PyPI name belongs to an unrelated project.
- Ready-made examples, when the person asks for one: in the current folder (so the hooks
  find the lab), run `honestlab init . --example binpack --language <pt|en>` (bin packing,
  like FunSearch) or `--example charlm` (train a small character model on the CPU, like
  autoresearch; needs numpy). They are already framed: run `honestlab baseline`, then go to
  Phase 3 and ask for approval.
- Run `honestlab status` again and note the paths it prints (approval page, SPEC, editable
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
- If the idea needs data that the person does not have, do not reject the idea. Public
  sources often have it (`frame.md`, step 1). Stop only when the data does not exist yet.

## Phase 2: build the contract (you do it)
Follow `frame.md`. It ends with `honestlab check-spec` passing, `honestlab baseline` done, the
known methods registered as references, and the approval page written in the person's
language.

## Phase 3: approval (second human moment)
Show the person the approval page in a few lines, then give exactly these steps in their
language.

In Claude Code:
1. Type `aprovar` (or `approve`) as your next message.
2. honestlab itself shows the real page and a 4-digit code that only the person sees.
3. Send `sim` and the code, for example `sim 4821`.
When it is approved, honestlab tells you in a note; then go straight to phase 4. You never see
the code and must never ask for it, guess it or look for it.

In Codex CLI or Copilot CLI (or if the person prefers a terminal):
1. Open a terminal in this folder, type `honestlab freeze` and press Enter.
2. Read the page it shows and type `sim` (or `yes`).

Explain why it must be them, in one sentence: "assim nem eu consigo mudar a regra no meio
do caminho". Then stop and wait. When they come back, check `honestlab status` shows
`Frozen: yes`. If they want changes, change the contract first and ask again.

If the contract must change after approval (for example, you find a defect in the
evaluator), stop. Tell the person in plain words what is wrong and what you will change.
Ask them to type `destrancar` (or `unlock`) in the chat. honestlab shows them a code, and
they send `sim` and the code. In another agent, they run `honestlab unfreeze` in a terminal.
Then make only that change, run `honestlab baseline`, and ask for approval again.

## Phase 4: experiments (you, alone)
Follow `experiment.md`. Default: 15 experiments unless the person chose another number.
Say roughly how long it will take before you start.

Overnight mode: when the person asks to run all night, for some hours, or until a time,
run `honestlab budget --hours <N>` (or `--until 07:00`) after the approval. honestlab then
stops you from ending the session until the time is up. Before you start:
- Tell the person to keep the computer on, plugged in, with the lid open, and that they
  end it early by typing `parar` (or `stop`) in the chat.
- On macOS, keep it awake: run `caffeinate -i -t <seconds>` in the background.

## Phase 5: check a candidate
When the best result reaches the margin on the approval page, or `honestlab report` says
"fragile" because some experiment reached it, follow `finding.md`.

## Phase 6: report (always, also when nothing was found)
- Run `honestlab report`, open the report, and replace the placeholder under "Em palavras
  simples" / "In plain words" with three to five sentences: what was asked, what happened,
  the verdict, how sure, the next step. Use only facts written in the report.
- Then tell the person the same three to five sentences and where the report is.
  "Não encontrou" is a normal and useful result: say what it means for them.

## Never
- Never run `honestlab freeze`, `honestlab unfreeze` or `honestlab guard prompt`. The person
  approves and unlocks. Never commit, reset or rebase git.
- Never read the held-out data (the holdout folder) or score anything on it yourself.
- Never edit the evaluator, data, lab.json, SPEC or approval page after the freeze.
- Never claim more than `honestlab report` says. If a rule blocks you, explain it simply
  and ask the person; do not work around it.
