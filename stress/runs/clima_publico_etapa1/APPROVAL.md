# Página de aprovação: clima_publico

**A pergunta:** usar a previsão do tempo (calor e chuva) de Pinheiros faz a previsão de vendas de amanhã errar pelo menos 10% menos do que o melhor método que não usa o tempo?

**Como vamos medir:** quantos sorvetes a previsão erra por dia, em média (para mais ou para menos). Quanto menor, melhor. A previsão é feita "na noite anterior": usa só as vendas até ontem e a previsão do tempo para o dia.

**De onde vêm os dados:** as vendas são da sua planilha (2024 e 2025). O tempo vem do Open-Meteo, um serviço público de dados do tempo, baixado em 09/11/2026: a previsão feita cerca de 24 horas antes, e o tempo que realmente fez nos dias anteriores.

**Com o que vamos comparar** (erro médio por dia, de março de 2024 a junho de 2025):
- sua média das últimas 4 vezes do mesmo dia da semana: erra 32,3 por dia;
- repetir o mesmo dia da semana passada: erra 37,6 por dia;
- Holt-Winters, um método clássico que acompanha a tendência e o padrão da semana, sem olhar o tempo: erra 27,2 por dia. É o mais forte, e é ele que precisa ser vencido.

**O que conta como sucesso:** o modelo com tempo precisa errar pelo menos 10% menos que o Holt-Winters (cerca de 24,5 por dia ou menos). Isso tem de valer nos dados de trabalho e também nos dados guardados, com uma conta de segurança que verifica que não foi sorte.

**Dados guardados para a prova final:** os últimos seis meses (julho a dezembro de 2025). Ninguém olha para eles até o fim.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas, sozinho, cada uma registrada, mesmo as que não derem certo.

**Limitações:**
- O Open-Meteo é grátis só para uso não comercial. Para usar isto no dia a dia da loja, seria preciso um plano pago ou outra fonte, por exemplo o INMET (Instituto Nacional de Meteorologia).
- A previsão do tempo de cada dia está um pouco "adiantada": as últimas horas da noite vêm de previsões feitas algumas horas depois das 20h. Isso pode deixar o resultado um pouco otimista.
- São só dois anos de vendas de uma loja. O resultado vale para ela, não para qualquer sorveteria.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite `honestlab freeze` e depois `sim`.
