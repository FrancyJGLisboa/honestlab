# SPEC: etanol_sp

<!-- Fill every section. `honestlab check-spec` fails while any TODO remains.
     The honestlab skill fills this in with you. -->

## Question
O aumento do ICMS do etanol hidratado em São Paulo, de 9,57% para 12% a partir de 1º de julho de 2023,
subiu o preço do etanol na bomba em SP mais do que em Minas Gerais, nas 4 semanas seguintes?

## Why it matters
É um teste de evento com dados reais e um controle limpo: o mesmo produto num estado vizinho que não mudou o
imposto na mesma data (nenhuma mudança encontrada para MG em julho de 2023). Se o imposto for repassado
inteiro, o preço sobe cerca de 2,7% (preço com imposto "por dentro": 0,9043 / 0,88 = 1,0276).

## Metric
`gap`: média do log do preço nas 4 semanas a partir da data, menos o log do preço normal (o preço da semana
anterior). O teste usa a diferença SP menos MG. Sem data, a medida inicial é menos o erro de uma semana.

## Evaluator
`eval/evaluate.py`. Lê `HONESTLAB_EVENT_DATE` e `HONESTLAB_EVENT_SERIES` (treated = SP, mg = MG).

## Data
ANP, Levantamento de Preços de Combustíveis, preço médio semanal de revenda do etanol hidratado (R$/l), SP e
MG, via TerraPulse (tabela anp_fuel_prices_weekly, versão mais recente de cada observação). Licença CC BY-ND
3.0: os dados não vão para o repositório público. Dev: semanas de 30/12/2012 a 25/06/2023. Holdout: as 4
semanas de 02/07/2023 a 23/07/2023, buscadas só depois deste arquivo estar escrito e registrado.

## Baseline
O preço normal é o da última semana (passeio aleatório). Nada é ajustado depois da aprovação.

## Budget
Uma olhada nos dados guardados. Nenhuma tentativa de melhorar o modelo.

## What counts as a finding
A diferença SP menos MG nas 4 semanas é de pelo menos 0,01 em log (cerca de 1%), e no máximo 5% das 506
datas falsas dão uma diferença igual ou maior. Datas falsas: toda semana de 03/02/2013 a 28/05/2023 com as 5
semanas necessárias na pesquisa, exceto janelas que tocam mudanças de ICMS do etanol já conhecidas em SP ou
MG (15/01/2021, 15/07/2022, 18/07/2022). Outras mudanças desconhecidas podem estar entre as datas falsas; isso
torna o teste mais difícil de passar, não mais fácil. Outros fatos da mesma janela: o ICMS fixo da gasolina
(junho de 2023, nacional) e os preços da Petrobras atingem SP e MG; o controle remove o que atinge os dois.

## Prior work
Notícias da época estimaram alta de R$ 0,11 por litro (Reuters, citada por netcpa.com.br).

## Project rules
Nenhuma.

## Known ways to cheat this metric
Escolher a janela ou o controle depois de ver o resultado. Por isso ambos estão fixados aqui.
