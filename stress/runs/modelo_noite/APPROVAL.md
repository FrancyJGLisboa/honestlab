# Página de aprovação: modelo_noite

**A pergunta:** uma pequena rede neural, treinada por 60 segundos neste computador, consegue adivinhar a próxima letra de *Dom Casmurro* melhor do que o método clássico de contar sequências de letras?

**Como vamos medir:** quantos bits por letra o modelo precisa, em capítulos que ele nunca viu. Menor é melhor. Um arquivo de texto comum usa 8.

**Com o que vamos comparar:** o ponto de partida (uma rede minúscula, cerca de 2,65) e o método clássico de contagem com suavização Witten-Bell (cerca de 2,38), já registrado.

**O que conta como sucesso:** precisar de pelo menos 0,05 bit a menos por letra que o método clássico, nos capítulos de desenvolvimento e nos capítulos guardados, com uma checagem estatística.

**Dados guardados para a prova final:** os capítulos 127 a 148, que ninguém olha até o fim.

**O que fica trancado depois da aprovação:** a pergunta, a medida, o tempo de treino de 60 segundos, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho, cerca de uma hora. Cada tentativa é treinada 3 vezes por 60 segundos, porque o treino muda um pouco de uma vez para outra. Se você pedir, ele roda a noite toda.

**Limitações:** é um exemplo de aprendizado com um livro só. O resultado vale para este computador e este tempo de treino.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta, digite `honestlab freeze` e depois `sim`.
