# A inspeção chinesa de fertilizantes (outubro de 2021) subiu a ureia além do que o gás explica?

Data do relatório: 10/11/2026.

## Em palavras simples

- **Pergunta:** a inspeção chinesa às exportações de fertilizantes, que começou em 15/10/2021, subiu o preço da ureia além do que o gás natural explica?
- **O que aconteceu:** de outubro a dezembro de 2021, a ureia ficou cerca de 97% acima do que uma regra baseada no gás (2015 a set/2021) esperava. Nenhum dos 43 trimestres antigos testados chegou perto: o maior desvio foi 50%.
- **Veredito:** **não foi só o gás**, mas **não é possível separar a parte da China**. Ela é uma suspeita plausível. A Índia (compra grande fechada em 3/out) e a Europa (fábricas paradas em setembro por causa do gás) chegaram na mesma época.
- **Quanto confio:** nos números, muito (são medidos). Na causa, pouco (é inferência).
- **Próximo passo:** obter preços semanais de ureia de out–dez/2021 (Argus, CRU ou Profercy) e o preço do carvão chinês.

Este relatório **não** usou o ciclo de teste e aprovação do honestlab: a pergunta pede uma comparação com um cenário imaginado, com só 3 meses na janela de interesse, e isso não se encaixa em "achar uma versão melhor". **Nada aqui é uma prova no sentido formal do honestlab.** O laboratório foi criado nesta pasta, mas nunca foi aprovado (trancado) nem rodou experimentos.

## O que foi medido

### 1. Quanto o gás explica (arquivo `notes/excess.py`)
- Regra: o preço da ureia segue o gás (EUA e Europa) em proporção fixa, aprendida de jan/2015 a set/2021.
- Em out–dez/2021 o preço real ficou 97% acima do esperado. Só com o gás europeu: 101%. Só com o gás dos EUA: 170%.
- Comparação com 43 trimestres antigos (regra aprendida só com o passado de cada um): desvio típico 15%, máximo 50%.
- Acrescentando o carvão australiano à regra (`notes/excess_coal.py`): continua 97%.

### 2. Setembro → outubro de 2021 (Banco Mundial)
| Preço | Setembro | Outubro | Variação |
|---|---|---|---|
| Ureia (US$/t) | 418,8 | 695 | +66% |
| Gás da Europa (US$/mmbtu) | 22,84 | 31,05 | +36% |
| Gás dos EUA (US$/mmbtu) | 5,11 | 5,48 | +7% |
| Carvão australiano (US$/t) | 185,7 | 224,5 | +21% |

### 3. Outros fertilizantes (Banco Mundial)
| Variação | Set→Out | Set→Dez |
|---|---|---|
| Ureia | +66% | +113% |
| DAP | +5% | +16% |
| TSP | +8% | +20% |
| Cloreto de potássio | +6% | +10% |

Só a ureia disparou. Li que a inspeção cobria 29 produtos, mas não conferi se os fosfatos estavam na lista.

### 4. Exportações de ureia da China (UN Comtrade, código 310210)
Milhões de toneladas por mês, 2021: média jan–ago 0,36; setembro 1,09; outubro 0,74; novembro 0,50; dezembro 0,035. A soma jan–nov (5,24) bate com o Global Times (5,26). Dezembro pode estar incompleto. A China ainda exportou mais que a média em outubro e novembro, e o corte físico só aparece em dezembro, depois do salto de preço.

### 5. Brasil (Comex Stat, ureia NCM 31021010, preço de embarque)
- Preço médio de importação (US$/t): set 438; out 442; nov 476; dez 601. O Brasil sentiu o salto com 2 a 3 meses de atraso (inferência: compras fechadas com antecedência).
- A China foi cerca de 1% das compras brasileiras em jul–set (22 mil de 1,89 milhão de t) e quase zero em out–dez (1,6 mil de 2,41 milhões). O preço subiu em todas as origens (por exemplo Catar de 403 para 511 US$/t).

### 6. Linha do tempo (notícias do setor)
- 15–17/set: CF Industries para duas fábricas no Reino Unido; Yara com cerca de 40% da amônia europeia parada na semana de 20/set por causa do gás.
- 19/set a 3/out: compra grande da Índia.
- 15/out: início da inspeção chinesa (Argus, Global Trade Alert).
- Dezembro: exportações chinesas quase a zero.
Datas variam um ou dois dias entre fontes.

## Por que não dá para separar a China

1. **Um ponto por mês.** Setembro e a primeira metade de outubro já vinham subindo, e a inspeção começou no meio de outubro.
2. **Causas juntas.** China, Índia e Europa agiram quase ao mesmo tempo.
3. **O gás age por dois caminhos.** Como custo (que a regra enxerga) e como falta de produto, quando fábricas europeias pararam (que a regra não enxerga). Parte dos 97% "não explicados" pode ser gás pelo segundo caminho.
4. **A regra é simples** e o gás europeu saiu da faixa que ela conhece. Uma regra melhor poderia mudar o tamanho da sobra. Não testei.
5. **Qualidade dos dados.** O carvão usado é o australiano, não o chinês. A ureia do Banco Mundial é a do Oriente Médio, não a brasileira. Dezembro de exportações chinesas pode estar incompleto.

## O que falta para separar as causas
- Preços semanais ou diários de ureia de set–dez/2021 (Argus, CRU, Profercy). Mostrariam a semana do salto frente a 3/out e 15/out. Não achei fonte gratuita.
- Preço do carvão chinês e preço doméstico da ureia na China.
- Detalhes das compras da Índia e das paradas europeias, com datas.

## Fontes e arquivos
- Banco Mundial, Commodity Price Data (Pink Sheet), preços mensais, CC BY 4.0 (a confirmar nos termos do site), atualizado em 03/11/2026: https://www.worldbank.org/en/research/commodity-markets. Cópia: `notes/dados_baixados/worldbank_pink_sheet_2026-11-03.xlsx`.
- UN Comtrade (API pública de prévia), China, exportações, código 310210, baixado em 10/11/2026. Os valores estão neste relatório (a consulta não foi salva em arquivo).
- Comex Stat (MDIC, Brasil), baixado em 10/11/2026: arquivos `notes/dados_baixados/comexstat_*.json`.
- Inspeção chinesa: [Argus](https://www.argusmedia.com/en/news/2263001-china-customs-to-inspect-fertilizer-exports-from-15-oct), [Global Trade Alert](https://globaltradealert.org/intervention/100224-china-new-export-inspection-requirements-for-certain-fertilisers), [Global Times](https://globaltimes.cn/page/202112/1242825.shtml).
- Paradas europeias: [World Fertilizer](https://www.worldfertilizer.com/nitrogen/17092021/cf-industries-halts-operations-at-uk-facilities-due-to-high-natural-gas-prices/), [ICIS](https://icis.com/explore/resources/news/2021/09/17/10686151/ammonia-producer-yara-cuts-production-on-high-gas-prices).

## Aviso sobre a janela de interesse
Ao conferir a cobertura dos dados, vi os valores de out–dez/2021 antes de definir qualquer regra. Por isso essa janela não estava "escondida" de mim. A comparação com trimestres antigos, que usa só o passado de cada um, não depende disso.
