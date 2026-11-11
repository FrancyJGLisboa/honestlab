# Step 5 demonstration: China's export checks and the urea price, October 2021

Question: from 15 October 2021 China's customs put 29 fertilizer products, urea included, under export
inspection (Announcement 2021/81 of 11 October 2021; sources: [Argus](https://www.argusmedia.com/en/news/2263001-china-customs-to-inspect-fertilizer-exports-from-15-oct),
[Global Trade Alert](https://globaltradealert.org/intervention/100224-china-new-export-inspection-requirements-for-certain-fertilisers)). Did that raise the world urea price beyond what the price of natural gas explains? Gas is the main
cost of making urea, and European gas prices were also rising fast at that time.

Data: World Bank Commodity Price Data ("Pink Sheet"), monthly, nominal US dollars, downloaded 2026-11-10
from the World Bank Commodity Markets page. Urea is f.o.b. Black Sea until February 2022 (f.o.b. Middle East
after that), so the main window stops in January 2022. Script: `analysis.py`. Result: `result.json`.

## Method, fixed before looking at the result window

1. **Normal urea price.** A model of the monthly urea price from this month's and last month's gas price
   and last month's urea price, fitted on 2005 to September 2021.
2. **The gap.** From October 2021, the model runs 4 months ahead with the real gas prices. The gap is the
   average difference between the real urea price and the model's price.
3. **Fake dates.** The same test with the "event" placed at each of 137 months from 2010 to May 2021, when
   nothing of this kind happened. A real effect should be larger than almost all of these.

## Result

| | Urea ($/t) | European gas ($/mmbtu) |
|---|---|---|
| September 2021 | 419 | 22.8 |
| October 2021 | 695 | 31.1 |
| November 2021 | 901 | 27.6 |
| December 2021 | 890 | 38.0 |

- From October 2021 to January 2022, urea was about **84% above** what the gas price explains (measured).
- Only **1 of 137** fake dates gave a gap that large (June 2011). With windows of 2 or 6 months the gap is
  about 79%, and again only 1 fake date reaches it.

## What we can and cannot say

**Can say:** the jump in October 2021 was far outside what gas prices explain, and outside almost every
other month since 2010. The fake-date test passes.

**Cannot say:** that China's export checks caused it. At least three things happened in the same weeks:

1. China's export checks (the claim).
2. China's power cuts in September and October 2021, which also cut its own urea production (widely
   reported at the time; we did not measure their size).
3. European gas reached prices far above anything in the 2005-2021 data the model learned from, so the
   model may simply not know how urea reacts at those levels.

A fake-date test cannot tell apart events that happen at the same time. That needs a comparison that only
one of them touches: for example a fertilizer that the export checks did not cover but that the power cuts
and the gas price did affect. The World Bank data has no clean candidate: DAP and TSP were covered by the
same Chinese checks, and the potash series changed source in 2020 and was hit by sanctions on Belarus in
late 2021.

## What this shows for honestlab

- The fake test does its job: it rules out "this happens all the time".
- The verdict must name its assumption. Here the honest wording is: "a jump far beyond gas costs, consistent
  with China's export checks, but not separable from China's power cuts and the record gas prices of the
  same weeks".
- This matches the limit written in ROADMAP Step 5: two events at the same time cannot be told apart.

## Limits

- Monthly data, and one price series per product. Weekly prices from industry reports would allow a sharper
  test, but they are not public.
- The model is deliberately simple. A different model of the normal price would give a different gap; the
  fake-date test checks the model too, because it runs the same model at every fake date.
- This study was run as a script, not inside an honestlab lab, so there is no locked approval page or ledger.
- The method was written before the script ran, but not blind: it was already public knowledge that urea
  prices rose sharply in late 2021. The window checks (2 and 6 months) were run after the first result.

## Inside honestlab: the same question asked by a simulated analyst

We then gave the question to honestlab itself (Claude Code plugin, Sonnet), asked by a simulated fertilizer
market analyst with no data and no statistics (`run_lab.sh`, scenario `ureia_china`; transcript in
`runs/lab.json`, the agent's report and scripts in `runs/agent_files/`).

**What the agent found (measured by it, public data):**

1. Gas explains about half the price: from October to December 2021 urea was about 97% above a gas-based rule
   learned on 2015 to September 2021 (our own model gave 84%). In 43 earlier quarters the largest gap was 50%.
2. Only urea jumped: from September to December 2021 urea rose 113%, DAP 16%, TSP 20%, potash 10%.
3. China did not cut its exports at once: UN Comtrade shows 0.74 and 0.50 million tonnes in October and November,
   above its January-August average (0.36); exports fell to almost zero only in December, after the price jump.
4. Another suspect: a large Indian urea tender closed on 3 October, twelve days before the Chinese checks.
5. Brazil felt the jump 2 to 3 months later: Comex Stat import prices of 442 $/t in October and 601 in December.

Its verdict: "not only gas, but China's part cannot be separated". That matches our own study.

**What went wrong for honestlab:**

- The agent decided the question "does not fit honestlab" and did the whole analysis outside the lab. Nothing
  was approved or locked, no ledger entry was written, and it saw the October-December numbers before choosing
  its method. It said so in its report.
- The simulated person was confused 5 times (for example by "contrafactual" and "janelas falsas") and asked 13
  messages. At the end it still asked whether something was "found", because the report had no honestlab verdict.

**What this shows:** honestlab's framing has a path for "find a better version" and none for "did this event
change that number". Fake tests exist only as a check on a finding. A question about an event needs its own
path: lock the event date, the window, the model of the normal price and the fake dates first, then compute
the gap and its rank among the fake dates. That is the next piece of ROADMAP Step 5.

## Run 2: the same analyst after the event test was added

Same scenario and model (`run_lab.sh lab2`; transcript `runs/lab2.json`, the agent's files in
`runs/agent_files_lab2/`). 20 minutes, 13 messages from the simulated person, 3 confused replies (5 in run 1).

**What changed (measured in the transcript and the lab's ledger):**

1. The agent called it an "event at a date" question in its first reply and stayed in honestlab.
2. October to December 2021 went to the sealed held-out data. The approval page named the date, the 3-month
   window, the model of the normal price (European and US gas and last month's urea), the fake dates
   (2010 to May 2021) and one allowed look. The person approved it in the chat.
3. `honestlab event` ran once: gap 0.571 in log units (about 77% above normal), 1 of 137 fake dates as large
   or larger, chance about 1.5%. Report verdict: "Incomum ... Isso sozinho não prova que o evento foi a causa."
4. The agent measured that the normal-price model predicts ordinary months no better than "same as last
   month" (both about 11% error), and wrote it on the approval page.
5. Follow-up looks (other fertilizers, China's exports from UN Comtrade) are in the report under "SÓ UM
   INDÍCIO, NÃO É PROVA", outside the approved test. Only urea was unusual: DAP 13% of fake dates, TSP 6%,
   potash 47%.

**What still went wrong:**

- A second, formal test (urea against potash and phosphate) needed a new lab, and honestlab's lock on the
  first lab also blocked the new one in the same session. The person could not open a new session, so the
  agent did an informal look instead. honestlab needs a way to start a second question from the first.
- The approval page promised "at least 10% above normal", but the event test did not check the margin.
  Fixed after this run: the event test now also requires `finding.min_effect` (this run passes it: 0.571 > 0.1).
- The page said "in percent" but the report gave log units. The person was confused by "escala de log".
- The simulated person copied the lab into its home folder. We moved that copy out of the home folder.
