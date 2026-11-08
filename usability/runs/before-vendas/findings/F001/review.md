# F001: independent review

Escrito por um subagente que não rodou os experimentos. Entradas: SPEC.md, eval/evaluate.py, claim.md, change.patch (sem journal nem histórico). Não abriu o holdout.

## Evaluator exploits
Nenhum exploit encontrado. O avaliador entrega só o histórico anterior, em cópia profunda e sem a coluna `teste`; o alvo traz só calendário e tempo, sem `vendas`. O `src/predict.py` não referencia arquivos nem guarda estado entre chamadas. A varredura de texto é heurística, mas o código do candidato é limpo. O revisor reproduziu o MAE de dev (12,217).

## Leakage or overfitting
Sem vazamento de rótulos: janela de 90 dias anterior ao dia alvo, ridge com 10 coeficientes e LAMBDA=1. Foi tentado um único experimento antes do candidato, então a seleção sobre o dev é mínima. O holdout (13,94) confirma o dev (12,22). O revisor não abriu o holdout e confiou nos números do claim.md.

## Fairness of the comparison
Contra a referência certa do SPEC (dev: média de 7 dias, 26,99; holdout: média de 28 dias, 30,47), com margem muito acima de 2,0 e correção de alfa. Porém as referências não usam o tempo, e o modelo recebe temperatura e chuva reais do dia alvo, como previsão perfeita. O revisor mediu no dev, injetando ruído gaussiano no tempo do dia alvo (desvios arbitrários, não calibrados com erro real de previsão):

| Ruído (temp, chuva) | MAE do modelo no dev |
|---|---|
| (0, 0) | 12,2 |
| (2 °C, 2 mm) | 19,0 |
| (3 °C, 5 mm) | 25,7 |
| (5 °C, 10 mm) | 40,3 |

Com erro de 3 °C e 5 mm o ganho sobre a média de 7 dias (26,99) praticamente some. O ganho de mais de 50% é um teto otimista. Também não há baseline simples que use o tempo (por exemplo, média por dia da semana mais ajuste de temperatura), então não dá para separar o ganho de "usar o tempo" do ganho do ridge.

## Does the claim say more than the numbers?
O claim literal é estreito e verdadeiro, mas omite que o tempo é o observado, não uma previsão (a pergunta do SPEC fala em "tempo previsto"). Não sustenta generalização a outras lojas: uma sorveteria, dois anos, e o holdout cobre só jul–dez 2025, sem um verão novo. O claim cita a média de 7 dias, enquanto o holdout compara com a de 28 dias (inconsistência inofensiva).

## Strongest objection
O ganho vem de comparar um modelo com o tempo perfeito do dia alvo contra médias sem tempo nenhum. Com ruído plausível de previsão, a vantagem encolhe muito e pode desaparecer. Falta uma avaliação com tempo previsto ruidoso e uma baseline que também use o tempo.

Condição de aceite: o texto do finding deve dizer que o tempo é o observado e que a ordem de grandeza do ganho não vale para uso real.

Verdict: ACCEPT
