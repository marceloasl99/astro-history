# Relatório de Validação Estatística v2 (Fase 3 & Marco M2)

- **Data da Execução**: 2026-10-29 20:11:35 UTC
- **Dataset Analítico**: `data/events_v2.csv` ($N = 59$ eventos históricos objetivos com precisão diária, 1800–2025)
- **Modelos Nulos**: N1 (Uniforme), N2 (Estratificado por Década), N3 (Deslocamento Circular $N = 10.000$)
- **Controle de Múltiplos Testes**: Benjamini-Hochberg FDR ($q = 0.05$) sobre hipóteses científicas

---

## 1. Tabela Geral de Resultados de Hipóteses (v2)

| Hipótese Testada | N | Score Obs. | Nulo (Média ± DP) | Efeito ($z$) | $p$-valor (1-caudal) | $p$-valor (2-caudais) | $q$ (FDR) | Significante ($q < 0.05$)? |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| H1 Geral vs N3: Deslocamento Circular (Principal) | 59 | 481.1 | 500.6 ± 38.5 | -0.506 | 0.6941 | 0.6117 | 0.8834 | ❌ Não |
| H1 Geral vs N2: Estratificado por Década | 59 | 481.1 | 493.9 ± 36.6 | -0.350 | 0.6418 | 0.7163 | 0.8834 | ❌ Não |
| H1 Geral vs N1: Uniforme Aleatório | 59 | 481.1 | 499.7 ± 37.7 | -0.493 | 0.6850 | 0.6299 | 0.8834 | ❌ Não |
| H1 Classe: armed_conflict vs N3 | 9 | 353.0 | 500.7 ± 95.9 | -1.541 | 0.9336 | 0.1328 | 0.9336 | ❌ Não |
| H1 Classe: coup_d_etat vs N3 | 11 | 538.4 | 501.6 ± 84.9 | +0.434 | 0.3327 | 0.6653 | 0.8834 | ❌ Não |
| H1 Classe: economic_recession vs N3 | 10 | 547.6 | 501.9 ± 93.8 | +0.487 | 0.3112 | 0.6223 | 0.8834 | ❌ Não |
| H1 Classe: pandemic vs N3 | 5 | 349.0 | 500.0 ± 129.3 | -1.167 | 0.8700 | 0.2600 | 0.9336 | ❌ Não |
| H1 Classe: regime_change vs N3 | 9 | 570.5 | 500.2 ± 95.2 | +0.738 | 0.2299 | 0.4598 | 0.8834 | ❌ Não |
| H1 Classe: war_interstate vs N3 | 15 | 462.1 | 499.4 ± 73.3 | -0.509 | 0.6918 | 0.6163 | 0.8834 | ❌ Não |
| H2 Treino Temporal (1800-1950) | 26 | 512.4 | 499.4 ± 56.8 | +0.229 | 0.4083 | 0.8165 | 0.8834 | ❌ Não |
| H2 Teste Fora da Amostra (1951-2025) | 33 | 456.5 | 501.6 ± 53.0 | -0.851 | 0.7996 | 0.4008 | 0.9329 | ❌ Não |
| H3 Orbe Estrito 1.0° vs N3 | 59 | 92.3 | 90.1 ± 7.0 | +0.320 | 0.3485 | 0.6971 | 0.8834 | ❌ Não |
| H3 Orbe Estrito 2.0° vs N3 | 59 | 118.7 | 120.0 ± 9.7 | -0.133 | 0.5377 | 0.9246 | 0.8834 | ❌ Não |
| H4 Tese de Tarnas (Aspectos Duros Saturno/Urano/Netuno/Plutão) | 59 | 33.4 | 34.0 ± 8.7 | -0.063 | 0.5103 | 0.9794 | 0.8834 | ❌ Não |

---

## 2. Teste de Equivalência (TOST - Two One-Sided Tests)

- **Margem de Equivalência ($\Delta$)**: $0,3$ Desvio-Padrão (86.4 pontos).
- **Estatística $t_1$ ($H_{01}: \text{Efeito} \le -\Delta$)**: $t = +1.739$, $p = 0.04103$
- **Estatística $t_2$ ($H_{02}: \text{Efeito} \ge +\Delta$)**: $t = +2.752$, $p = 0.00296$
- **$p$-valor Combinado TOST**: **0.04103** ($p < 0,05$).
- **Conclusão Metodológica**: Rejeita-se a hipótese de que haja qualquer efeito astronômico de magnitude relevante ($\ge 0,3$ DP). O efeito observado é **estatisticamente equivalente a zero**, estabelecendo prova de ausência de efeito prático, e não apenas ausência de evidência.

---

## 3. Análise de Poder Estatístico e Efeito Mínimo Detectável (E7)

- **Erro-Padrão do Nulo (N3)**: 38.48 pontos.
- **Efeito Mínimo Detectável para 80% de Poder ($\alpha = 0,05$)**: **95.7 pontos** (0.332 DP de eventos individuais).
- **Curva de Poder Teórica (Taxa de Rejeição por Tamanho de Efeito $\delta$)**:
  - $\delta = 0.1$ DP: 18.5%
  - $\delta = 0.2$ DP: 44.3%
  - $\delta = 0.3$ DP: 72.8%
  - $\delta = 0.5$ DP: 98.2%
  - $\delta = 0.8$ DP: 100.0%

---

## 4. Calibração de Falsos Positivos em 1.000 Controles Negativos (E6)

- **Total de Catálogos Sintéticos**: 1000 execuções independentes pareadas por década.
- **Taxa de Rejeição Empírica ($\alpha = 0,05$)**: **3.7%** (37/1000).
- **Aderência ao Alvo (3% a 7%)**: **Calibrado com sucesso**.
- **Higiene Metodológica**: Os controles negativos sintéticos atuam como termômetro de calibração do modelo nulo e foram **excluídos da família de hipóteses do FDR**, evitando diluição artificial de $q$-valores.

---

## 5. Teste da Tese de Tarnas (Planetas Lentos)

- **Score Restrito**: Conjunções, quadraturas e oposições entre Saturno, Urano, Netuno e Plutão (orbe $\le 3,0^\circ$).
- **Resultado sob Deslocamento Circular (N3)**: $z = -0.063$, $p = 0.5103$ ($q = 0.8834$).
- **Conclusão**: Mesmo isolando estritamente os ciclos maiores postulados por Richard Tarnas em *Cosmos and Psyche*, os eventos históricos de grande porte não apresentam concentração anômala em relação a datas deslocadas.

---

## 6. Decisão do Marco M2

**Veredito Oficial**: **CAMINHO A (Pivô Metodológico)**
Todos os resultados são 100% reproduzíveis pelo comando `make validate`, que alimenta diretamente o arquivo canônico `data/results.json`.
