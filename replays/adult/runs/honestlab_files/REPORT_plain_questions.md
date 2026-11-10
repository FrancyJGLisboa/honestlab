# Relatório do honestlab: honestlab

## Veredito

**Não encontrou: nenhuma tentativa superou o melhor método conhecido pela margem combinada.**

**Confiança:** Média: 15 tentativas e nenhuma chegou à margem combinada.

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

Perguntamos se, em 15 tentativas, dava para prever quem ganha mais de 50 mil dólares por ano melhor do que o método mais usado hoje (LightGBM, nota 0,928). Não encontramos: a melhor tentativa tirou 0,9296 nos dados de desenvolvimento, abaixo da barra de 0,930. A única ideia que ajudou foi tirar duas colunas de ruído, ganho de cerca de 0,0016, e que ficou abaixo da margem aprovada (0,002). O honestlab recusou abrir a prova final (0 de 3 conferências usadas, nada gasto). Resultado final registrado: não encontrou. A pessoa decidiu não fazer outra rodada agora; se houver uma, deve usar ideias diferentes.

## Os números

- Medida: `auc` (maior é melhor)
- Ponto de partida (o que já existia): 0.9074
- Melhor método conhecido registrado: lightgbm_default = 0.928
- Melhor resultado do agente: 0.9296 (E0008) (+0.2% vs lightgbm_default)
- Margem combinada para contar como achado: 0.002 auc
- Modo: prova (só guardou tentativas cuja melhora é improvável de ser sorte)

## O que foi tentado

15 tentativa(s): 3 guardadas (melhoraram), 12 desfeitas, 0 com erro. Todas ficam registradas.

**Melhores ideias:**
- E0008 (0.9296, keep): Drop fnlwgt and education columns (noise and duplicate) so trees stop splitting on them
- E0015 (0.9294, discard): Path smoothing and 80% column sampling to shrink noisy leaf values
- E0011 (0.9292, discard): On cleaned columns add net capital = gain - loss so one split sees both (earlier test mixed it with other changes)

**Ideias que não funcionaram (exemplos):**
- E0014 (0.9233 vs 0.9296): Monotone constraints (more education, capital gain, hours never lower income odds) as a regulariser
- E0012 (0.9277 vs 0.9296): One-hot categoricals instead of native category splits: native splits can overfit rare levels
- E0006 (0.9264 vs 0.928): linear_tree: leaves fit small linear models on numeric features, smoother in age/hours/education

## Próximo passo

O melhor método conhecido continua sendo o melhor. Opções: trazer dados ou variáveis diferentes, mudar a pergunta, ou ficar com o método atual com mais confiança.

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
Registro: 23 entries, hash chain intact.
