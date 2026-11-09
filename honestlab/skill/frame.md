# Frame: turn the idea into a contract

Run `honestlab status` first for the paths. "SPEC", "approval page", "evaluator", "dev
data" and "holdout data" mean the paths it prints.

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
     `.venv/bin/python <evaluator path>`.
5. **lab.json** (keep it short): `metric`, `direction` (`minimize` or `maximize`),
   `evaluator`, `editable` (the files the experiments may change), and `finding`:
   `min_effect` is the margin over the best known method that would matter to the person,
   from their answer ("10% menos erro" means `"min_effect": 0.10, "effect": "relative"`).
   If they said nothing, use 0.05 relative. Leave the other settings at their defaults.
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
   no jargon, no TODO:
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
   - **Limitações:** one to three honest points.
   - **Para aprovar:** in Claude Code, type `aprovar` in the chat; in another agent, open a
     terminal in this folder, type `honestlab freeze`, then `sim`.
   Editing the SPEC or this page after `honestlab baseline` is fine; changing data, the
   evaluator or the measure requires `honestlab baseline` again.
10. Red-team the evaluator: list in SPEC "Known ways to cheat this metric" three ways a
    solution could score well without being good, and close each one you can.
