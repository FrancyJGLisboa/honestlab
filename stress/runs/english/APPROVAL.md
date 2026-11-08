# Approval page: english

**The question:** Can we forecast tomorrow's support tickets with at least 10% lower average error than the 4-week same-weekday average you use today?

**How we will measure it:** The average miss in tickets per day, forecasting one day ahead. Lower is better. We also watch the miss on the worst days, since spikes matter for staffing.

**What we compare with:** Your current method (average of the same weekday over the last 4 weeks): about 13.3 tickets/day of average miss on the development data. It is the only method, so it is the bar.

**What counts as success:** An average miss at least 10% lower than yours (about 12.0 or less), on the development data and on the final period, confirmed by a statistical safety check.

**Data kept for the final test:** The last six months (July to December 2025). Nobody looks at it until the end.

**What is locked after approval:** the question, the measure, the data and the success rule.

**What the agent will do:** Up to 15 attempts, alone, each one recorded. Ideas include using the release schedule and recent trend. The forecast only uses what is known the day before: the release schedule, not tomorrow's active users.

**Limitations:** (1) Only 2 years of data and one split, so results can shift. (2) Tickets depend on events we don't see, so some misses can't be avoided. (3) It assumes the release schedule is truly known a day ahead.

**To approve:** in Claude Code, type `approve` in the chat. In another agent, open a terminal in this folder and run the freeze command, then answer `yes`.
