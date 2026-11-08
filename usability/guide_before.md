Guia rápido (labloop 0.3.2):
1. Instale: `pipx install ./labloop-kit` (já instalado no seu computador).
2. Para uma ideia sua: `labloop init minha-ideia`, abra o agente e peça: "Use the labloop-frame skill. My idea: ...". Revise o `SPEC.md` e o `eval/` e rode `labloop freeze` você mesmo.
3. Depois peça ao agente: "Use the labloop-experiment skill for 10 experiments."
4. Num repositório que você já tem: `labloop init --here` na raiz, depois peça "Use the labloop-scout skill." e escolha uma proposta de `lab/notes/PROPOSALS.md`.
5. Acompanhe com `labloop status` e `labloop history`. Nada vira "descoberta" sem passar pelo holdout, pela busca de literatura e por uma revisão independente ("Use the labloop-finding skill.").
