# Página de aprovação: plugin-cropcast

**A pergunta:** dá para criar uma previsão de safra por condado que erre pelo menos 10% menos que o melhor método simples conhecido, usando só o que se sabe antes da safra?

**Como vamos medir:** erro médio absoluto em bu/ac, por condado e depois a média dos 80 condados. Quanto menor, melhor. Cada previsão usa só safras de anos anteriores.

**Com o que vamos comparar** (nos dados de desenvolvimento, 2015–2021):
- Método de hoje, média das últimas 5 safras: **8,20**
- Média olímpica de 5 anos (tira a maior e a menor): 8,23
- Suavização exponencial: 8,00
- **Tendência linear por condado (15 anos): 6,93**, o melhor método conhecido

Atenção: só trocar a média de 5 anos pela tendência linear já dá 15% menos erro. Isso é um método conhecido, não uma descoberta. Por isso a régua é contra a tendência.

**O que conta como sucesso:** erro de 6,24 bu/ac ou menos nos dados de desenvolvimento (10% abaixo da tendência), confirmado nos dados guardados para o fim, com um teste estatístico de segurança para a melhora não ser sorte.

**Dados guardados para a prova final:** as safras de 2022 a 2024. Ninguém olha esses dados até o fim. Eles são usados no máximo 3 vezes. As ideias são testadas com 1995–2021.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho, mexendo só em `cropcast/forecast.py` (só numpy, função pura). Cada tentativa fica registrada, inclusive as que falham.

**Limitações:**
1. A chuva e a temperatura da própria safra ficam escondidas, porque só se conhecem no fim dela. Se a mesa tiver esses números antes da colheita, vale uma segunda rodada. O clima de anos anteriores pode ser usado.
2. Só 7 anos de teste na fase de desenvolvimento e 3 na prova final. Os condados sofrem o mesmo clima nos mesmos anos, então a certeza estatística é menor do que os 80 condados sugerem.
3. Se nada passar da régua, o resultado é "não encontrou", e isso também é uma resposta útil.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite `honestlab freeze` e depois `sim`.
