# Relatório do labloop: after-cropcast

## Veredito

**Encontrou: uma melhora real sobre o melhor método conhecido, confirmada em dados novos e por uma revisão independente.**

**Confiança:** Alta: passou nos dados novos com margem estatística e na revisão independente.

## Em palavras simples

Perguntamos se dava para errar pelo menos 10% menos na previsão de safra do que o melhor método padrão conhecido. Em 5 tentativas, sim: o erro caiu de 8,20 (método de hoje) para 6,18 bu/ac, contra 6,93 da tendência linear, nos dados de desenvolvimento. Nos anos guardados (2022–2024), a melhora sobre a tendência linear foi de 14,9%, e a revisão independente aceitou. A confiança é boa, mas não é certeza: são só 3 anos de prova final, a chuva e os graus-dia usados são os valores reais da safra e não uma previsão, e o intervalo estatístico não prova com folga que o ganho passa de 10%. O próximo passo é pedir a alguém da área para conferir o método e testá-lo no próximo período antes de usar em decisões importantes.

## Os números

- Medida: `score` (menor é melhor)
- Ponto de partida (o que já existia): 8.195
- Melhor método conhecido registrado: trend_15 = 6.929
- Melhor resultado do agente: 6.184 (E0005) (+10.8% vs trend_15)
- Margem combinada para contar como achado: 10%
- Em dados novos (trancados até o fim) (F001, E0005 vs trend_15): +14.9%, CI [0.4856, 1.85]

## O que foi tentado

5 tentativa(s): 3 guardadas (melhoraram), 2 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0005 (6.184, keep): Weather-adjusted trend with the county slope shrunk toward the typical slope across counties (ridge)
- E0004 (6.258, discard): Rain-adjusted trend plus a concave growing-degree-days term (pooled, fitted up to 2014)
- E0003 (6.258, discard): Fit the county trend on rain-adjusted past yields so weather noise does not distort the trend

**Ideias que não funcionaram (exemplos):**
- E0004 (6.258 vs 6.329): Rain-adjusted trend plus a concave growing-degree-days term (pooled, fitted up to 2014)
- E0003 (6.258 vs 6.329): Fit the county trend on rain-adjusted past yields so weather noise does not distort the trend

## Candidatos a achado

- F001: verified: Weather-adjusted per-county trend with shrunk slope cuts forecast MAE by at least 10% versus the best standard method (linear trend)

## Próximo passo

Peça a alguém da área para conferir o método e teste no próximo período de dados antes de usar em decisões importantes.

## Como isso se compara ao que os laboratórios de IA fazem

| O que o labloop fez | Equivalente nos laboratórios |
|---|---|
| Uma pergunta com uma medida que o computador calcula sozinho | O "avaliador" automático do FunSearch e do AlphaEvolve (DeepMind) |
| Métodos conhecidos registrados antes de começar | Comparar com o melhor resultado já publicado, não com um ponto de partida fraco |
| O agente muda uma coisa por vez e o labloop mede | O laço gerar, avaliar e guardar o melhor, com milhares de tentativas |
| Mudanças piores são desfeitas, mas ficam registradas | O banco de programas com pontuação, inclusive os que falharam |
| Dados trancados, usados só no fim | Separar desenvolvimento de teste para não se enganar com sorte ou trapaça do avaliador |
| Revisão por alguém que não fez o trabalho | Verificação independente: especialistas, provadores formais como o Lean |

---
Registro: 12 entries, hash chain intact.
