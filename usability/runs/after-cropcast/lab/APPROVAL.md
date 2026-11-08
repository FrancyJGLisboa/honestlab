# Página de aprovação: after-cropcast

**A pergunta:** Dá para errar pelo menos 10% menos na previsão de safra por município do que o melhor método conhecido?

**Como vamos medir:** pelo erro médio da previsão, em bu/ac, em cada município e ano. Menor é melhor.

**Com o que vamos comparar:** erro médio nos dados de desenvolvimento (2015–2021), em bu/ac:
- O que você usa hoje (média das 5 últimas safras): **8,20**
- Tendência linear por município, método padrão da área: **6,93** (já 15% melhor que o atual)
- Tendência + chuva e graus-dia, outro método padrão: **6,94**

O melhor método conhecido é a tendência linear (6,93). Para valer como descoberta, é preciso chegar a cerca de **6,24** ou menos, e não apenas bater o método de hoje.

**O que conta como sucesso:** erro pelo menos 10% menor que o do melhor método conhecido da lista acima, tanto nos dados de desenvolvimento quanto nos dados guardados, com um teste estatístico de segurança para não ser sorte.

**Dados guardados para a prova final:** os anos 2022–2024. Ninguém olha para eles, nem eu, até o fim. Os experimentos usam só 1995–2021.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho, mudando só o arquivo `cropcast/forecast.py`. Cada tentativa fica registrada.

**Limitações:**
- A chuva e os graus-dia são os valores reais da safra, não uma previsão feita antes. O teste é um pouco otimista em relação ao uso real.
- São só 3 anos na prova final (240 casos), então a conclusão final tem margem de dúvida.
- Se não der para chegar a 10%, o relatório diz quanto foi possível e o que isso significa.

**Para aprovar:** abra um terminal nesta pasta, digite `labloop freeze` e depois `sim`.
