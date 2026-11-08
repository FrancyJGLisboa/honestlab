# Approval page: lab

**The question:** can a rule that puts each item in a bin as soon as it arrives use fewer bins than the classic "best fit" rule?

**How we will measure it:** how many bins above the minimum possible, in percent. Lower is better.

**What we compare with:** the starting rule ("next fit", about 27% extra) and the classic "best fit" (about 8.5% extra), already registered.

**What counts as success:** at least 1.5 percentage points fewer than "best fit", on the development data and on the data kept for the end, with a statistical check.

**Data kept for the final test:** 40 longer sequences nobody looks at until the end.

**What is locked after approval:** the question, the measure, the data and the success rule.

**What the agent will do:** up to 15 attempts alone, each one measured and recorded.

**Limitations:** this is a learning example; published rules better than "best fit" exist.

**To approve:** in Claude Code, type `approve` in the chat. In another agent, open a terminal in this folder, type `honestlab freeze`, then `yes`.
