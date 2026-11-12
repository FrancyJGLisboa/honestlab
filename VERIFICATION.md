# Verification

honestlab asks its users to prove a result before calling it a discovery. This page holds the
project to the same rule: every claim in the [README](README.md) is listed here with the way to
check it.

Run the automated checks with:

```bash
python3 tests/verify_claims.py          # about a minute; runs the full test suite too
python3 tests/verify_claims.py --fast   # skips the test suite
```

A claim that cannot be checked by a command says so, and points to the record or the outside
source it rests on.

## Claims checked by `tests/verify_claims.py`

| Id | Claim in the README | How it is checked |
|---|---|---|
| V1 | Status: early (0.5) | The version is the same in `pyproject.toml`, `honestlab/__init__.py`, `.claude-plugin/plugin.json` and the README. |
| V2 | honestlab itself makes no network calls | No module in `honestlab/` imports a network library or opens a URL. |
| V3 | By default the agent tries up to 15 changes | The skill's instructions set 15 attempts as the default. |
| V4 | The report excerpt at the top | Its numbers (18.6, 52.8, 27.5) and its verdict appear in the recorded `usability/runs/after-vendas/REPORT.md`. |
| V5 | Usability numbers (messages, terminal commands, jargon blocks, reports) | They are recomputed from the transcripts in `usability/runs/*.json`, for the runs before the redesign and for the plugin runs. |
| V6 | How long a run takes | The time range in the README covers the minutes recorded in the plugin runs. |
| V7 | Honesty benchmark: plain Claude Code 12 of 12, honestlab 11 of 12 | Round 2 is recomputed from `bench/raw/results_naive.json` (plain 6 of 6, honestlab 5 of 6). That file was graded against the original ground truth; the check applies the correction documented in `bench/RESULTS.md` (on bin packing the right answer is "no", because Sum-of-Squares beats the new rule, 6.55 vs 6.88). Without the correction the file reads plain 4 of 6. Round 1 (6 of 6 each) is recorded in `bench/RESULTS.md`; its raw logs were not kept. |
| V8 | The agent cannot approve the page in a terminal | `honestlab freeze` run with an agent's environment marker is refused. |
| V9 | Installs as a Claude Code plugin | `claude plugin validate` passes (skipped when the `claude` command is not installed). |
| V10 | 51 hook decisions, 83 end-to-end cases, 48 approval, unlocking and plugin cases, 17 attack replays, 73 robustness cases, 24 overnight mode cases, 17 ablation cases, 11 reproduction cases, 30 machine-speed drift cases, 22 explain-back checker cases, 36 measure cases, 12 fake-test cases, 29 event-test cases, 18 follow-up question cases, 9 sanity-check cases, 15 hypothesis-list cases, 11 researcher-mode cases, 16 skill-rule cases, 31 team cases | A fresh run of `tests/run_all.sh` passes all of them, with exactly those counts. |
| V11 | With no real effect honestlab never said "found" in 400 simulated labs per scenario; below-margin effects were called "found" up to 15% of the time | The rates are read from `stress/calibration.json`, written by `python3 stress/calibration.py 400` (fixed seed, so the run reproduces exactly). |
| V12 | Only questions whose data does not exist yet are out of scope; the agent looks for data the person lacks in public sources | The README row and the skill rules are read from `README.md`, `README.pt-BR.md`, `honestlab/skill/SKILL.md` and `honestlab/skill/frame.md`: search public sources, fetch with a script in `notes/`, use only values published before each forecast date, record each source, show downloaded sources on the approval page, stop when the data does not exist yet. |

| V13 | Training noise: "one run, keep if lower" kept 10 changes, 4 really better and 5 noise; honestlab now keeps 5, 4 really better | The counts are read from `stress/keep_rule.json`, written by `python3 stress/keep_rule.py report` from the recorded runs in `stress/keep_rule_runs.json` (regenerate the runs with `python3 stress/keep_rule.py run 15`, about 25 minutes; timings vary by machine, so a new run gives somewhat different numbers). |
| V14 | Explain-back: 22 of 24 readings of `REPORT.md` had the right verdict and only true numbers, against 5 of 24 for an autoresearch-style log | The readings recorded in `usability/runs/explain_back/before_fix.json` are scored again with the checker in `usability/explain_back.py` against the lab files in `stress/runs` (new readings: `python3 usability/explain_back.py --labs ... --samples 3 --out FILE`, about 10 minutes, calls Claude; a new run gives somewhat different numbers). |

## Claims checked by the test suite

These are covered case by case in `tests/` (run `bash tests/run_all.sh`):

| Claim in the README | Where |
|---|---|
| After approval, the measuring code, data and success rule are fingerprinted and read-only, and any change is detected and blocks further results | `tests/edge.sh`, tampering cases |
| The agent cannot see the locked test data | `tests/guard_test.py` (holdout reads and holdout scoring are denied) and `tests/edge.sh` |
| The approval code is shown only to the person; honestlab blocks the obvious ways for the agent to approve, and a report cannot say "Found" without the person's own confirmation message | `tests/approve_test.sh` (the code is not in the agent's context, is stored only as a slow hash bound to its expiry; wrong, expired, edited or out-of-date codes are refused; a self-approval or a subagent's message is flagged and downgrades "Found") and `tests/guard_test.py` (internals, the pending file, `.honestlab/` and session transcripts are blocked) |
| Every attack that worked in the stress test is now blocked or detected, except the forged review | `tests/redteam_test.sh` replays them; `stress/RESULTS.md` lists them and what remains open |
| The result is compared with the best known method, not just with the starting point | `tests/edge.sh`, strongest-reference cases (including a reference that is strongest only on the held-out data) |
| A finding needs a prior-work search someone else can repeat, and the report says whether the result is known, similar or nothing similar was found | `tests/edge.sh`, prior-work cases (free text, 2 searches, 1 source, a work without a link, no novelty line and a vague reviewer re-check are each refused; the report and the ledger show the search) |
| The report says which parts of a finding's change made the difference, measured without the held-out data | `tests/ablate_test.py` (a part that helps, a cosmetic part, a part that hurts and a part the rest depends on are each told apart; the code is restored; the holdout budget is untouched; a finding promoted from a discarded experiment works) |
| Anyone with the lab folder can measure the result again with one command | `tests/reproduce_test.py` (same verdict from a clean copy; the start, the candidate on dev and on held-out data are re-measured; the holdout budget is not spent; an edited record shows as a difference outside the noise; a changed protected file fails the copy's check) |
| "Not found" and "promising but fragile" are reported as such | `tests/edge.sh`, report verdict cases |
| The plugin brings its own command, skill and hooks, and does not run twice when a project has its own | `tests/approve_test.sh`, plugin cases |

## Claims that rest on records or outside sources

| Claim in the README | Basis |
|---|---|
| The agent wrote the caveat in the report excerpt without being asked | The transcript in `usability/runs/after-vendas.json`. |
| Tested live with Claude Code 2.1 on Linux, including the plugin and approving in the chat | The transcripts in `usability/runs/plugin-*.json`, run with Claude Code 2.1.319. |
| When honestlab blocks a message to show the approval page, Claude Code shows it to the person and does not add it to the model's context | Claude Code's hooks documentation for `UserPromptSubmit` ("Shown to the user when decision is block. Not added to context"): https://code.claude.com/docs/en/hooks. In the live test the blocked message cost zero model turns. |
| DeepMind's FunSearch (2023) worked on online bin packing | Romera-Paredes et al., "Mathematical discoveries from program search with large language models", Nature, 2023: https://www.nature.com/articles/s41586-023-06924-6 |
| DeepMind's AlphaEvolve (2025) found new algorithms with an automatic evaluator in a loop | DeepMind blog, 14 May 2025: https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/ |

## Known limits of these checks

- The usability runs use a model playing a non-technical person, one run per scenario.
- The benchmark is small and synthetic, and uses one model family.
- Codex CLI, Copilot CLI and Windows are not covered by live tests.
- The guard matches text, and checks that run inside the evaluator's process can be evaded by a
  determined agent running as the same OS user. honestlab cannot verify who wrote the
  "independent" review. See `stress/RESULTS.md`, "Still open".

If you find a claim on the README that is not on this page, or a check that does not hold,
please open an issue.
