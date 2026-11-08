# Página de aprovação: ruido

**A pergunta:** Saber o gasto planejado de anúncio do dia (e os cliques dos dias anteriores) faz prever as vendas do dia de manhã com pelo menos 10% menos erro do que a média do mesmo dia da semana que você usa hoje?

**Como vamos medir:** pelo erro médio, em número de vendas por dia. Menor é melhor. A previsão é feita "de manhã": só usa o gasto planejado do dia, o dia da semana e o que já aconteceu nos dias anteriores. Os cliques e as vendas do próprio dia nunca entram.

**Com o que vamos comparar:** o que você faz hoje (média do mesmo dia da semana) erra 13,86 vendas por dia nos dados de iteração. Outros métodos comuns erram mais: média das últimas 8 ocorrências (14,49), suavização por dia da semana (14,24) e "mesmo dia da semana passada" (18,41). Ou seja, a barra a vencer é o seu método de hoje.

**O que conta como sucesso:** erro pelo menos 10% menor que o do seu método de hoje (cerca de 12,5 vendas ou menos), tanto nos dados de iteração quanto nos dados guardados, e com uma checagem estatística de que a diferença não é sorte.

**Dados guardados para a prova final:** de abril a dezembro de 2025 (274 dias). Ninguém olha essa parte até o fim. Os dados de iteração vão de janeiro de 2024 a março de 2025.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho (por exemplo, regressão com gasto, efeito do gasto dos dias anteriores, cliques de ontem), cada uma medida e registrada. No fim, um relatório em palavras simples diz se algo real foi encontrado, inclusive se a resposta for "não".

**Limitações:**
- Não sei se o gasto planejado de manhã é igual ao gasto final que está no arquivo. Se o planejado for diferente, o resultado real pode ser pior.
- Nos dados, o gasto e os cliques quase não se relacionam com as vendas do mesmo dia. É possível que a resposta seja que não ajudam.
- Dois anos de dados é pouco para detectar efeitos pequenos.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite `honestlab freeze` e depois `sim`.
