# F001: prior work

## How I searched
Duas buscas web (2026-11-08): "ice cream daily sales forecasting temperature regression baseline seasonal naive" e "daily retail sales forecasting rolling linear regression temperature day-of-week holiday dummy variables". Só vi títulos e resumos; não li os artigos inteiros.

## Closest existing work
- Artigo da AIUB, regressão linear e XGBoost de vendas de sorvete contra temperatura: https://dspace.aiub.edu/jspui/handle/123456789/2663. Usa temperatura, mas não compara com sazonal ingênuo nem com variáveis de calendário.
- Estudos de vendas do varejo (Walmart, semanais) e "Forecasting: theory and practice" (https://arxiv.org/pdf/2012.03854): regressão com indicadoras de dia da semana e feriado é um método padrão; um estudo de rede de supermercados canadense indica que acrescentar clima a um modelo de dia da semana melhora a previsão.

## Assessment
Método já conhecido: regressão linear com temperatura, feriado e dia da semana é prática padrão, não uma novidade. A contribuição é só a medição nos dados desta sorveteria: o erro ficou menor que o da reta de temperatura. Não verifiquei janelas rolantes específicas nem a literatura de sorvete a fundo.
