# Relatório de Validação Estatística: Fase 3

- **Data da Execução**: 2026-10-29 15:43:49 UTC
- **Protocolo de Pré-registro**: `docs/hipoteses.md` (Commit `e3ae334`)
- **Dataset de Validação**: `data/events_v2.csv` (N = 61 eventos históricos objetivos com precisão diária)
- **Modelos Nulos**: N1 (Uniforme), N2 (Estratificado por Década), N3 (Deslocamento Circular $N = 10.000$)
- **Controle de Múltiplos Testes**: Benjamini-Hochberg FDR ($q = 0.05$)

---

## 1. Tabela Geral de Resultados de Hipóteses

| Hipótese Testada | N | Score Obs. | Nulo (Média ± DP) | Efeito ($z$) | $p$-valor | $q$ (FDR) | Significante ($q < 0.05$)? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| H1 Geral vs N3: Deslocamento Circular (Principal) | 59 | 481.1 | 500.6 ± 38.5 | -0.506 | 0.6941 | 0.9772 | ❌ Não |
| H1 Geral vs N2: Estratificado por Década | 61 | 477.6 | 493.7 ± 35.9 | -0.450 | 0.6715 | 0.9772 | ❌ Não |
| H1 Geral vs N1: Uniforme Aleatório | 61 | 477.6 | 499.9 ± 37.0 | -0.602 | 0.7250 | 0.9772 | ❌ Não |
| H1 Classe: armed_conflict vs N3 | 9 | 353.0 | 500.7 ± 95.9 | -1.541 | 0.9336 | 0.9772 | ❌ Não |
| H1 Classe: coup_d_etat vs N3 | 12 | 538.4 | 501.6 ± 84.9 | +0.434 | 0.3327 | 0.9772 | ❌ Não |
| H1 Classe: economic_recession vs N3 | 10 | 547.6 | 501.9 ± 93.8 | +0.487 | 0.3112 | 0.9772 | ❌ Não |
| H1 Classe: pandemic vs N3 | 5 | 349.0 | 500.0 ± 129.3 | -1.167 | 0.8700 | 0.9772 | ❌ Não |
| H1 Classe: regime_change vs N3 | 10 | 570.5 | 500.2 ± 95.2 | +0.738 | 0.2299 | 0.9772 | ❌ Não |
| H1 Classe: war_interstate vs N3 | 15 | 462.1 | 499.4 ± 73.3 | -0.509 | 0.6918 | 0.9772 | ❌ Não |
| H2 Treino Temporal (1800-1950) | 28 | 512.4 | 499.4 ± 56.8 | +0.229 | 0.4083 | 0.9772 | ❌ Não |
| H2 Teste Fora da Amostra (1951-2025) | 33 | 456.5 | 501.6 ± 53.0 | -0.851 | 0.7996 | 0.9772 | ❌ Não |
| H3 Orbe Estrito 1.0° vs N3 | 61 | 92.3 | 90.1 ± 7.0 | +0.320 | 0.3485 | 0.9772 | ❌ Não |
| H3 Orbe Estrito 2.0° vs N3 | 61 | 118.7 | 120.0 ± 9.7 | -0.133 | 0.5377 | 0.9772 | ❌ Não |
| Controle Negativo (Ruído Puro Sintético) | 61 | 427.8 | 501.5 ± 37.2 | -1.982 | 0.9772 | 0.9772 | ❌ Não |

---

## 2. Análise Detalhada dos Resultados

### 2.1 Hipótese 1: Teste contra o Modelo Nulo de Deslocamento Circular (N3)
- **Score Médio Observado**: **481.13** (escala percentil empírica 0–1000).
- **Média da Distribuição Nula sob Deslocamento Circular**: **500.62 ± 38.48**.
- **Tamanho de Efeito ($z$-score)**: **-0.506**.
- **$p$-valor Empírico**: **0.69413**.
- **Interpretação**:
  O modelo nulo N3 desloca todo o conjunto de eventos por offsets temporais aleatórios circulares, preservando a aglomeração temporal e os lentos ciclos de planetas externos. O teste demonstra de forma conclusiva se os eventos históricos ocorrem em momentos geometricamente mais tensos do que datas deslocadas.

### 2.2 Hipótese 2: Generalização Fora da Amostra (Walk-Forward 1951–2025)
- **Efeito no Período Intocado**: $z = -0.851$, $p = 0.7996$.
- Avaliação da consistência inter-épocas: qualquer sinal aparente calibrado no passado que desaparece fora da amostra no pós-guerra representa sobreajuste histórico.

### 2.3 Controle Negativo
- O controle negativo processou datas sintéticas de ruído puro pelo mesmo arcabouço computacional, resultando em ausência de significância, comprovando a robustez matemática do motor de teste.

---

## 3. Conclusão e Decisão do Marco M2

**Decisão**: **CAMINHO A (Pivô Metodológico)**

Conforme os critérios estritos de pré-registro em `docs/hipoteses.md`:
Os resultados foram computados com sementes fixas e são 100% reprodutíveis via comando `python src/analysis/run_phase3_validation.py`.
