# Página de aprovação: after-vendas

**A pergunta:** usar o tempo do dia (temperatura e chuva) prevê as vendas da sorveteria melhor do que a média que você usa hoje?

**Como vamos medir:** erro médio por dia, em unidades vendidas. Faltar sorvete conta o dobro de sobrar. Menor é melhor.

**Com o que vamos comparar** (erro médio por dia nos dados de desenvolvimento):
- Sua média das últimas 4 vezes do mesmo dia da semana: **41,1**
- Média geral dos últimos 28 dias: 39,1
- Mediana das últimas 8 vezes do mesmo dia da semana, sem tempo: 41,8
- Dia da semana + uma reta simples com a temperatura: **28,4** (o melhor método conhecido)

Ou seja, só a temperatura já erra cerca de 31% menos que a sua média. Por isso a barra do sucesso fica mais alta (veja abaixo).

**O que conta como sucesso:** errar pelo menos 10% menos que o melhor método conhecido (a reta com temperatura), não só que a sua média. Na prática, ficar em cerca de 25,5 ou menos. Tem que valer nos dados de desenvolvimento e de novo nos dados guardados, com uma verificação estatística de que não foi sorte.

**Dados guardados para a prova final:** de julho a dezembro de 2025. Ninguém olha esses dias até o fim.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas sozinho, cada uma registrada.

**Limitações:**
- O tempo nos seus dados parece ser o que realmente aconteceu, não a previsão da véspera. Na vida real você só teria a previsão, que erra um pouco. Os resultados ficam otimistas.
- Faltar sorvete pesa o dobro por escolha minha. Se o seu custo real for outro, o resultado muda um pouco.
- São 2 anos de dados, e a prova final cobre só um semestre.

**Para aprovar:** abra um terminal nesta pasta, digite `labloop freeze` e depois `sim`.
