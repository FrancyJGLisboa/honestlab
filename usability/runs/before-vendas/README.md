# before-vendas

A labloop project. The discipline:

1. **Frame** the idea into a contract (`SPEC.md`, `eval/`, `data/`, baseline in `src/`).
   Ask your agent: *"Use the labloop-frame skill. My idea: ..."*
2. **Freeze** it yourself, in your own terminal: `labloop freeze`.
3. **Loop:** ask your agent: *"Use the labloop-experiment skill for 20 experiments."*
4. **Confirm** a candidate: *"Use the labloop-finding skill."*

Everything is recorded in `ledger.jsonl` (hash-chained), `experiments/` (every
patch, kept or not) and git. `labloop status` shows where things stand.
