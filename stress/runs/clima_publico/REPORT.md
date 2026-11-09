# Relatório do honestlab: clima_publico

## Veredito

**Encontrou: uma melhora real sobre o melhor método conhecido, confirmada em dados novos e por uma revisão independente.**

**Confiança:** Alta: passou nos dados novos com margem estatística e na revisão independente.

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

A pergunta era se a previsão do tempo da véspera (calor e chuva) ajuda a prever as vendas de amanhã melhor que a média que você usa hoje. Somar a temperatura máxima e as horas de chuva previstas a um método padrão levou o erro médio por dia em 2024 de 32,7 (seu método) e 28,3 (o melhor método sem tempo) para 20,3. Em 2025, ano trancado até o fim e usado uma vez só, o erro ficou 27% menor que o do melhor método sem tempo, bem acima da meta de 10%. A checagem estatística e uma revisão independente aceitaram o resultado. O próximo passo é usar o método em paralelo com o seu por algumas semanas antes de comprar estoque só por ele.

## Os números

- Medida: `mae` (menor é melhor)
- Ponto de partida (o que já existia): 32.71
- Melhor método conhecido registrado: suavizacao = 28.3
- Melhor resultado do agente: 20.34 (E0003) (+28.1% vs suavizacao)
- Margem combinada para contar como achado: 10%
- Em dados novos (trancados até o fim) (F001, E0003 vs suavizacao): +27.0%, CI [4.463, 9.962]

## O que foi tentado

6 tentativa(s): 3 guardadas (melhoraram), 3 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0004 (20.2, discard): E4: somar também o total de chuva prevista no dia (mm); chuva forte pode pesar mais que horas de garoa
- E0003 (20.34, keep): E3: somar as horas de chuva previstas no horário de abertura (11h-21h) ao ajuste de tempo; chuva deve afastar clientes
- E0005 (20.49, discard): E5: efeito extra do calor forte (graus acima de 28 °C), porque o efeito da temperatura pode não ser uma reta

**Ideias que não funcionaram (exemplos):**
- E0006 (24.01 vs 20.34): E6: base que reage mais rápido (alpha 0.6, sugerido pela revisão) junto com o tempo; separa o ganho do tempo do ganho de uma base melhor
- E0005 (20.49 vs 20.34): E5: efeito extra do calor forte (graus acima de 28 °C), porque o efeito da temperatura pode não ser uma reta
- E0004 (20.2 vs 20.34): E4: somar também o total de chuva prevista no dia (mm); chuva forte pode pesar mais que horas de garoa

## Candidatos a achado

- F001: verified: Somar a temperatura máxima e as horas de chuva previstas na véspera a um método de suavização com dia da semana e feriado reduz o erro médio diário da previsão de vendas de amanhã em pelo menos 10% em relação ao melhor método sem tempo

## Próximo passo

Peça a alguém da área para conferir o método e teste no próximo período de dados antes de usar em decisões importantes.

## Como isso se compara ao que os laboratórios de IA fazem

| O que o honestlab fez | Equivalente nos laboratórios |
|---|---|
| Uma pergunta com uma medida que o computador calcula sozinho | O "avaliador" automático do FunSearch e do AlphaEvolve (DeepMind) |
| Métodos conhecidos registrados antes de começar | Comparar com o melhor resultado já publicado, não com um ponto de partida fraco |
| O agente muda uma coisa por vez e o honestlab mede | O laço gerar, avaliar e guardar o melhor, com milhares de tentativas |
| Mudanças piores são desfeitas, mas ficam registradas | O banco de programas com pontuação, inclusive os que falharam |
| Dados trancados, usados só no fim | Separar desenvolvimento de teste para não se enganar com sorte ou trapaça do avaliador |
| Revisão por alguém que não fez o trabalho | Verificação independente: especialistas, provadores formais como o Lean |

---
Registro: 19 entries, hash chain intact.
