# AstroHistory: Relatório Final de Investigação Científica & Auditoria Metodológica

**Versão**: 1.0.0  
**Data**: 2026-10-29  
**Repositório**: `marceloasl99/astro-history`  
**Licença**: GNU AGPL-3.0-or-later  

---

## 1. Resumo Executivo

O projeto original `astro-history` possuía uma infraestrutura de cálculo astronômico de alta precisão (baseada no Swiss Ephemeris), porém operava como uma **máquina de confirmação retrospectiva**, sujeita a múltiplos vieses e artefatos metodológicos graves:
- Ausência total de grupos de controle e testes nulos;
- Vazamento de dados (*data leakage*) no motor de similaridade (`find_similar_events`), que comparava eventos com eles mesmos gerando concordâncias artificiais de 98.5%;
- Saturação matemática em 990 pontos devido a uma curva de contraste arbitrária;
- Inflação combinatorial de contatos estelares (1.467 contatos em 300 mapas) decorrente do teste de 4 aspectos maiores sobre 17 corpos e 30 estrelas com orbe de 0.3° (o que gerava ~5 contatos por mapa por puro ruído probabilístico);
- Amostragem temporal assimétrica (4 amostras por ano nos anos comuns versus datas exatas nos anos de eventos);
- Seleção subjetiva de eventos históricos sem critérios operacionais pré-estabelecidos.

Este plano de melhoria reconstruiu integralmente o repositório, convertendo-o em uma **plataforma de pesquisa aberta, pré-registrada e reprodutível**.

Submetido a testes estatísticos controlados com 10.000 permutações de deslocamento circular (N3), pareamento estratificado por década (N2) e controle de FDR ($q = 0.05$), **a hipótese nula não pôde ser rejeitada**:
- **Efeito Geral vs N3 Deslocamento Circular**: $z = -0.506$, $p = 0.6941$ ($q = 0.9772$).
- **Teste Fora da Amostra Temporal (1951–2025)**: $z = -0.851$, $p = 0.7996$ ($q = 0.9772$).

Em consonância com o pré-registro em `docs/hipoteses.md`, o projeto executou o **CAMINHO A (Pivô Metodológico)**: cancelamento de qualquer funcionalidade preditiva determinística, documentação transparente dos resultados negativos e transformação da plataforma em uma ferramenta educacional de literacia estatística e pensamento crítico.

---

## 2. Auditoria e Correções Metodológicas (Fase 1)

| Dimensão Auditada | Estado Anterior (v0-baseline) | Estado Corrigido (Fase 1) | Justificativa Matemática |
| :--- | :--- | :--- | :--- |
| **Similaridade e Vazamento** | Comparava o ano com o próprio catálogo (auto-match de 98.5%). | **Leave-One-Out estrito**: exclusão de $|ano - Y| \le 1$. | Erradicação de contaminação de alvo (*target leakage*). |
| **Contatos com Estrelas Fixas** | 1.467 contatos em 300 eventos (~4.9 por mapa). | **216 contatos** (~0.72 por mapa). | Restrição exclusiva a Conjunções ($0^\circ \pm 0.3^\circ$). O cálculo anterior de 4 aspectos cobria 3.6° por par, gerando 5.1 contatos esperados ao acaso. |
| **Saturação do Score** | Clamp fixo em 990.0 via fórmula `min(1.0, excess/640)**1.35 * 920 + 70`. | **Percentil Empírico Contínuo** (0 a 1000). | Score derivado da distribuição real dos 109.938 dias da grade diária 1800–2100. |
| **Incerteza da Lua** | Calculada arbitrariamente ao meio-dia para mapas sem hora. | **Excluída do score** quando `is_time_known = False`. | A Lua move-se ~13.2°/dia; orbe de 3° cobre ~22% do zodíaco por dia, tornando a Lua ao meio-dia puro ruído. |
| **Amostragem Temporal** | 4 pontos/ano misturados com datas exatas de eventos. | **Grade diária vetorizada completa (365 dias/ano)**. | Estatísticas homogêneas (média, mediana, p90 e máximo de cada ano). |

---

## 3. Dataset Objetivo `events_v2` e Grupo de Controle (Fase 2)

O catálogo `events_v2` foi estruturado sob regras públicas pré-estabelecidas:
- Fontes canônicas: Correlates of War (COW), UCDP/PRIO, NBER, Powell & Thyne Coup Dataset e Polity5/V-Dem.
- Regra de limite regional: nenhum país isolado representa mais de 20% do dataset (maior concentração: Estados Unidos com 18.0%).
- Precisão temporal: 100% dos eventos incluídos possuem precisão de dia documentada.
- Grupo de Controle: 10.000 datas aleatórias pareadas e estratificadas por década (seed = 42).

---

## 4. Testes de Hipóteses e Resultados Estatísticos (Fase 3)

| Hipótese | N | Score Obs. | Nulo sob N3 (Média ± DP) | Efeito ($z$) | $p$-valor | $q$ (FDR) | Veredito |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **H1 Geral vs N3 Circular Shift** | 59 | 481.1 | 500.6 ± 38.5 | -0.506 | 0.6941 | 0.9772 | **Nulo não rejeitado** |
| **H1 Geral vs N2 Estratificado** | 61 | 477.6 | 493.7 ± 35.9 | -0.450 | 0.6715 | 0.9772 | **Nulo não rejeitado** |
| **H1 Classe: Guerra Interestadual** | 15 | 462.1 | 499.4 ± 73.3 | -0.509 | 0.6918 | 0.9772 | **Nulo não rejeitado** |
| **H1 Classe: Crise Econômica** | 10 | 547.6 | 501.9 ± 93.8 | +0.487 | 0.3112 | 0.9772 | **Nulo não rejeitado** |
| **H1 Classe: Golpe de Estado** | 12 | 538.4 | 501.6 ± 84.9 | +0.434 | 0.3327 | 0.9772 | **Nulo não rejeitado** |
| **H2 Treino Temporal (1800–1950)** | 28 | 512.4 | 499.4 ± 56.8 | +0.229 | 0.4083 | 0.9772 | **Nulo não rejeitado** |
| **H2 Teste Fora da Amostra (1951–2025)** | 33 | 456.5 | 501.6 ± 53.0 | -0.851 | 0.7996 | 0.9772 | **Sem sinal preditivo** |
| **Controle Negativo (Ruído Puro)** | 61 | 427.8 | 501.5 ± 37.2 | -1.982 | 0.9772 | 0.9772 | **Pipeline Íntegra** |

---

## 5. Conclusões Epistemológicas

1. **A Ilusão da Correlação**: Quando astrólogos afirmam que grandes guerras coincidem com "tensão cósmica extrema", a sobreposição ocorre porque o número de corpos celestes (17 corpos $\times$ 4 aspectos maiores $\times$ 28 estrelas) garante que praticamente qualquer dia do ano apresente múltiplos aspectos duros por pura combinatória probabilística.
2. **Preservação da Autocorrelação Temporal (O Modelo Nulo N3)**: Planetas lentos (Plutão, Netuno, Urano) levam décadas em um mesmo signo ou aspecto. Um modelo nulo ingênuo (N1) pode sugerir falsos sinais simplesmente porque os eventos se concentram no século XX. Quando o catálogo é submetido ao teste de deslocamento circular (N3), que mantém o espaçamento histórico real, qualquer diferença em relação ao nulo desaparece.
3. **Compromisso com a Ciência Aberta**: Este estudo demonstra a importância de pré-registrar hipóteses e tratar resultados negativos como contribuições científicas fundamentais para o esclarecimento público.
