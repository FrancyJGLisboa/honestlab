# Event test with a control on real data: São Paulo's ethanol tax, July 2023

Question: from 1 July 2023 São Paulo raised the ICMS tax on hydrated ethanol from 9.57% to 12% (Informativo
SFP, DOE-SP 30 June 2023; sources: [netcpa](https://netcpa.com.br/noticias/urgente-cpa-icmssp-aliquota-do-etanol-hidratado-combustivel-passa-a-ser-12-a-partir-de-1o072023/16193),
[novacana](https://www.novacana.com/n/etanol/impostos/governo-sao-paulo-aumenta-icms-etanol-9-5-12-030723)).
Did the pump price in São Paulo rise more than in Minas Gerais, which did not change its ethanol tax then?
(No change for Minas Gerais in July 2023 was found; its last change found was 18 July 2022.)

Data: ANP weekly retail price survey, mean hydrated-ethanol price per state, read from the TerraPulse MCP
(`fetch.sql`). ANP's licence (CC BY-ND 3.0) does not allow changed copies, so the prices are not in this
repository; `fetch.sql` gets them again.

## How it ran (all inside honestlab)

1. Plan written and recorded in the lab's git before the July 2023 prices were fetched (`lab_git_log.txt`:
   commit "Plano registrado antes de buscar os dados de julho de 2023", 10:56:36, then baseline, freeze and
   the event test). The agent did see the 4 held-out weeks when it wrote them into the lab.
2. Treated series: São Paulo. Control: Minas Gerais (`"control": "mg"`). Window: the 4 survey weeks from
   2 July 2023. Normal price: the week before (`model.py`). Gap: mean log price in the window minus the log
   normal price. Tested: São Paulo's gap minus Minas Gerais's gap.
3. Fake dates: 506 survey weeks from February 2013 to May 2023, without survey gaps, and without windows that
   touch the known ethanol tax changes in either state (15 Jan 2021, 15 and 18 July 2022).
4. Bar: São Paulo at least 0.01 (about 1%) above Minas Gerais, and at most 5% of fake dates as large.
5. Approval: given by the operator (Claude) through the terminal path the tests use, not by a person. This
   is a demonstration of the mechanism; the person did not read the page first.

## Result (measured)

| | Gap over 4 weeks |
|---|---|
| São Paulo (treated) | +1.2% |
| Minas Gerais (control) | +2.9% |
| Difference tested | -1.7% |

- 466 of 506 fake dates gave a difference as large or larger (chance about 0.92). **Not passed.**
- The control was calm by its own history: 147 of 506 fake dates moved Minas Gerais as far.
- Verdict in the lab's report: "Não mostrou efeito: mudanças desse tamanho também acontecem em datas comuns."

## Could the test have seen the tax?

Yes, if the tax was passed on in full. With the tax inside the price, 9.57% to 12% raises the price by about
2.8% (0.9043 / 0.88). Only 1.6% of the fake dates reach a difference that large, so a full pass-through would
have passed. Half of it (about 1.4%) would not: the 95th percentile of the fake differences is 1.9%.

Reading rule: in this data, a tax effect on one state's ethanol price is visible only above about 2%.

## What we can and cannot say

- **Can say:** in the 4 weeks after the change, São Paulo's ethanol price did not rise more than Minas
  Gerais's. A full pass-through of the tax is unlikely in that window.
- **Cannot say:** that there was no effect. A partial or later pass-through is possible. Both states also
  jumped about 5 to 6% in the first week of July 2023: something hit both (a national cause is likely; we did
  not check which). The control removes it, which is its job.

## What this showed for honestlab

- The control path works on real data: the shock that hit both states did not count as São Paulo's effect.
- It found a bug: the report called this gap "unusual but smaller than the margin" when it was not unusual.
  Fixed, with a test case (`tests/event_test.py`).
