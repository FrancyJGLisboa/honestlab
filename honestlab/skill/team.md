# Team: many hypotheses, one subagent per family

Use this when the person wants several ideas tested at once ("teste várias ideias", "um mapa de
hipóteses", "use um time"), or when the list of good ideas has two or more clear families. You are the
coordinator. You never decide a verdict: the `honestlab` program does.

**When not to use it.** One idea, or ideas that all change the same lines: work alone (`experiment.md`).
A team costs several times the tokens of one agent (Anthropic measured about 15 times the tokens of a
chat for multi-agent research), so use it only when the families are truly independent. Scale: 2 to 5
families, one subagent each; never more subagents than families.

## Before approval (Phase 2)
1. Write `eval/hypotheses.json`: 2 to 5 families, 2 to 4 hypotheses each (the format is in `frame.md`, step 12b, which you already followed in Phase 2). One
   family groups ideas that change the same part of the solution (inputs, model, data cleaning).
   For each one, search for prior work and set `prior` to what you found.
2. Set `"hypotheses": "eval/hypotheses.json"` in `lab.json`. On the approval page, say in plain words:
   how many ideas, in how many groups, and that each group gets its own helper.

## After approval
1. Run `honestlab team split`. It prints one copy per family, with its folder and its hypothesis ids.
2. Start one subagent per family, all in the same message so they run at the same time (Claude Code: the
   Agent tool). In Codex or Copilot, there are no subagents: do the families one after the other
   yourself, each in its own copy. Give each subagent this brief, filled in:

   > You test the hypotheses {ids} of family '{family}' in the honestlab copy at {copy}.
   > Work only inside {copy}. Give every file path in full, starting with {copy}. Start every shell
   > command with `cd {copy} && `. Never name another folder and never use `..`.
   > For each hypothesis: change the code in {copy}/src, then run
   > `cd {copy} && honestlab run -m "{id}: <what you changed and why>"`. honestlab keeps or reverts it.
   > Test every hypothesis at least once. Try variations of a hypothesis only under its own id.
   > Do not run `honestlab finding`, `freeze`, `unfreeze` or any git command.
   > When done, reply with one line per hypothesis: id, attempts, best score, kept or not.

3. When every subagent has replied, run `honestlab team collect` in the main lab.
4. For each family with a kept change, run
   `honestlab finding new --family <family> -m "<one-sentence claim>"`. The held-out bar is stricter by
   the number of families; honestlab says whether the change holds. Promote at most the families whose
   gain on the attempts data looks large enough to matter: each promotion uses one look at the
   held-out data.
5. For a confirmed finding, follow `finding.md`. The reviewer is a new subagent that gets only the files
   `finding.md` lists, never the team's replies or your notes.
6. Run `honestlab report`. The report has a section "The team" with every hypothesis. In the plain
   words, say how many ideas were tested, which held on new data, and that the others are listed too.

## Why the rules
- The copies have no held-out data, so the families cannot tune on it, even by accident.
- Every attempt names its hypothesis, so honestlab knows how many ideas were tried. More ideas need more
  evidence, and honestlab raises the bar for you.
- Only the main lab promotes findings, so one held-out look counts for the whole team.
