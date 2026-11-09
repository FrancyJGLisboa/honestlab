# SPEC: modelo_noite

## Question
Can a small neural character model in src/model.py, trained for a fixed 60 seconds on a laptop CPU, predict the next character of Machado de Assis's *Dom Casmurro* better than a classical interpolated n-gram model, measured in bits per character on chapters it never trained on?

## Why it matters
This is the experiment loop of Karpathy's autoresearch (an agent edits a training script, every run gets the same time budget, and the validation loss decides) on a CPU instead of a GPU. It adds what autoresearch leaves out: a success rule written before any result, a strong classical method to beat, chapters locked until the end, and a statistical check before a change is kept.

## Metric
`bpc`: bits per character on the scored chapters, the mean over chunks of 400 characters. Direction: minimize. A plain text file uses 8 bits per character; the starting model uses about 2.65, the n-gram reference about 2.38 on dev.

## Evaluator
eval/evaluate.py hands the training text to `train(ids, vocab, seconds, rng)` as integer ids, with a fixed budget of 60 seconds (BUDGET_SEC, plus 5 seconds of slack; a slower training is an error). It then scores every 400-character chunk from left to right: `predict(state, contexts)` sees only the CONTEXT characters before each guess, inside the same chunk, and returns one probability per possible character. Rows must be valid probabilities that sum to 1. The random generator is seeded from HONESTLAB_SEED. Training gives a slightly different model every time, so honestlab runs the evaluator 3 times per attempt (lab.json "repeats": 3, seeds 0 to 2) and counts that run-to-run noise in its statistics. One attempt takes about 3.5 minutes.

## Data
Machado de Assis, *Dom Casmurro* (1899), public domain, from Project Gutenberg eBook #55752 (header and license text removed), bundled with honestlab. data/train: chapters 1 to 104 (about 284,000 characters). data/dev: chapters 105 to 126 (about 50,000). data/holdout: chapters 127 to 148 (about 42,000), locked until the end. Characters never seen in training get id 0.

## Baseline
A tiny neural network in the style of Bengio et al. (2003): the last 3 characters, embeddings of 16, one hidden layer of 64 units, plain stochastic gradient descent, numpy only. About 2.65 bpc on dev.

## Budget
60 seconds of training per run, fixed in the evaluator; 3 runs per attempt. 15 attempts by default (about an hour); overnight mode (`honestlab budget --hours 8`) runs about 130.

## What counts as a finding
Machine-checked by honestlab (lab.json "finding"): beat the strongest registered reference (the n-gram model, registered by `honestlab init --example charlm`) by at least 0.05 bits per character on dev, and on the holdout with a paired bootstrap CI over the chunks that excludes zero.

## Prior work
Bengio et al. (2003) introduced neural language models of this shape. Witten-Bell smoothing (Witten and Bell 1991) and its comparison with other n-gram smoothing methods (Chen and Goodman 1998) give the classical reference. Karpathy's autoresearch runs the same kind of loop with a GPT model and a 5-minute budget on a GPU. Small neural models beat n-grams on large corpora; on 284,000 characters and 60 seconds of CPU the outcome is open.

## Known ways to cheat this metric
1. Seeing the character being guessed: closed, predict() receives only the characters before it, inside the same chunk.
2. Training longer than the budget: closed, the evaluator times train() and fails the run when it exceeds 65 seconds. Work done at import time counts, because the clock starts before the import.
3. Training on the scored chapters: the files are protected and the tripwire flags candidate code that opens data files. predict() may adapt to characters it has already seen (dynamic evaluation); the other chunks it sees in the same call are later text, so the reviewer must check that any such adaptation is honest.
4. Reading the evaluator's variables (frames, gc, inspect): the tripwire flags it; the reviewer checks the patch too.
5. Invalid probabilities: closed, rows must be finite, non-negative and sum to 1.
