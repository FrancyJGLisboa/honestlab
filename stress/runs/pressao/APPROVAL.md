# Página de aprovação: pressao

**A pergunta:** Saber o gasto com anúncio do dia ajuda a prever as vendas do dia melhor do que a média do dia da semana, que é o que você usa hoje?

**Como vamos medir:** pelo erro médio da previsão, em unidades de vendas por dia. Menor é melhor. A previsão de cada dia usa só o passado, o dia da semana e o gasto planejado; nunca as vendas nem os cliques daquele dia.

**Com o que vamos comparar:** com a média do dia da semana (o seu método), que erra cerca de 14,9 vendas por dia nos dados de desenvolvimento. Também há a média geral, só como referência.

**O que conta como sucesso:** o erro cair pelo menos 10% em relação à média do dia da semana, tanto nos dados de desenvolvimento quanto nos dados guardados, com uma checagem estatística para não ser sorte.

**Dados guardados para a prova final:** os últimos 146 dias (20%), separados sem serem abertos. Ninguém olha até o fim.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho (modelos com gasto, efeito acumulado, saturação etc.), cada uma registrada.

**Limitações:** (1) nos dados de desenvolvimento, a relação linear entre gasto e vendas já parece quase nula, então "não encontrou" é um resultado provável e válido; (2) mostrar que prevê melhor não prova que o anúncio causa as vendas; (3) são só 2 anos de dados de uma campanha.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, rode o comando de congelar do honestlab e responda `sim`.
