# F001: prior work

## How I searched
Uma busca na web (2026-11-08): "ice cream sales forecasting temperature regression daily demand weather". Só olhei os resultados da busca, não li os artigos inteiros.

## Closest existing work
- IEOM Society (2024), comparação de regressão linear e XGBoost para vendas de sorvete em função da temperatura: https://index.ieomsociety.org/index.cfm/item/55298 . Usa o mesmo tipo de método; não testei em dados deste negócio nem contra médias simples.
- Livro-texto "Hands-On Machine Learning with Microsoft Excel 2019": regressão linear da produção diária de sorvete contra a temperatura média (R² 0,78): https://m.appbook.qq.com/read/1036698668/26 . Mesma ideia básica.
- Tutoriais e exercícios de sala de aula com a mesma relação temperatura x vendas (ex.: https://rstudio-pubs-static.s3.amazonaws.com/1357580_9d4dcac71cf5439fa4697869ef0eea9a.html ).

## Assessment
Identical method already known: prever vendas de sorvete por regressão sobre a temperatura é uma técnica clássica e bem documentada. A contribuição aqui não é um método novo, é a medida concreta, nos dados desta sorveteria, de quanto ela ganha das médias simples (cerca de 55% menos erro nos dados guardados). Não verifiquei métodos mais fortes (ex.: modelos de árvore) nem ajuste fino dos parâmetros.
