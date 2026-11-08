# Página de aprovação: planilha_br

**A pergunta:** Dá para prever o tempo de entrega de cada pedido, usando hora, dia, distância e chuva, errando pelo menos 10% menos do que prometer sempre o tempo médio?

**Como vamos medir:** pelo erro médio em minutos entre o que foi previsto e o que realmente levou. Quanto menor, melhor. Atrasar e adiantar pesam igual.

**Com o que vamos comparar:** (erro médio nos dados de teste, em minutos)
- Prometer a média, como você faz hoje: **11,24 min**.
- Prometer a mediana: 11,23 min.
- Modelo clássico simples (efeito da hora + distância + chuva): **4,85 min**, ou seja, já erra cerca de 57% menos que a média de hoje.

**O que conta como sucesso:** como o método simples já passa de longe da sua meta, a barra é bater **ele** em pelo menos 10% (chegar a cerca de 4,36 min ou menos), nos dados de teste e também nos dados guardados, com uma checagem estatística de que não foi sorte. Seus 15% contra a média de hoje já foram superados pelo método simples; a barra aqui é mais dura de propósito.

**Dados guardados para a prova final:** os pedidos de julho a dezembro de 2025 (cerca de 900). Ninguém olha antes do fim. Os pedidos até junho de 2025 (3.085) são usados para experimentar.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho, cada uma registrada.

**Limitações:**
- Não sei se a chuva da planilha é a que de fato caiu ou a previsão feita na hora do pedido. Se for a que caiu, os números ficam um pouco otimistas.
- Há só hora, dia, distância e chuva; sem trânsito, restaurante ou entregador, o erro tem um piso que não dá para baixar.
- Os dados cobrem 2024 e 2025; mudanças futuras (nova região, nova frota) podem mudar os resultados.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite `honestlab freeze` e depois `sim`.
