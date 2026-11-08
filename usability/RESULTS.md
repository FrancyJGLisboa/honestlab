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
