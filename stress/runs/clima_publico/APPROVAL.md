# Página de aprovação: clima_publico

**A pergunta:** a previsão do tempo para amanhã (calor e chuva, como era prevista na véspera) ajuda a prever as vendas de amanhã da sorveteria pelo menos 10% melhor do que o melhor método sem tempo?

**Como vamos medir:** o erro médio por dia, em unidades de venda da sua planilha (quanto a previsão erra para mais ou para menos). Menor é melhor. Cada dia é previsto só com o que se sabia até a véspera.

**De onde vêm os dados:** as vendas vêm da sua planilha (2024 e 2025). A previsão do tempo vem do serviço público Open-Meteo (modelo americano GFS, da agência NOAA), para Pinheiros, baixada em 09/11/2026. São as previsões feitas na véspera, não o tempo que de fato aconteceu.

**Com o que vamos comparar** (erro médio por dia em 2024, contando semanas completas):
- Seu método de hoje, a média das últimas 4 vezes do mesmo dia da semana: erra cerca de **32,7**.
- Vendas do mesmo dia da semana passada: **40,1**.
- Média das últimas 8 vezes do mesmo dia da semana: **30,5**.
- Um método padrão que acompanha a tendência e ajusta para dia da semana e feriado: **28,3**. Este é o mais forte e é a régua.

**O que conta como sucesso:** um método com tempo precisa errar pelo menos 10% menos que o mais forte (cerca de 25,5 ou menos). Isso vale em 2024 e depois em 2025, com uma checagem estatística para descartar sorte.

**Dados guardados para a prova final:** todo o ano de 2025. Ninguém olha esses dados até a prova final, nem eu.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho, cada uma registrada, mudando só o método de previsão.

**Limitações:**
- O tempo é de um modelo global para a região de Pinheiros, não de uma estação na sua rua.
- Uso o serviço gratuito só para este teste. Para usar todo dia no negócio, é preciso uma assinatura paga do Open-Meteo ou os dados diretos da NOAA.
- São só dois anos de vendas. Um resultado positivo vale para esta loja e este período.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite `honestlab freeze` e depois `sim`.
