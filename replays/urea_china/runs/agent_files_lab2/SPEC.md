# SPEC: ureia_china

## Question
Nos três meses a partir de outubro de 2021 (out, nov, dez), o preço mundial da ureia ficou acima do que o gás natural e o próprio preço recente da ureia explicam, de modo mais forte do que em datas falsas sem evento (2010-01 a 2021-05)?

## Why it matters
Quem compra adubo (produtores, cooperativas, governos) precisa saber se a inspeção de exportação imposta pela China em outubro de 2021 pesou no preço além do custo do gás, ou se o preço subiu só pelo gás. Ganho que importa: um desvio de pelo menos 10 pontos percentuais (0,10 em escala de log) acima do normal, e fora do que as datas falsas costumam mostrar.

## Metric
`score`, em log (lê-se como fração: 0,11 = 11%). Sem data de evento: erro absoluto médio do modelo do "preço normal" em janelas de 3 meses, origens 2010-01 a 2021-06 (menor é melhor; é só a medida de partida). Com a data do evento: diferença média entre log do preço real e log do preço normal nos 3 meses a partir da data (`gap`; positivo = preço acima do normal). Direção em lab.json: minimize (vale para a medida de partida); a leitura do evento usa `event.side = up`.

## Evaluator
`eval/evaluate.py`: lê dev (e, só para datas a partir de 2021-10, os dados guardados), chama `src/model.py::predict_normal`, que recebe só os meses ANTES da data (ureia, gás europeu, gás americano) e o gás realizado dos 3 meses da janela, nunca a ureia da janela. Valida que a saída tem 3 números finitos. Roda em menos de 1 s.
Checagens de sanidade (cópia fora do projeto, dados de desenvolvimento, `notes` e saída desta sessão):
- Palpite: a média histórica erra 0,544; o modelo com respostas embaralhadas erra 0,549 (igual a chute), então não há vazamento.
- Direção: um modelo errado de propósito (+100%) erra 0,994, bem pior que o modelo (0,113).
- Aviso: o palpite "o preço fica igual ao mês anterior" erra 0,111, quase igual ao modelo com gás (0,113). Em meses normais, fora da amostra, o gás quase não acrescenta.

## Data
Fonte: Banco Mundial, "Commodity Markets: Pink Sheet", planilha mensal `CMO-Historical-Data-Monthly.xlsx` (atualizada em 3 nov 2026), https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx, baixada em 10 nov 2026. Termos de uso: não conferi o texto da licença; conferir no site do Banco Mundial antes de republicar os dados. Script: `notes/fetch_data.py` (grava dev e a parte guardada direto).
Séries usadas, em US$ nominais: Ureia (US$/t), gás natural Europa (US$/mmbtu; TTF desde abril de 2015, antes preço de fronteira), gás natural EUA (US$/mmbtu, Henry Hub). Janeiro de 1990 em diante, só meses com as três séries.
Limpeza: nenhuma além de descartar meses sem número. Ureia: "Ucrânia, prill, spot FOB Oriente Médio desde março de 2022; antes, FOB Mar Negro". A troca cai depois da janela, que por isso é de 3 meses.
Divisão: dev = 1990-01 a 2021-09 (381 meses). Guardado = 2021-10 a 2021-12 (3 meses). Ninguém abriu a parte guardada antes da aprovação.

## Baseline
`src/model.py`: regressão simples (mínimos quadrados) de log(ureia no mês) sobre log(ureia do mês anterior), log(gás europeu) e log(gás americano), ajustada só com meses antes da data. Prevê os 3 meses da janela usando as próprias previsões como "mês anterior" e o gás realizado.

## Budget
Um teste de evento: roda `honestlab event` uma única vez após a aprovação, depois `honestlab report`. Sem rodadas de tentativas. Menos de 1 minuto, sem custo.

## What counts as a finding
Só se diz "o preço subiu além do gás" se: (1) o desvio médio dos 3 meses é positivo e de pelo menos 0,10 (cerca de 10%); (2) ele fica fora do que as datas falsas mostram (pelo menos 19 datas de 2010-01 a 2021-05, em que nada de especial ocorreu); (3) uma única olhada nos dados guardados. Medido contra o método conhecido mais forte (o melhor entre os registrados).
Limite que fica escrito: o teste mostra se o preço ficou incomum naquela janela. Não separa a inspeção chinesa de outros fatos nas mesmas semanas: crise de energia na Europa, gás europeu já subindo desde meados de 2021 e corte russo no fornecimento de gás, furacão Ida nos EUA (fim de ago/2021) e falta de carvão e racionamento de energia na China (esses três vêm da sua lista e do meu conhecimento, não os conferi em fonte). O gás europeu e o corte russo entram parcialmente no "normal" pelo gás realizado; o resto não. Além disso, as datas falsas mais recentes (2021) já mostram desvio positivo (ex.: 2021-05 dá +18%), então a alta começou antes do evento.

## Prior work
Busquei na internet a série do Banco Mundial; não busquei estudos publicados sobre a inspeção chinesa (a pesquisa foi de uma só busca para achar os dados). Métodos conhecidos usados como referência: (a) passeio aleatório (o preço fica igual ao do mês anterior), o padrão em previsão de preços de commodities; (b) modelo com gás (o ponto de partida). Não há número publicado de comparação para esta medida.

## Project rules
None (projeto novo; só os arquivos criados pelo honestlab).

## Known ways to cheat this metric
1. Deixar a ureia real da janela entrar no modelo: fechado, o modelo só recebe meses anteriores e o gás; o avaliador mantém o real fora.
2. Ajustar o modelo para absorver a alta de outubro (por exemplo, usar dados depois da data): fechado, o ajuste usa só linhas antes da data.
3. Escolher a janela ou a data depois de ver o resultado: fechado, data (2021-10) e janela (3 meses) ficam trancadas no lab.json.
4. Escolher um modelo que sempre produz desvio grande: coberto pelas datas falsas, que pegam um modelo que erra muito em qualquer data.
