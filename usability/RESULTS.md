# Usability test: labloop 0.3.2 (before) vs 0.4.0 (after)

> These runs used honestlab's earlier name, labloop. The tool is the same; only the name changed.

Method: a real Claude Code agent (headless, tools allowed) works with a simulated
non-technical person, played by a second model instance that knows only the version's quick
guide, answers in plain Portuguese, flags jargon it does not understand with [CONFUSO],
and runs a terminal command only when told to. Two scenarios: an ice-cream shop owner with
a sales spreadsheet (`vendas`), and someone who inherited a crop-forecast repository
(`cropcast`). One run per cell. Driver: `novice_sim.py`; transcripts in `runs/*.json`.

| | before: vendas | before: cropcast | after: vendas | after: cropcast |
|---|---|---|---|---|
| Messages the person typed | 4 | 4 | 3 | 3 |
| Terminal commands the person ran | 2 | 3 (1 failed) | 1 | 1 |
| Times the person got stuck on jargon | 1 | 1 | 0 | 0 |
| Plain-language final report produced | no | no | yes | yes |
| Minutes | 3.7 | 3.8 | 3.6 | 4.6 |

What went wrong before: the person had to run `labloop init` and use skill names; one
typed "Use the labloop-frame skill on proposal 1" into the terminal as if it were a
command. Both hit jargon (MAE, baseline, holdout, dev, bootstrap) at decision points and
had to ask for explanations. Neither got a report without asking.

What happened after: the person typed "Use labloop: <idea>", answered one set of
questions, ran `labloop freeze` once, and received a verdict in plain words plus
REPORT.md. In both runs the agent explained, unprompted, that the success bar was set
against the best known method and not against the person's current method, and flagged
that the weather in the data is the observed weather, not a forecast.

Limitations: one run per cell; the "person" is a model, not a human; tool permissions were
granted up front, so approval prompts a real Claude Code user would see were not counted;
Codex CLI, Copilot CLI and Windows were not tested; both scenarios contain a real signal
by construction, so "found" was the correct verdict; the statistics treat items
(days, county-years) as independent, which the cropcast report itself flagged as a reason
for caution with only three held-out years.

## 0.5: the Claude Code plugin and approval in the chat

Same method and scenarios. This time the person had only the honestlab Claude Code plugin
installed (no `pip`, no `pipx`, and no `honestlab` command in their own terminal), and approved
in the chat: `aprovar`, then `sim` with the 4-digit code that honestlab showed them. Driver:
`run_plugin.sh`; transcripts in `runs/plugin-*.json`; guide the person read: `guide_plugin.md`.

| | 0.4: vendas | 0.4: cropcast | 0.5 plugin: vendas | 0.5 plugin: cropcast |
|---|---|---|---|---|
| Messages the person typed | 3 | 3 | 5 (4 for the flow, plus 1 follow-up question) | 4 |
| Terminal commands the person ran | 1 | 1 | 0 | 0 |
| Times the person got stuck on jargon | 0 | 0 | 0 | 0 |
| Plain-language final report produced | yes | yes | yes | yes |
| Verdict | found | found | found | not found |
| Minutes | 3.6 | 4.6 | 4.7 | 4.7 |

Approving now takes two short chat messages instead of one chat message plus a command in a
second terminal. The person never needs a terminal.

**A first run found a bug.** In the first plugin run of the cropcast scenario, the person sent
`aprovar` twice. The file holding the pending code was not excluded from git, so honestlab read
the second request as "something measured changed" and refused it; after the agent re-measured,
the file was committed. The agent ended up asking the person to run a git command in a terminal
(10 messages, 1 terminal command in total). Fixed in 0.5.0: the file is excluded from git in every
repository and ignored by change checks, sending `aprovar` again simply shows a new code, and the
code now also appears on the first line of the message. Regression tests cover both cases. That
run's transcript was overwritten by the rerun reported above; the description here comes from
reading it before the rerun.

**Run-to-run variation.** The buggy first run of cropcast ended with "found" (about 13% less
error than a per-county linear trend on the held-out years). The rerun registered different and
stronger known methods as the bar, and ended with "not found". Same data, same person, different
agent choices. This is why a single "found" deserves a second look.

In the vendas rerun, the agent simulated forecast error in the weather on its own initiative,
so the test would not assume a perfect forecast, and then answered the person's follow-up with a
table of how the gain shrinks as forecasts get worse.

Limitations: as above (one run per cell after the fix, a model playing the person, permissions
granted up front, Claude Code on Linux only). The plugin was installed from a local folder, since
the repository is not yet published, so the one-line install itself was not exercised.

## 0.5: explain-back test (can a person repeat the result correctly?)

Method (`explain_back.py`, data in `runs/explain_back/`):
1. A reader model (Claude Haiku) plays a person with no technical training. It reads one document
   once and explains the result to a business partner in 120 words or fewer.
2. An extractor model (Claude Sonnet) reads only that explanation and writes down what it claims:
   verdict, numbers, whether it was confirmed on new data, whether it is new.
3. Python compares the claims with the truth computed from each lab's state, configuration and
   ledger, not from the report text. A reading passes when the verdict is right, every number
   it states is a true number (within 2%, or 2 points for a percentage), and it does not
   overclaim.

Two documents on the same 8 finished labs from `stress/runs` (4 found, 4 not found), 3 readings
each:
- **report**: honestlab's `REPORT.md`.
- **log**: what autoresearch leaves behind, a `results.tsv` with one row per attempt (id, score,
  keep or discard, description), built from the same ledger.

| | report | log |
|---|---|---|
| Readings that pass | 22 of 24 | 5 of 24 |
| Verdict right | 22 of 24 | 5 of 24 |
| Every stated number true | 24 of 24 | 18 of 24 |
| Says something false about the result | 0 | 1 |

(First run, scored with the final checker. The first checker version did not know the
held-out scores, so it marked true numbers as wrong.)

Why the log fails: it does not contain the best known method or the agreed margin, so the reader
cannot know whether the result is a finding. In 18 of 24 log readings the reader said
"promising, not proven". In the not-found labs that hides the answer the person needs. One log
reader of the delivery lab said the simple model was a new finding, but that model was already a
known method. In the ice-cream lab, log readers called the starting point the known method. This is
a limit of the log format by construction, not of the reader.

**What the test found in the report.** In the ice-cream lab (`impaciente`), all 3 readers mixed
two candidates: the confirmed finding (E0001, 16.1 vs 19.6 on new data) and a later, better
attempt that was never tested on new data (E0003, 12.04). One reader wrote: "the report says
high confidence, but its numbers do not match each other". The numbers section showed E0003 as
the best result and a new-data line with a percentage next to an interval in score units.
Fix in `report.py`:
- The new-data line shows both scores ("E0001 (F001) 16.06 against 19.57 for so_temperatura:
  17.9% better"), and labels the interval with its unit.
- When the best result is not the finding tested on new data, the report says so.

After the fix (same 8 labs, 3 new readings each): 22 of 24 pass. Readers of the ice-cream lab no
longer said the numbers do not match. But 1 of 3 still called the verdict "fragile", because the
report also says that the rain variant is not confirmed. The other failure is the extractor's: a
reader wrote "fell from 28.3 to 20.3" (known method to best), and the extractor called 28.3 the
starting point. 22 of 24 before and after: the fix removed a confusion, but this test cannot
show a change in the pass rate with 24 readings.

Limits:
- A model plays the person. It reads more carefully than many people do, and it never skims.
- The extractor can misread an explanation. Each failure above was read by hand.
- The log comparison is unfair to the log by design: it lacks the information. The test shows
  that the missing information changes what a person repeats.
