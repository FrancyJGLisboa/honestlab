# F001: prior work

## How I searched
Duas buscas na web em 2026-11-08 (modo padrão): (1) "daily retail sales forecasting weather temperature day-of-week baseline seasonal naive vs regression ice cream demand"; (2) "weather-driven daily sales forecasting ridge regression temperature day-of-week ice cream demand MAE improvement over moving average". Não consultei bases acadêmicas (Scopus, Google Scholar) nem os textos completos dos artigos; só os resultados da busca.

## Closest existing work
- [Best Practices in Weather-based Sales Forecasting (scm.dk)](https://www.scm.dk/best-practices-weather-based-sales-forecasting): ajuste de clima sobre uma base que já capta dia da semana e sazonalidade; a sensibilidade ao clima varia por estação e por dia da semana. Mesma ideia geral, é guia de prática e não traz MAE comparável.
- [Bushra, "Weathering the Forecast" (IEOM 2024)](https://dspace.aiub.edu/jspui/bitstream/123456789/2663/1/Weathering%20the%20Forecast.pdf): regressão linear vs XGBoost para vendas de sorvete e temperatura; a linear é estável. Mesma família de método, outro dado e outra métrica.
- [Forecasting Seasonal Products: A Case of Ice-Cream Sales (Emerald)](https://Www.Emeraldinsight.com/insight/content/doi/10.1108/S1477-407020210000014003/full/html): previsão de vendas de sorvete sazonais; não li o texto completo.
- Projeto de GitHub de regressão linear multivariada de sorvete com dia da semana, mês e clima, que sugere ridge apenas como proposta (resultado de busca, não testado).

## Assessment
Método semelhante já é conhecido: regressão linear/ridge com temperatura, chuva e dia da semana para vendas de sorvete é prática comum e não é uma novidade. Não achei estudo com a mesma comparação (ridge com clima vs média móvel, em MAE); "não achei" não prova novidade e eu não verifiquei bases acadêmicas pagas. O valor do resultado é prático (esta sorveteria, estes dados), não científico. Não consegui checar o quanto o ganho sobrevive a uma previsão do tempo com erro (ver review.md).
