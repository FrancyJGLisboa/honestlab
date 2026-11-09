# Journal

One to three lines per experiment: id, result, what was learned.
- E0001 Adam (lr 0.003): 2.697, pior que 2.660. Otimizador não é o gargalo; provavelmente capacidade/contexto.
- E0002 contexto 8: 2.621 (mantido). Mais passado ajuda.
- E0003 oculta 256: 2.575 (mantido). Capacidade ajuda.
- E0004 LR 0.3 com decaimento linear: 2.464 (mantido, maior ganho). Estava subtreinado.
- E0005 LR 0.6: 2.453 (mantido, ganho pequeno; passo está perto do ideal).
- E0006 lote 512: 2.505 (desfeito). Mais passos importam mais que lotes grandes.
- E0007 lote 64: 2.500 (desfeito). 128 é o ponto bom.
- E0008 embed 32: 2.448, não significativo (desfeito). 3 desfeitos seguidos -> mudar estrutura.
- E0009 ligação direta: 2.466 (desfeito). Passos ficam mais caros e não compensam.
- E0010 contexto 12: 2.551 (desfeito). Contexto longo demais atrapalha em 60 s.
- PROGRESSO após 10: melhor 2.453 (E0005). Funcionou: contexto 8, oculta 256, passo 0.6 decaindo. Meta 2.328 ainda longe.
- E0011 contexto 6: 2.404 (mantido). Em 60 s, contexto menor treina melhor.
- E0012 contexto 5: 2.384 (mantido). Quase empata com o n-grama (2.378).
- E0013 contexto 4: 2.382, não significativo (desfeito). Ponto ideal 4-5.
- E0014 oculta 384: 2.380, não significativo (desfeito). FIM dos 40 min: melhor 2.384 (E0012), empata com n-grama, não atinge margem.
