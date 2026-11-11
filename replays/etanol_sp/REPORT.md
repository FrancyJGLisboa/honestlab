# Relatório do honestlab: etanol_sp

## Veredito

**Não mostrou efeito: mudanças desse tamanho também acontecem em datas comuns.**

**Aprovação:** feita por você num terminal.

## Em palavras simples

Nas 4 semanas depois do aumento do ICMS, o etanol em São Paulo ficou 1,2% acima do preço da semana anterior, e em Minas Gerais, que não mudou o imposto, 2,9% acima. A diferença SP menos MG foi de -1,7%: SP subiu menos, não mais. Em 466 de 506 semanas comuns, a diferença foi igual ou maior, então não há sinal do imposto além do movimento normal. O teste conseguiria ver um repasse inteiro (cerca de 2,8%): só 1,6% das semanas comuns chegam a isso. Um repasse pequeno, abaixo de cerca de 1,9%, ficaria escondido no ruído.

## Os números

- Medida: `gap` (maior é melhor)
- Ponto de partida (o que já existia): -0.01248
- Melhor método conhecido registrado: baseline = -0.01248
- Melhor resultado do agente: -0.01248 (baseline) (+0.0% vs baseline)
- Margem combinada para contar como achado: 0.01 gap
- Modo: prova (só guardou tentativas cuja melhora é improvável de ser sorte)
- Teste de evento em 2023-07-02: diferença -0.01692; 466 de 506 datas falsas deram uma diferença igual ou maior (chance 0.921, limite 0.05). NÃO PASSOU: mudanças desse tamanho também acontecem em datas comuns
- Comparado com o controle 'mg' (uma série parecida que o evento não atinge): série atingida 0.01198, controle 0.0289. A diferença é o que foi testado. O controle mudou tanto quanto ou mais em 147 de 506 datas falsas

## O que foi tentado

0 tentativa(s): 0 guardadas (melhoraram), 0 desfeitas, 0 com erro. Todas ficam registradas.

## Próximo passo

Com estes dados não dá para ver um efeito do evento. Opções: dados mais frequentes (semanais), outra janela aprovada antes, ou aceitar que o efeito, se existe, é pequeno.

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
Registro: 4 entries, hash chain intact.
