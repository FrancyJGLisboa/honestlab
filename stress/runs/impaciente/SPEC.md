# SPEC: impaciente

<!-- Fill every section. `honestlab check-spec` fails while any TODO remains.
     The honestlab skill fills this in with you. -->

## Question
Usar temperatura, chuva e feriado (do próprio dia) reduz em pelo menos 5% o erro médio diário de previsão das vendas da sorveteria, em comparação com o melhor método sem tempo ou o melhor método simples conhecido?

## Why it matters
Prever melhor as vendas diárias ajuda a comprar insumos e escalar pessoal, evitando falta ou sobra de sorvete. Menos de 5% de melhora no erro não muda decisões na prática (margem escolhida por padrão; a pessoa não indicou outra).

## Metric
Erro absoluto médio (MAE) em unidades vendidas por dia; menor é melhor. No lab.json a métrica chama-se `score`.

## Evaluator
eval/evaluate.py faz previsão dia a dia (walk-forward): para cada dia, src/model.py recebe só os dias anteriores (com vendas) e as características do dia (dia da semana, feriado, temperatura máxima, chuva), sem as vendas do dia. Saída precisa ser um número finito entre 0 e 5000, senão a avaliação falha. Os primeiros 60 dias de dev só servem de histórico. Roda em segundos.

## Data
vendas.csv da pessoa, 730 dias (2024-01-01 a 2025-12-30). dev = 2024-01-01 a 2025-06-30 (546 dias, 486 avaliados). Guardado para a prova final = 2025-07-01 a 2025-12-30 (183 dias), período posterior e novo. Na prova final os dias de dev entram como histórico, como na vida real.

## Baseline
src/model.py começa prevendo as vendas do mesmo dia da semana na semana anterior, sem usar tempo.

## Budget
Até 15 experimentos, cada um em segundos; sem custo de dinheiro. Só src/ pode ser alterado.

## What counts as a finding
Erro (MAE) pelo menos 5% menor, em termos relativos, que o melhor método conhecido registrado (`honestlab reference list`), tanto nos dados de desenvolvimento quanto nos guardados para o final, com verificação estatística (bootstrap pareado, alpha 0,05). Fixado em lab.json: min_effect 0.05, relative, compare_to strongest.

## Prior work
Busca web rápida (1 consulta). Comparações de regressão linear/XGBoost de vendas de sorvete contra temperatura aparecem em trabalhos como o artigo da AIUB (dspace.aiub.edu/jspui/handle/123456789/2663), sem números comparáveis aos nossos dados. Referências registradas: semana passada (naïve sazonal), média dos últimos 8 mesmos dias da semana (sem tempo) e reta de vendas contra temperatura (ideia de livro-texto). O método atual da pessoa não foi informado.

## Known ways to cheat this metric
1) Usar a venda do próprio dia: o avaliador entrega só o passado e remove `vendas` do dia. 2) Ler os dados da prova final ou os dias futuros dentro do modelo: o histórico é cortado a cada dia e a pasta da prova final é protegida e vigiada. 3) Sorte em um período curto: 486 dias avaliados, comparação pareada e prova final em período novo. 4) Previsão fora de faixa ou inválida: números não finitos ou fora de 0-5000 derrubam a avaliação.
