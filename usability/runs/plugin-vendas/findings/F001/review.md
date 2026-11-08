# Revisão independente de F001

Li somente SPEC.md, eval/evaluate.py, claim.md e change.patch. Não li nada em data/ e não rodei o avaliador. Tudo abaixo vem da leitura do código e dos números do claim, não de medições minhas.

## O que tentei refutar

**1. Vazamento do futuro.**
- O avaliador monta `hist = rows[:i]`. São só os dias anteriores, e a coluna `avaliar` é removida.
- `today` tem só data, dia da semana, feriado, temperatura e chuva. Não tem `vendas`.
- O `hist` é uma lista nova de dicts novos. O código de previsão não recebe referência a linhas futuras.
- O candidato usa `history[-120:]` e `today`. Treina só com vendas passadas e prevê com as características do dia. Não achei vazamento no patch.
- No holdout só há 28 dias de histórico antes do primeiro dia avaliado, então no começo a janela fica menor que 120 (mínimo de 14). Isso piora a previsão do candidato e não o favorece.

**2. Truques no avaliador.**
- A lista proibida (`FORBIDDEN`) é frágil. Ela casa palavras inteiras, então `__globals__`, `f_back`, `gi_frame` e `vars` passam. Em tese um código mal-intencionado poderia subir pela pilha até as variáveis do avaliador (`rows`, que tem as vendas futuras).
- O patch não usa nada disso. Ele só faz aritmética em listas, sem importações, sem arquivos e sem introspecção. Isso é uma fraqueza do avaliador, não do candidato.
- Eu não vi os outros arquivos de `src/`. O patch mexe só em `predict.py`, e `check_source` olha todos os `.py` de `src`. Recomendo conferir que não há outros arquivos.
- A validação de saída (finito, entre 0 e 2000) e o conjunto fixo de dias avaliados impedem escolher só os dias fáceis. O corte dev/holdout é por tempo.

**3. Sobreajuste.**
- O modelo tem 5 coeficientes, ridge fraco (1.0) e janela de 120 dias. A janela e o ridge são fixos no código, e só 2 experimentos vieram antes. A seleção é leve.
- Dev (11.77) e holdout (13.63) têm erros parecidos. O holdout é posterior e inédito, e o claim usa alpha corrigido (0,05/3).
- Não vejo sinal de sobreajuste. O holdout fica um pouco pior que o dev, como se espera.

**4. Comparação com as referências.**
- A referência forte usada é `media28`, que é melhor que o método do dono (28.25 dev, 31.21 holdout). A comparação é mais dura que a pergunta original, e a regra foi fixada antes.
- As contas do claim batem: 15.03/26.796 = 56,1%; 16.85/30.4731 = 55,3%; 30.4731 − 13.6261 = 16.85.
- Ressalva de justiça: nenhuma referência usa tempo ou feriado. A comparação mostra que usar essas variáveis ajuda muito, que era a pergunta. Mas não separa quanto vem do tempo e quanto só do fim de semana ou do nível recente. Faltou uma referência como "média por dia da semana + feriado". Isso não muda o veredito, porque a pergunta é justamente se usar o tempo e o calendário ganha do método atual.
- A mediana tem erro de dev de 71.28 contra 31.03 no holdout. É um valor estranho, mas não afeta o candidato, porque a referência mais forte é outra.

**5. Estatística.**
- O bootstrap pareado trata os dias como independentes, mas dias vizinhos têm erros correlacionados, então o intervalo é um pouco otimista.
- O efeito é tão grande que isso não importa. O limite inferior do holdout é 12.36 contra 30.47, ou cerca de 40% de redução, bem acima dos 10%.

## Afirmações maiores que os números

- **O tempo usado é o real observado do dia, não a previsão.** O claim não diz isso. Em uso de verdade, o dono teria uma previsão de tempo, com erro. Os 55% são um teto, não o ganho esperado em produção. O claim deveria dizer "com o tempo real do dia". O ganho com previsão do tempo não foi medido aqui.
- Um corte de 55% do erro é muito maior que o típico em demanda diária. Pode ser um negócio fortemente ligado ao calor, e os dados podem ser sintéticos ou muito limpos. O holdout confirma isso para esta série, mas só vale para esta sorveteria e para este período (jul–dez/2025, uma única estação).
- "Pelo menos 10%" está bem apoiado como limite inferior para o tempo real. O texto não deveria sugerir que o ganho vale na operação sem essa ressalva.

## Conclusão

Não achei vazamento, truque nem sobreajuste relevante. O ganho passa com folga no holdout inédito e a conta é consistente. A única ressalva material é que o resultado depende do tempo observado, e o texto do claim deve dizer isso. A fraqueza do filtro do avaliador (introspecção de pilha) vale corrigir em rodadas futuras, mas este candidato não a usa.

Aceito, desde que o claim seja citado como "com o tempo real do dia; não testado com previsão do tempo".

Verdict: ACCEPT
