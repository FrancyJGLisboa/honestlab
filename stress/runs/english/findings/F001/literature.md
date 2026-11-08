# F001: prior work

## How I searched
One web search on 2026-11-08: "support ticket volume forecasting methods seasonal naive regression release day effect benchmark". Results were mostly practitioner guides and a Porto master's thesis; no controlled benchmark.

## Closest existing work
- Practitioner guides ([supportbench](https://www.supportbench.com/?p=27587), [supportbench](https://www.supportbench.com/?p=24242), [cobbai](https://cobbai.com/blog/customer-support-forecasting)): trailing-average baselines adjusted for known events such as releases (+15% to +50% suggested lifts). Similar in spirit to the release lift used here; the lift here is learned from past releases in the data.
- [Porto thesis](https://repositorio-aberto.up.pt/bitstream/10216/154576/2/648596.pdf): Lasso/Ridge regression and other models for ticket volume. Different method.
- Per-user (rate-based) scaling is a standard idea in demand forecasting; not searched separately.

## Assessment
Similar work exists. The ingredients (event adjustment, scaling by exposure, trailing averages) are standard, so this is not a novel method. The finding is practical: for this team's data these ingredients clearly beat the current 4-week weekday average. Not checked: SARIMA or regression baselines on this data, and other ticket datasets.
