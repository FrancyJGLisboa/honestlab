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

## Step 3: results a person can trust and repeat (next)

1. **A prior-work search that can be checked.** Today `literature.md` is free text, and
   `honestlab finding verify` only checks that it exists. The change:
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
2. **Automatic ablation.** For a finding, undo each part of the change one at a time and measure
   what each part contributes.
3. **A progress chart page.** Every attempt, the best so far and the known methods, in one
   picture the person can read without the terminal.
4. **One-command reproduction.** Run the finding again from a clean copy and get the same verdict.
5. **An explain-back test.** After the report, a simulated person explains the result in their
   own words, and the test checks that the explanation matches the numbers.

Open: a whole-night live run, so that the Stop hook blocks a real agent at least once.
