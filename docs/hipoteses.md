# Pré-registro Formal de Hipóteses e Protocolo Estatístico

- **Data do Registro**: 2026-10-29
- **Hash do Commit Base**: `6a2a3d8ab2c19efaa78c1e4642923d8324851985`
- **Repositório**: `marceloasl99/astro-history` (branch `feat/validation-phase3`)
- **Dataset Alvo**: `data/events_v2.csv` (versão 2.0.0, 61 eventos objetivos)
- **Grupo de Controle**: `control_dates` (10.000 datas pareadas por década, seed 42)
- **Grade Diária**: `data/ephemeris/daily_grid_1800_2100.npz` (109.938 dias)

---

## 1. Hipóteses Pré-Registradas

### Hipótese 1 (H1: Distinção frente ao Acaso Estratificado)
O score médio de tensão astrológica dos eventos históricos objetivos é significativamente maior do que o obtido por modelos nulos estratificados por década (N2) e por deslocamento circular (N3):
$$\mathbb{E}[S_{\text{eventos}}] > \mathbb{E}[S_{\text{nulo}}]$$

### Hipótese 2 (H2: Generalização Fora da Amostra Temporal / Walk-Forward)
O efeito observado em H1 mantém o sinal positivo e significância estatística no período de teste intocado (1951–2025) utilizando parâmetros e limiares calibrados exclusivamente no período histórico anterior (1800–1950).

### Hipótese 3 (H3: Estabilidade ao Orbe)
O efeito observado em H1 não é um artefato de tolerância angular, mantendo-se estável com orbes estritos de $1.0^\circ$, $2.0^\circ$ e $3.0^\circ$.

### Hipótese 4 (H4: Identificação do Mecanismo por Ablação)
O sinal de H1 é explicado primariamente por ciclos de planetas externos geracionais (Plutão, Netuno, Urano, Saturno) e não desaparece quando corpos rápidos ou asteroides são removidos.

---

## 2. Modelos Nulos

1. **N1 (Datas Uniformes)**: Amostragem aleatória uniforme de datas entre 1800 e 2025.
2. **N2 (Estratificado por Década)**: Pareamento temporal exato pela década de ocorrência de cada evento histórico, neutralizando a órbita lenta dos planetas transpessoais.
3. **N3 (Deslocamento Circular / Teste Primário)**: Desloca todo o vetor temporal de eventos por um mesmo offset aleatório circular uniforme $k \in [0, \text{span}]$, preservando perfeitamente a autocorrelação temporal e o agrupamento intrínseco dos eventos.
4. **N4 (Embaralhamento de Rótulos de Classe)**: Permutação aleatória dos rótulos de classes entre os eventos para verificar se o score diferencia tipos de eventos (ex: guerra vs. crise econômica).

---

## 3. Métricas e Controle de Múltiplas Comparações

- **Número de Permutações**: $N = 10.000$ iterações por teste.
- **$p$-valor Empírico**:
  $$p = \frac{1 + \sum_{i=1}^{N} \mathbb{I}(S_{\text{nulo}}^{(i)} \ge S_{\text{obs}})}{N + 1}$$
- **Tamanho do Efeito**:
  $$z = \frac{S_{\text{obs}} - \mu_{\text{nulo}}}{\sigma_{\text{nulo}}}$$
- **Controle de Múltiplas Comparações (FDR)**:
  - Procedimento de Benjamini-Hochberg aplicado a toda a família de testes de hipótese com nível crítico $q = 0.05$.

---

## 4. Critérios Inegociáveis de Decisão (Marco M2)

- **Sucesso (Go para Fase 4 / Caminho C)**:
  - H1 e H2 confirmadas com $q < 0.05$, $z \ge 0.3$ e persistência nos orbes de $1.0^\circ$ e $2.0^\circ$.
- **Fracasso (Pivô para Caminho A - Metodológico)**:
  - Qualquer resultado que não atenda integralmente aos critérios acima será registrado como resultado nulo/negativo. A Fase 4 será cancelada e o projeto publicará o estudo metodológico transparente demonstrando a ausência de sinal preditivo estatístico.
