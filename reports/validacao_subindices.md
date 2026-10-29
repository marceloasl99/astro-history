# Relatório de Validação dos Sub-índices (Experimento E4)

> **Auditoria Metodológica**: Os sub-índices (Risco Bélico, Crise Econômica e Transformação Social) discriminam suas classes históricas melhor que o acaso?

---

## 1. Tabela de Validação de Poder Discriminativo (AUC-ROC)

| Sub-índice | Classe Alvo | N (Alvo vs Outros) | Média Alvo | Média Outros | AUC-ROC | p-valor (Mann-Whitney) | p-valor (Permutação) | Discrimina? |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Risco Bélico** | Guerras e Conflitos Armados | 24 vs 37 | 96.1 | 110.4 | **0.457** | 0.5707 | 0.5744 | ❌ **Não** (Pior que acaso) |
| **Risco de Crise** | Recessões Econômicas | 10 vs 51 | 317.1 | 368.3 | **0.408** | 0.365 | 0.3796 | ❌ **Não** |
| **Transformação Social** | Golpes de Estado e Mudanças de Regime | 22 vs 39 | 296.5 | 279.7 | **0.499** | 0.994 | 0.9923 | ❌ **Não** |

---

## 2. Diagnóstico de Saturação Artificial

- **Piso de 10,0 no Risco Bélico**: Presente em 36.1% dos eventos.
- **Teto de 1000,0 no Risco de Crise**: Decorrente do divisor arbitrário fixado em 520 pontos.

---

## 3. Decisão de Projeto Conforme o Pré-registro

Conforme estipulado na **Etapa 3** do plano:
> *"Se não discriminar, **remover da interface** em vez de manter com nome sugestivo."*

Como todos os três sub-índices apresentaram AUC estatisticamente indistinguível de $0,50$ (ou inferior a $0,50$), os vetores de **"Risco Bélico"**, **"Risco de Crise"** e **"Inovação Tech"** foram formalmente **descontinuados e removidos da interface de `/projections`**, eliminando falsas atribuições causais e preservando estritamente a literacia de dados.
