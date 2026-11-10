# Replay 2: autoresearch-tabular on UCI Adult Income, both tools side by side

Source: [autoresearch-tabular](https://github.com/saikatkumardey/autoresearch-tabular). It predicts whether a
person earns more than $50K a year from 1994 US census data. The author published no results, so we ran the task
twice on 2026-11-10, with the same goal both times.

- **Plain autoresearch:** Claude Sonnet follows the repo's own `program.md`. 15 experiments, then it must say
  whether it beat the best known approach.
- **honestlab:** Claude Sonnet with the honestlab plugin. A simulated beginner asks for the same goal in
  Portuguese and approves in the chat (`usability/novice_sim.py`, scenario `renda_adult`).

Then we scored each final model on data neither agent saw: the separate UCI `adult.test` file (16,281 people).
Scripts: `run_pair.sh` (the two runs), `grade.py` (the hidden-data score). Raw output: `runs/`.

## Result

Both agents said **no**: neither found a model worth calling better than the known method.

| | Plain autoresearch | honestlab |
|---|---|---|
| Experiments | 15 | 9 (it stopped, the scores had leveled off) |
| Agent time | 6 minutes | 13 minutes, plus 6 messages from the person |
| Known method | none registered; it named "tuned boosted trees, about 0.926" at the end | XGBoost and LightGBM, registered and measured before any experiment |
| Bar for "better" | none set in advance | at least 2% lower log loss, on new data too, set before the start |
| Best model | blend of 4 boosted tree models | blend of XGBoost, LightGBM and CatBoost |
| Claim | no: "the blend's extra 0.0015 is within noise" | not found: 0.3% better on dev, the bar was 2% |

On the hidden data (95% interval from a paired bootstrap over people):

| | Gain of the best model over the known method | Reading |
|---|---|---|
| Plain: blend vs LightGBM out of the box | AUC +0.0016 [+0.0007, +0.0024]; log loss 1.0% lower | real, but very small |
| honestlab: blend vs registered XGBoost | AUC +0.0008 [-0.0001, +0.0018]; log loss 0.5% lower | not clear, far below the 2% bar |

## What this shows

1. **Both claims hold on the hidden data.** No agent overclaimed. This matches the planted-flaw benchmark
   (`bench/RESULTS.md`): plain Claude Code is often well calibrated when it is asked the question directly.
2. **Plain autoresearch guessed the noise, honestlab measured it.** The plain agent estimated that AUC "wobbles
   by about 0.003" and called its gain noise. On 15,060 hidden people the gain is +0.0016 and its interval
   excludes zero. The gain is real, but too small to matter. The verdict was right for a wrong reason.
3. **honestlab set the bar before it saw results.** The 2% bar and the two known methods were fixed and
   approved first, so the "no" could not move after the scores came in.
4. **honestlab costs more time and asks the person to approve.** 13 versus 6 minutes, and 6 messages. The
   simulated person was confused once, by "bootstrap" and "confidence interval", and the agent then answered
   in plain words.

## Things to fix or watch

- **honestlab changed the project's metric.** The repo optimizes AUC, and honestlab's framing chose log loss.
  It said so in the approval page, but a user of this repo would expect AUC.
- **honestlab installed CatBoost.** The repo's `program.md` forbids new packages. honestlab does not read
  `program.md`, so it did not know this rule.
- **The plain setup shows the test score every time.** `prepare.py` prints `test_auc` after every run, so the
  agent could see it 15 times, and it quoted it at the end. Its log shows no choice made on it.

## After the fix: the honestlab run again

We changed the framing step: it now reads the project's own rules first (`honestlab/skill/frame.md`, step 0)
and writes them in SPEC "Project rules". Then we ran the honestlab side again (`run_pair.sh <clone> honestlab`,
recorded in `runs/honestlab_after_fix.json`).

| Check | First run | After the fix |
|---|---|---|
| Names the project's measure (AUC) | no | yes, in its first message and in SPEC "Project rules" |
| Decides with AUC | no (log loss) | no (log loss), with AUC reported next to it |
| Asks before it adds a package | no | yes, and the person said yes |
| Declares the new package in `pyproject.toml` | no | **no**, although its SPEC says "catboost was added" |
| Verdict | not found | not found (15 experiments, best 0.8% better than tuned CatBoost, bar 1%) |

Two things this shows:

1. **The measure has a real limit.** honestlab's statistics need one score per person whose average is the
   measure. AUC compares pairs of people, so it has no such form. The agent chose log loss for this reason and
   explained it. Fixed after this run: with `"aggregate": "auc"` the evaluator prints each person's label and
   prediction, and honestlab resamples people and computes AUC again (`tests/auc_test.py`). This rerun used
   the version before that fix.
2. **A written rule was not enough.** The agent said it added CatBoost and did not. So `honestlab check-spec`
   now checks it: every package that the evaluator or the editable code imports must be in a dependency file.
   On both recorded labs the check reports `catboost`. Five cases in `tests/robust_test.py` cover it.

## Third run: AUC support and the "use the whole budget" rules

After both fixes (AUC as a measure, and rules from the Claude prompting guide: use the whole budget,
work through ordinary obstacles, give each "never" rule its reason), we ran the honestlab side once more
(`runs/honestlab_finish_rules.json`).

| Check | First run | Second run | Third run |
|---|---|---|---|
| Experiments used of 15 | 9 (stopped at a plateau) | 15 | 15 |
| Decides with the project's measure (AUC) | no | no | **yes** (`"aggregate": "auc"`) |
| Uses only the project's packages | no (CatBoost) | no (CatBoost, not declared) | **yes** |
| Verdict | not found | not found | not found: 0.9253 vs LightGBM 0.9243, bar +0.003 |
| Messages from the person / confused | 6 / 1 | 4 / 0 | 6 / 2 |
| Agent time | 13 min | 41 min | 15 min |

The two fixes worked here. One new problem: the agent's first questions used "gradient boosting" and "AUC"
without plain words, and the simulated person was confused twice before approving. One run per version,
so these are signs, not proof.

**Fourth run, plain questions.** We then told the agent not to name methods or measures in its questions
and to say what they do instead ("o método mais usado hoje para tabelas", "uma nota de 0,5 (chute) a 1
(perfeito)"). Result (`runs/honestlab_plain_questions.json`): two short questions (the margin, and explore
or prove), no confused reply before approval, AUC as the measure, 15 of 15 attempts. Best 0.9296 against
LightGBM 0.928 with a bar of +0.002, so honestlab refused the final check on dev and spent no held-out
look; the verdict was "not found". After the result the person still asked what "dados de desenvolvimento"
and "intervalo de segurança" meant, so the plain-words rule needs to hold in the results message too.

**Fifth run, plain results and sanity checks** (`runs/honestlab_plain_results.json`). Before approval the
agent ran the new sanity checks and wrote them in the SPEC: random scores gave an error of 0.494 (chance is
0.5); XGBoost trained on shuffled answers gave 0.473 (no leak); the weak start scored worse than the strong
methods (direction right). It used the new custom measure to decide on `1 - AUC`, so that "5% less error"
has a meaning; the ranking is the same as AUC. 15 of 15 attempts, only the project's packages, verdict
"not found" (0.0725 against LightGBM 0.0723). The plain-words rule for the results message did not hold:
the message named "LightGBM" and "dados guardados" and coined "taxa de erro de ordenação", and the person
asked what they meant (one confused reply). The agent then explained them well. Written rules moved the
questions to plain words, but not yet the results message; a test with real people is the next check.

## Limits

- One run per tool. A second run could differ.
- One model (Sonnet) and one task. On this data the known method is hard to beat, so "no" was the likely answer.
  The case does not test what each tool does when a real gain exists.
- The two tools trained on different splits (plain: 60% of rows without missing values; honestlab: 80% of all
  rows), so compare each row of the hidden-data table within its own tool, not across tools.
- The honestlab ledger is not in `runs/`: it holds a local path, and editing it would break its hash chain.
