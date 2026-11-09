# Roadmap

Goal: an evolution of Karpathy's autoresearch that follows the practices of AI labs, and is
easier to use and to understand than anything built so far.

## Step 1: no terminal for the person (done)

Unlock in the chat, a refused baseline when `per_unit` is wrong, and a guard fix. A simulated
person needed 4 messages and 0 terminal commands. See `stress/RESULTS.md`, "Public data".

## Step 2: training models, like autoresearch (done)

Native libraries allowed in candidate code, the character model example, overnight mode, and a
two-level bootstrap that counts run-to-run training noise. See `stress/RESULTS.md`, "Training
round".

## Step 3: results a person can trust and repeat (done)

1. **A prior-work search that can be checked (done).** Before, `literature.md` was free text, and
   `honestlab finding verify` only checked that it existed. The change:
   - `literature.md` gets a fixed table: each query, where it was run (for example Google
     Scholar, arXiv, Semantic Scholar, GitHub), the date, and the results found, each with a
     link and one line on how it differs from the claim.
   - `honestlab finding verify` refuses a search with fewer than 3 queries, fewer than 2
     sources, or a listed result without a link.
   - The independent reviewer runs one query again and says whether it found something the
     search missed.
   - The report shows the search next to the verdict ("searched 4 queries in 3 sources on
     <date>; closest work: ...") and always says that finding nothing does not prove the result
     is new.
   - Limit: honestlab makes no network calls, so it checks the form of the search, not that the
     links are real or complete.
2. **Automatic ablation (done).** `honestlab finding ablate F00N` undoes each part of the change
   (each diff hunk, or each file when there are more than 12 hunks) alone, measures it on dev, and
   says which parts help, hurt, have no clear effect or are needed for the code to run. The
   report lists them under "What made the difference".
3. **A progress chart page (done).** `honestlab report` also writes `PROGRESS.html`: every
   attempt (kept or undone), the best so far, the starting point, the best known method and
   the bar, with the verdict on top, hover details and a table view. No network.
4. **One-command reproduction (done).** `honestlab reproduce [F00N]` clones the lab from its git
   history, checks the ledger and the approval fingerprints, measures the start, the strongest
   reference and the candidate again (dev, and held-out data already used for that finding), and
   says whether the verdict is the same. Differences are judged against the noise.
5. **An explain-back test (done).** A simulated person reads the report and explains the result
   in their own words. A second model writes down the claims, and Python checks them against the
   lab's records. 22 of 24 readings of `REPORT.md` passed, against 5 of 24 for an
   autoresearch-style `results.tsv`. The test found a confusing line in the report, which is now
   fixed. See `usability/RESULTS.md`.

Open:
- A whole-night live run, so that the Stop hook blocks a real agent at least once.
- Time-budget drift (done, one part not yet live): `"remeasure_best": true` measures the current
  best again next to each change (live check in `stress/RESULTS.md`), and `finding new` measures
  the known method and the candidate again side by side. The finding part is tested with a fake
  speed file only. Open: a live finding on a time-budget lab.
