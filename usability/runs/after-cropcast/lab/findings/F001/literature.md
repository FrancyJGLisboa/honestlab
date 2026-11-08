# F001: prior work

## How I searched
Duas buscas padrão na web em 2026-11 (sem acesso a bases pagas): (1) "county crop yield forecasting standard methods trend regression weather detrended ridge benchmark rolling origin"; (2) "crop yield trend estimation shrinkage empirical Bayes county slope pooled weather adjusted quadratic rainfall".

## Closest existing work
- Detrending de produtividade com regressão linear, quadrática e local, e tendência ajustada por clima (estilo USDA Westcott-Jewison): https://agris.fao.org/search/en/records/65de2acb63b8185d9ca74eb2 , https://ageconsearch.umn.edu/record/122541/files/Conradt.pdf . O método aqui é uma tendência linear com efeito de clima removido antes do ajuste, então é da mesma família.
- Encolhimento (shrinkage) e Bayes hierárquico/empírico para produtividade por município: Awondo et al. (2018) https://econpapers.repec.org/RePEc:taf:uaajxx:v:22:y:2018:i:2:p:289-308 ; Park et al. https://ageconsearch.umn.edu/record/313319/files/JARE47_3_10_Park.pdf ; Bellow (NASS) https://data.nass.usda.gov/Education_and_Outreach/Reports,_Presentations_and_Conferences/reports/conferences/JSM-2011/JSM-2011-Bellow.pdf . Puxar a inclinação de cada município para a média geral é a ideia central desses métodos (aqui feita por ridge simples, com constantes fixas).

## Assessment
Existem trabalhos parecidos: cada ingrediente (tendência linear, ajuste por clima com chuva côncava, encolhimento da inclinação) é conhecido. Não achei esta combinação exata com estes números, mas "não achei" não prova novidade, e não li os artigos completos. A contribuição aqui é prática: mostrar que essa combinação supera as referências padrão neste projeto, não um método novo.
