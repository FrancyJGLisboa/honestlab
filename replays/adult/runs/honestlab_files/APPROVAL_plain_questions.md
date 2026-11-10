# Página de aprovação: honestlab

**A pergunta:** em 15 tentativas, dá para prever "ganha mais de 50 mil dólares por ano?" melhor do que o método mais usado hoje para tabelas como esta?

**Como vamos medir:** uma nota de 0,5 (chute) a 1 (perfeito) para a capacidade de separar quem ganha mais de quem ganha menos. Quanto MAIOR, melhor.

**De onde vêm os dados:** da base pública "Adult Income" (UCI), já guardada no projeto. 30.162 pessoas, divididas como o projeto já fazia.

**Com o que vamos comparar:** o método mais usado hoje para tabelas (LightGBM, árvores que aprendem com os erros umas das outras) tira 0,928 nos dados de desenvolvimento; uma variante comum (XGBoost) tira 0,926; o ponto de partida simples (regressão logística) tira 0,907. A barra a bater é a mais alta: 0,928.

**O que conta como sucesso:** nota pelo menos 0,002 acima do melhor método conhecido, tanto nos dados de desenvolvimento quanto nos dados guardados, com um teste de que a diferença não é sorte.

**Dados guardados para a prova final:** 6.033 pessoas (20%). Ninguém olha até a prova final; só 3 conferências são permitidas.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho, cada uma registrada, mudando só `src/model.py`.

**Modo:** provar. Só guardo uma mudança se houver evidência de que não é sorte; "encontrei" exige prova nos dados guardados.

**Limitações:** (1) 0,002 é um ganho pequeno e o teto da base é baixo: é provável que a resposta seja "não encontrou". (2) Os números de outros trabalhos citados na SPEC são de memória, não de busca; valem só as medidas feitas aqui. (3) Uma única base, de 1994.

**Para aprovar:** no Claude Code, digite `aprovar` na conversa. Em outro agente, abra um terminal nesta pasta e rode o comando de congelar (`honestlab` + `freeze`), depois `sim`.
