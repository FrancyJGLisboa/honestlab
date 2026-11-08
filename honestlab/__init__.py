"""honestlab: a disciplined, agent-agnostic experiment loop.

The discipline lives in this package, not in any coding agent: a frozen,
hash-checked evaluator, an append-only hash-chained ledger, automatic keep or
revert of every change, and a gated path from candidate to finding. Claude
Code, Codex CLI and Copilot CLI only get thin adapters (skills, instructions
and hooks) that call into it.
"""

__version__ = "0.5.0"
