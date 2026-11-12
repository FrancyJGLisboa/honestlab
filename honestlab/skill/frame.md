# Frame: turn the idea into a contract

## Contents
- Steps 0-1: the project's rules, the data
- Steps 2-4: the automatic check, known methods, the evaluator
- Steps 5-9: lab.json, SPEC, starting point, known methods registered, approval page
- Steps 10-12b: red team, sanity checks, fake tests, many ideas at once
- Step 13: event questions ("did this event change that number?")

Run `honestlab status` first for the paths. "SPEC", "approval page", "evaluator", "dev
data" and "holdout data" mean the paths it prints.

0. **The project's own rules.** In an existing project, read its instruction files first:
   `README*`, `program.md`, `AGENTS.md`, `CLAUDE.md`, `CONTRIBUTING*`, and the dependency
   file (`pyproject.toml`, `requirements*.txt`, `package.json`). Keep what they fix:
   - **The measure.** If the project already names a measure (for example "the goal: get
     the highest val_auc"), use it as `metric`. For AUC, see the evaluator rules below.
     Choose another only if the person asks; then also report the project's measure in
     the SPEC and explain the change on the approval page.
   - **Limits on changes.** Files the project says not to edit go into `protected`.
     Packages: use only those in the dependency file when the project forbids new ones.
   - Write these rules in SPEC "Project rules", one line each, with the file they come from.
     If a rule conflicts with honestlab (for example "never stop"), honestlab's discipline
     wins; write the conflict there.
1. **Data.** Copy the person's data in with `honestlab data add <file> --split dev` (no need
   for cp). Split it so the holdout part is truly new: later period for anything over
   time, other places or items otherwise. Write the split with a small script that writes
   the holdout file directly (`honestlab data add <file> --split holdout` for a file you
   created), and never open, print or summarize the holdout data, not even to check it.
   - **Data the person does not have.** If the question needs data that the person did
     not bring (weather, prices, official statistics, open datasets), search public
     sources for it. Do not stop before you search. Prefer the publisher's own source (a
     government agency, a weather service, an exchange) to copies. Check the terms of use.
   - **Download with a script.** Write the script in `notes/` (for example
     `notes/fetch_weather.py`), so the person can run it again. Let the same script write
     the dev and holdout files directly. Then add them with `honestlab data add`. Do not
     look at the holdout part.
   - **Use only what was known at the time.** For a forecast, use only values that were
     published before each forecast date. Many sources revise old values or publish them
     days later (official statistics, reanalysis weather). If only revised values exist,
     use them and write this as a limitation.
   - **Record each source** in SPEC "Data": the URL, the publisher, the download date, the
     terms of use, the fetch script, and what the cleaning changed.
   - **Data that does not exist yet** (a survey, a field trial, a test with real
     customers, next season's harvest): no agent can produce it. Stop. Explain this in
     plain words. Tell the person how to collect it. honestlab fits after the data exists.
2. **Find an automatic check.** List measures a program can compute without human
   judgment. Prefer one the person already cares about (their error in their units, in
   money, in time). If no automatic check exists, stop and explain in plain words, and
   offer two or three measurable stand-ins with their weak points. Let the person choose.
3. **Known methods.** Search the web (if available) for the standard ways to solve this
   kind of problem and any published numbers. Include what the person does today. Write
   them in SPEC "Prior work" with how you searched.
4. **The evaluator** (path in `lab.json`, usually `eval/evaluate.py`):
   - accepts `--split dev|holdout` and reads only that split;
   - imports or runs the editable code, never copies it;
   - checks the output strictly and exits with an error on invalid output;
   - prints as its last line JSON with the measure AND `per_unit`, the result for each
     item whose average is the measure, e.g. `{"mae": 12.3, "per_unit": [10.1, 14.2, ...]}`.
     Use at least 30 items per split when possible. This gives honestlab its statistics;
     the person never sees them.
   - **AUC** (area under the ROC curve, for yes/no predictions) is not an average over
     items. Set `"aggregate": "auc"` and `"direction": "maximize"` in `lab.json`, and print
     `per_unit` as the `[label, prediction]` pair of every item (label 0 or 1), for example
     `{"auc": 0.91, "per_unit": [[1, 0.83], [0, 0.12], ...]}`. honestlab recomputes the
     AUC from the pairs and compares two versions by resampling items.
   - **Any other measure computed from items** (F1, median error, RMSE, rank correlation):
     write `measure(items)` in a file inside the evaluator folder (for example
     `eval/measure.py`), let the evaluator use it, and set `"aggregate": "custom"` and
     `"aggregate_file": "eval/measure.py"`. `per_unit` holds the items it reads, for example
     `[true value, prediction]`.
   - **Items in time order** (days, weeks, months) usually depend on their neighbours: a bad
     day is followed by another bad day. Keep `per_unit` in time order and set
     `"block_size"` in `lab.json` to about how many neighbours move together (for daily
     data, often 7 to 20). honestlab then resamples runs of neighbours instead of single
     days. With strong dependence and a short series, blocks help but do not fix it all:
     the held-out later period stays the main check.
   - For forecasts, only use information available at forecast time. If the data has
     the actual weather of the day instead of a forecast, say so as a limitation.
   - If the result can change from one run to the next (training a model, random
     sampling, a time budget), seed the randomness from the `HONESTLAB_SEED` environment
     variable and set `"repeats": 3` in `lab.json`. With `repeats` at 1, `honestlab
     baseline` runs the starting point twice and refuses when the two runs differ.
   - If the evaluator trains for a fixed number of seconds, also set
     `"remeasure_best": true`. Each run then measures the current best again next to the
     change, and `finding new` measures the known method and the candidate again side by
     side, so a busy or idle computer cannot make a change look better or worse.
   - Prefer the Python standard library. If packages are needed, create `.venv` in the
     project, install them there, and point `evaluator` in `lab.json` at
     `.venv/bin/python <evaluator path>`. Add every package you install to the project's
     dependency file (create `requirements.txt` if there is none), so the result runs on
     another computer. `honestlab check-spec` refuses a package that is imported but not
     declared.
5. **lab.json** (keep it short): `metric`, `direction` (`minimize` or `maximize`),
   `evaluator`, `editable` (the files the experiments may change), and `finding`:
   `min_effect` is the margin over the best known method that would matter to the person,
   from their answer ("10% menos erro" means `"min_effect": 0.10, "effect": "relative"`).
   If they said nothing, use 0.05 relative. If the person chose to explore, set
   `"keep_rule": "point"` (keep every attempt that beats the best, without a significance
   test); for prove, leave the default `"significant"`. Leave the other settings at their
   defaults.
6. **SPEC.** Fill every section; no TODO. "What counts as a finding" repeats the margin
   in words, measured against the best known method, not against a weak start.
7. **Starting point and measure.** In an existing project the starting point is the
   current code; otherwise write the simplest reasonable version of what the person does
   today. Run `honestlab check-spec` until it passes, then `honestlab baseline`.
8. **Register the known methods.** Write each one in a file outside the editable folder
   (for example `notes/ref_trend.py`) and run
   `honestlab reference add <short-name> --from <file> -m "<what it is, source>"`.
   honestlab measures it and puts the starting code back. Register the person's current
   method too if it differs from the starting point.
9. **Approval page** (path from `honestlab status`), in the person's language, one screen,
   no jargon, no TODO. Name a method or measure only next to what it does, for example
   "LightGBM (o método mais usado hoje para tabelas)":
   - **A pergunta:** one sentence.
   - **Como vamos medir:** one sentence in their units, and whether lower or higher is better.
   - **De onde vêm os dados:** for each file you downloaded, the source and the download
     date, in plain words. Omit this line if all data came from the person.
   - **Com o que vamos comparar:** what they do today and the best known methods, with
     their current numbers from `honestlab reference list`.
   - **O que conta como sucesso:** the margin in plain words, on the development data and
     on the data kept for the end, with a statistical safety check.
   - **Dados guardados para a prova final:** which part, and that nobody looks at it until the end.
   - **O que fica trancado depois da aprovação:** the question, the measure, the data and
     the success rule.
   - **O que o agente vai fazer:** up to N attempts, alone, each one recorded.
   - **Modo:** explore or prove, in one sentence, and that a finding needs proof either way.
   - **Limitações:** one to three honest points.
   - **Para aprovar:** in Claude Code, type `aprovar` in the chat; in another agent, open a
     terminal in this folder, type `honestlab freeze`, then `sim`.
   Editing the SPEC or this page after `honestlab baseline` is fine; changing data, the
   evaluator or the measure requires `honestlab baseline` again.
10. Red-team the evaluator: list in SPEC "Known ways to cheat this metric" three ways a
    solution could score well without being good, and close each one you can.
11. Sanity checks, before the approval page. A broken evaluator fails silently and wastes the
    whole run. Let honestlab check the first one: add `"sanity": ["guess"]` to `lab.json` and make
    the evaluator measure a solution that always gives the same answer when `HONESTLAB_SANITY`
    is `guess`. `honestlab baseline` then refuses a measure that cannot tell the starting
    solution from that guess. In a scratch copy (not in the editable paths), check and write the results in
    SPEC "Evaluator":
    - **A guess scores like a guess.** A solution that ignores the inputs (the average, the
      most common answer, or random) gives the expected chance value, for example AUC near
      0.5. Register it as a reference named `guess` when it is cheap.
    - **Scrambled answers break the model.** Train the starting code on training answers in a
      random order. Its score must fall to about the guess. If it stays good, information
      leaks from the answers into the inputs: fix that first.
    - **The score moves the right way.** A clearly worse solution scores worse, so the
      direction (`minimize` or `maximize`) is right.
12. **Fake tests** (`"placebos"` in `lab.json`, up to five short names). Each one is a version of
    the test where a real effect must vanish. The evaluator reads the name from the
    `HONESTLAB_PLACEBO` environment variable and runs that version. Before the held-out
    data is used, `honestlab finding new` measures the known method and the candidate on
    each fake test, and refuses the finding if the gain stays. Add them when they are cheap:
    - `shuffled`: train on the answers in a random order (catches leaks), as in step 11.
    - For a claim about a cause (an event, a policy, a new rule), a fake date when nothing
      happened, and an outcome the cause cannot touch. Write the claim's assumption in SPEC
      "What counts as a finding": the fake tests check it; they do not prove the cause.
12b. **Many ideas at once.** When the person wants several ideas tested (a hypothesis map), write
    them first in `eval/hypotheses.json` and set `"hypotheses": "eval/hypotheses.json"` in
    `lab.json`: id (H01, H02, ...), family, one-sentence claim, lens, and what the search found
    (`known`, `similar`, `nothing found`). Say the count per family on the approval page. After
    approval, start every `honestlab run -m` with the id it tests.
13. **Event questions** ("did this event change that number?": a policy, an export ban, a
    new rule, a launch on a known date). This fits honestlab. Do not leave the lab for it.
    Use the event test instead of the search loop:
    - Put the data up to the day before the event in the dev split and the data from the
      event date on in the holdout split. Do not look at the holdout data: the method must
      be fixed before anyone sees the result.
    - The editable code is the model of the normal value: what the number would be without
      the event, from its usual drivers (for a price, its main costs and its own last value).
    - The evaluator reads `HONESTLAB_EVENT_DATE`. With it set, fit the model on data before
      that date only and print the gap: the mean of real minus normal over the window that
      starts at that date. Without it, print the model's error in normal months (any honest
      number: it is only the starting measure).
    - In `lab.json`: `"event": {"date": "2021-10", "fakes": {"from": "2010-01", "to": "2021-05"},
      "side": "up"}`. Fake dates are dates when nothing special happened. Stop them one
      window before the event, so no fake window includes it. At least 19 are needed.
    - On the approval page, say in plain words: the date, the window, what the normal value
      uses, the fake dates, and that one look at the result is allowed.
    - When a similar series exists that the event did not reach (the same product in another
      region, a product outside the rule) but the other suspects did, add it as a control:
      `"control": "<short-name>"` in `"event"`. The evaluator reads `HONESTLAB_EVENT_SERIES`
      (`treated` or that name) and prints the gap of that series. Say on the approval page
      why the event cannot reach the control.
    - List in SPEC "What counts as a finding" the other events in the same weeks. The test
      can show the change is unusual. It cannot tell apart two events in the same window.
    After approval, run `honestlab event` once, then `honestlab report`. Do not run attempts
    with `honestlab run` first: a model changed after approval is refused.
