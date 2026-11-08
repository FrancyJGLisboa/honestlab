# Página de aprovação: plugin-vendas

**A pergunta:** Dá para prever as vendas de amanhã da sua sorveteria usando o tempo (temperatura e chuva), o dia da semana e feriados, com pelo menos 10% menos erro do que o melhor método simples que já existe?

**Como vamos medir:** pelo erro médio da previsão, em sorvetes (unidades) por dia, calculado dia a dia como se fosse de verdade: para prever cada dia, só se usa o que já se sabia antes dele. Quanto menor, melhor.

**Com o que vamos comparar** (erro médio por dia nos dados de teste):
- Seu método de hoje (média do mesmo dia da semana, últimas 4 vezes): **28,3**
- Média simples dos últimos 28 dias: **26,8** (o mais forte hoje; é ele que precisamos bater)
- Mediana dos últimos 4 mesmos dias da semana: 28,4
- Venda do mesmo dia da semana passada: 34,4

**O que conta como sucesso:** errar pelo menos 10% menos que o melhor método acima (ou seja, chegar a cerca de 24,1 ou menos), tanto nos dados de teste quanto nos dados guardados, e passar numa verificação estatística de que não foi sorte.

**Dados guardados para a prova final:** julho a dezembro de 2025 (183 dias). O período de teste é janeiro/2024 a junho/2025. Ninguém olha os dados guardados até o fim.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas, sozinho, cada uma registrada.

**Limitações:**
1. A planilha tem o tempo que realmente aconteceu, não a previsão do tempo. Na vida real a previsão erra um pouco, então o ganho real pode ser menor.
2. Só há 2 anos de dados; o período guardado é o segundo semestre de 2025, e o resultado pode não valer para outras épocas ou situações novas (obra, promoção, evento).
3. Não busquei na internet métodos publicados; os comparativos são os métodos simples usuais.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite o comando de congelar do honestlab e depois `sim`.
