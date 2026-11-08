# Página de aprovação: impaciente

**A pergunta:** Dá para prever as vendas diárias da sorveteria usando o tempo (temperatura, chuva), o dia da semana e feriados, e errar pelo menos 5% menos que o melhor método simples conhecido?

**Como vamos medir:** Erro médio por dia, em unidades vendidas (quanto a previsão erra, em média). Menor é melhor. Cada dia é previsto usando só o que se sabia antes dele.

**Com o que vamos comparar:** (nos dados de desenvolvimento, erro médio em unidades por dia)
- Vendas do mesmo dia da semana passada: 34,1 (ponto de partida)
- Média dos últimos 8 mesmos dias da semana, sem tempo: 29,5
- Reta de vendas contra temperatura (ideia de livro-texto): **17,8**, o melhor atual e o número a bater
- Você não disse o que usa hoje; se for outro método, me conte e eu o registro.

**O que conta como sucesso:** Errar pelo menos 5% menos que o melhor acima (cerca de 16,9 ou menos), nos dados de desenvolvimento e também nos dados guardados para o final, com uma verificação estatística de que não foi sorte.

**Dados guardados para a prova final:** Os 183 dias de 01/07/2025 a 30/12/2025. Ninguém olha esses dados até o fim. O resto (01/01/2024 a 30/06/2025) é usado para testar ideias.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** Até 15 tentativas sozinho, cada uma registrada, com ideias como combinar dia da semana, feriado, temperatura e chuva, e ajustar o nível recente de vendas.

**Limitações:**
- A temperatura e a chuva parecem ser as medidas do próprio dia, não a previsão do tempo. Na prática você teria só a previsão de véspera, então o resultado real tende a ser um pouco pior.
- Só há dois anos de dados, e a prova final cobre só o 2º semestre de 2025.
- Errar para menos ou para mais pesa igual aqui; você não indicou que um é pior que o outro.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite `honestlab freeze` e depois `sim`.
