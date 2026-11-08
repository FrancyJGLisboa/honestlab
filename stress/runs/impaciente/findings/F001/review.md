# Revisão independente: F001

Li apenas SPEC.md, eval/evaluate.py, claim.md e change.patch. Não toquei nos dados guardados para a prova final nem rodei o avaliador. Tentei refutar a afirmação e o resultado está abaixo.

## O que não consegui refutar

- **Avaliador:** é walk-forward limpo. O histórico só tem dias estritamente anteriores. O `today` não tem `vendas`, e o valor real entra no histórico só depois da previsão. Os modelos recebem cópias dos dicts. A faixa de saída é validada. Não achei truque.
- **Vazamento do futuro:** o modelo só usa `history[-120:]` e as características do próprio dia (temperatura, feriado, dia da semana). Não lê arquivos, não lê a prova final e não usa a venda do dia. Na prova final, os dias de dev entram como histórico, o que é legítimo.
- **Sobreajuste:** foi 1 experimento antes do candidato, com um único hiperparâmetro (janela de 120 dias) e um modelo simples de 9 parâmetros. O risco de seleção é pequeno. A prova final é um período posterior, com 183 dias, e confirma: 17,95% de melhora, com IC de 98,3% [1,79; 5,21].
- **Margem:** o limite inferior do IC já é cerca de 9% da referência na prova final (1,79 / 19,57) e cerca de 9,4% no dev. Isso fica acima do limiar de 5%, não só o ponto central.
- **Referências:** a mais forte (`so_temperatura`) foi comparada nos dois conjuntos pela mesma regra pré-registrada.

## Ressalvas (afirmam menos, mas precisam estar escritas)

1. **Temperatura e feriado são valores medidos do próprio dia, não previsões.** O SPEC diz "do próprio dia", mas nenhum lugar diz com todas as letras que são observações reais. O claim.md também não diz. Na vida real, a pessoa teria só a previsão do tempo, que erra. Por isso 15,1 e 16,06 unidades de erro são um limite otimista ("com o tempo conhecido"), não o erro que ela terá ao planejar a compra. Isso precisa constar no relatório.
2. **A comparação não isola o efeito do tempo.** O candidato soma dia da semana e feriado à reta de temperatura. A referência `so_temperatura` não tem nenhum dos dois. Parte do ganho pode vir da sazonalidade semanal e do feriado, não do clima. Falta uma referência com regressão em dia da semana e feriado sem temperatura, e o claim.md não pode atribuir o ganho à temperatura. A pergunta do SPEC ("tempo reduz o erro") só fica respondida no sentido amplo de "este conjunto de informações do dia".
3. **Chuva não é usada**, apesar de estar na pergunta. A afirmação não deve dizer que "tempo e chuva" ajudam.
4. **Pequenas inconsistências:** o claim.md fala em 487 unidades no dev e o SPEC em 486 avaliados. Deve ser só diferença de contagem, mas convém conferir. A janela e os parâmetros de `so_temperatura` não foram vistos por mim. Se ela usa todo o histórico e o candidato usa 120 dias, parte do ganho é adaptação à tendência, não regressão em si.
5. **Alcance:** vale para uma sorveteria, 2 anos de dados, e uma prova final de um único semestre.

## Conclusão

Não há vazamento, truque ou sobreajuste relevante, e a evidência estatística sustenta a afirmação restrita ao que foi medido: esse modelo, com temperatura e feriado reais do dia, erra pelo menos 5% menos que a melhor referência registrada. Ela não sustenta "o tempo é o que melhora" nem "isso vale com previsão do tempo". Aceito, desde que o relatório inclua as ressalvas 1 a 3.

Verdict: ACCEPT
