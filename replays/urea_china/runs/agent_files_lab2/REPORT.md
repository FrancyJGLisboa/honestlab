# Relatório do honestlab: ureia_china

## Veredito

**Incomum: na data do evento o número mudou mais do que em quase todas as datas comuns. Isso sozinho não prova que o evento foi a causa.**

**Aprovação:** feita por você na conversa (confirmada pela sua própria mensagem).

## Em palavras simples

Perguntamos se, de outubro a dezembro de 2021, a ureia ficou mais cara do que o gás natural e o preço recente explicam. Ficou: a diferença média foi de 0,571 em escala de log, cerca de 77% acima do preço "normal" (a conversão para porcentagem é minha). Em 137 datas falsas, em que nada de especial ocorreu, só 1 teve diferença igual ou maior, então a chance de isso ser acaso é de cerca de 1,5%. Isso mostra que o salto foi incomum, mas não prova que a inspeção chinesa foi a causa: a crise de energia na Europa, o corte russo de gás e a falta de carvão na China ocorreram nas mesmas semanas. Para separar as causas, seria preciso um dado que só a inspeção atinge, como o preço da ureia em países que não dependem da China.

## Olhada informal: ureia contra potássio e fosfato (SÓ UM INDÍCIO, NÃO É PROVA)

**Aviso.** Esta seção não faz parte do teste aprovado. Foi pedida depois de o resultado da ureia sair, sem contrato próprio, sem dados guardados e sem aprovação. A regra de leitura foi escrita antes de rodar (em `notes/olhada_informal.py`), mas quem a escreveu já conhecia o resultado da ureia. Por isso ela vale como orientação, e não como evidência. Nada aqui muda o veredito do teste.

**O que foi medido.** O mesmo modelo de "preço normal" (que usa o gás), aplicado a cada adubo para outubro a dezembro de 2021, com as mesmas 137 datas falsas.

| Adubo | Acima do normal | Parte das datas falsas com salto igual ou maior |
|---|---|---|
| Ureia | 77% | 0,7% |
| DAP (fosfato) | 12% | 13,1% |
| TSP (fosfato) | 16% | 5,8% |
| Potássio | 1% | 46,7% |

**Como ler.** Abaixo de 5% da coluna da direita, o salto é incomum. Só a ureia passa disso. O potássio ficou normal e os fosfatos subiram pouco.

**O que isso indica (inferência minha, não medida).** O salto foi da ureia, e não de todos os adubos. Isso afasta a explicação de um choque geral que puxou tudo junto.

**O que isso não indica.** Não separa a China do gás. O potássio quase não usa gás, e a ureia usa muito (o gás é a matéria-prima do nitrogênio). Um choque de gás que afetasse só os adubos nitrogenados também deixaria o potássio parado. Os fosfatos subiram pouco apesar de a China também restringi-los, mas são só 3 meses, e isso não decide nada.

**Outros limites.** O potássio é um controle fraco, porque adubos tendem a andar juntos. O modelo de "normal" tem pouco poder de previsão mesmo em meses comuns. Há apenas 3 meses de dados para o evento.

## Olhada informal 2: exportações chinesas de ureia (SÓ UM INDÍCIO, NÃO É PROVA)

**Aviso.** Também fora do teste aprovado, pedida depois do resultado, sem regra escrita antes. Não muda o veredito.

**Fonte.** UN Comtrade, acesso aberto (pré-visualização, um mês por pedido), exportações da China do código 310210 (ureia), em toneladas, jan/2019 a dez/2021. Dados em `notes/china_urea_exports_comtrade.csv`. Conferi dois pontos contra notícias: set/2021 = 1,09 milhão de t e ago/2020 = 201 mil t. Setembro/2019 aparece como 0, o que parece dado ausente, não exportação zero.

**O que foi medido.** Exportações chinesas de ureia em out-dez: 1,71 milhão de t em 2019, 2,52 milhões em 2020 e 1,28 milhão em 2021. Isso é 49% a menos que em 2020 e 25% a menos que em 2019. Em 2021: set 1,09 milhão, out 0,74, nov 0,50, dez 0,035 milhão de t. Em jul e ago de 2021 já eram baixas (0,24 e 0,26 milhão).

**O que isso indica (inferência minha).** A oferta chinesa caiu forte no fim de 2021, sobretudo em dezembro, o que torna plausível um papel da China no preço.

**O que não indica.** Não mostra que a queda causou a alta. Em outubro as exportações ainda estavam altas, e o gás europeu já tinha disparado em setembro. Os dados continuam sem separar China de gás. A queda de jul-ago, anterior à inspeção, mostra também que a China já limitava exportações antes de outubro.

## Os números

- Medida: `score` (menor é melhor)
- Ponto de partida (o que já existia): 0.1128
- Melhor método conhecido registrado: passeio_aleatorio = 0.1114
- Melhor resultado do agente: 0.1128 (baseline) (-1.3% vs passeio_aleatorio)
- Margem combinada para contar como achado: 0.1 score
- Modo: prova (só guardou tentativas cuja melhora é improvável de ser sorte)
- Teste de evento em 2021-10: diferença 0.571; 1 de 137 datas falsas deram uma diferença igual ou maior (chance 0.0145, limite 0.05). PASSOU: a mudança é incomum. Isso não prova a causa: outro fato na mesma janela também pode explicá-la

## O que foi tentado

0 tentativa(s): 0 guardadas (melhoraram), 0 desfeitas, 0 com erro. Todas ficam registradas.

## Próximo passo

Liste os outros fatos da mesma janela e procure um dado que só o evento atinge (outro produto, outra região). Só isso separa as causas.

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
Registro: 5 entries, hash chain intact.
