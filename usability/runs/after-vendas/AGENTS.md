# labloop in this folder

This folder runs a disciplined discovery loop with **labloop**. To start or continue,
use the `labloop` skill (the person can just say "Use labloop: <idea>"). Run
`labloop status` to see where things stand and the exact paths.

Rules (enforced by labloop and by hooks):
1. Talk to the person in their language and plain words; they only answer a few
   questions and approve one page by typing `labloop freeze` themselves.
2. Never run `labloop freeze` or `labloop unfreeze`, and never commit, reset or rebase git.
3. After the freeze, change only the editable paths; measure every change with
   `labloop run -m "<hypothesis>"`.
4. Never read the held-out data or score on it yourself.
5. Never claim more than `labloop report` says. If a rule blocks you, explain it and ask.
