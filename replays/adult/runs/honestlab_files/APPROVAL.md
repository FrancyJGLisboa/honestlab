# Aprovação

**A pergunta:** Dá para prever a chance de uma pessoa ganhar mais de 50 mil dólares/ano melhor do que os melhores métodos conhecidos, em até 15 tentativas?

**Como vamos medir:** erro de probabilidade (log loss) por pessoa. Menor é melhor.

**De onde vêm os dados:** Adult Income, do repositório UCI (Census 1994), baixado em 10/11/2026. Todas as 32.561 pessoas, sem remover nenhuma.

**Com o que vamos comparar:** regressão logística (jeito simples), e LightGBM e XGBoost (os métodos mais conhecidos). Os números atuais estão em `honestlab reference list`.

**O que conta como sucesso:** erro pelo menos 2% menor que o melhor método conhecido, nos dados de desenvolvimento e também nos dados guardados, com teste estatístico de segurança. Escolhi 2% (e não 5%) porque este conjunto já é muito explorado e o ganho possível é pequeno.

**Dados guardados para a prova final:** 20% das pessoas (6.513), escolhidas ao acaso. Ninguém olha até o final.

**O que fica trancado depois da aprovação:** a pergunta, a medida, os dados e a regra de sucesso.

**O que o agente vai fazer:** até 15 tentativas, sozinho, cada uma registrada.

**Limitações:**
- A divisão é aleatória, não por época; não prova que funciona em dados de outro ano.
- Dados de 1994: resultado vale para este conjunto, não necessariamente para renda hoje.
- Prevê "acima de 50 mil" (sim/não), não o valor exato da renda.

**Para aprovar:** digite `aprovar` no chat.
