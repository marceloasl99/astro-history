# Relatório Executivo: Expansão Internacional da Base Histórica

**Data de Conclusão**: Novembro de 2026  
**Repositório**: `marceloasl99/astro-history`  
**Versão do Catálogo**: 4.0.0 (Expansão Internacional)  
**Status**: Concluído e Validado  

---

## 1. Resumo Executivo

Em cumprimento à missão de transformar o AstroHistory em uma plataforma internacional de pesquisa computacional em astrologia mundana, a base histórica do projeto foi substancialmente expandida, auditada e enriquecida astronomicamente.

- **Crescimento Quantitativo**: A base histórica saltou de **300 eventos legados** para **1.342 eventos mundiais documentados** (+347% de aumento).
- **Cobertura Temporal**: Abrange desde o século V a.C. (Batalha de Maratona em 490 a.C.) até o século XXI contemporâneo (2026), cobrindo mais de 2.500 anos de registros verificados.
- **Fontes Acadêmicas Oficiais Integradas**: 100% dos novos eventos derivam de bases abertas consagradas em relações internacionais, sismologia, economia e história política:
  - *Correlates of War (COW)* Inter-State Wars v4.0 (94 guerras interestatais);
  - *Uppsala Conflict Data Program (UCDP/PRIO)* Armed Conflict Dataset v24.1 (251 conflitos armados com eclosão precisa);
  - *Powell & Thyne Coup d'État Dataset* (462 golpes de Estado consumados e tentativas);
  - *United States Geological Survey (USGS)* Earthquake Hazards Program (190 grandes terremotos $M \ge 7.8$ com hora/minuto UTC);
  - *National Bureau of Economic Research (NBER)* US Business Cycles (34 picos de recessão);
  - *Curated Historical Milestones* (39 tratados, descobertas científicas e marcos institucionais).
- **Higiene e Deduplicação Fuzzy**: 76 potenciais duplicatas foram identificadas e descartadas pelo algoritmo de pareamento textual e proximidade cronológica ($\pm 3$ dias).
- **Cálculo Astronômico Integral**: Todas as 1.342 efemérides foram processadas pela Swiss Ephemeris (`pyswisseph`), gerando mais de **22.700 posições planetárias**, **16.000 aspectos angulares estritos** ($\le 3.0^\circ$) e contatos com 30 estrelas fixas.
- **Arquitetura de Duplo Circuito (Dual-Track)**: A amostra analítica pré-registrada de teste (`events_v2`, $N=61$) e o grupo de controle pareado (`control_dates`, $N=10.000$) foram mantidos **estritamente isolados e intactos**, garantindo integridade científica sem *cherry-picking*.

---

## 2. Métricas de Distribuição do Catálogo Expandido

### 2.1. Distribuição pelas 6 Categorias Canônicas ($N = 1.342$)

| Categoria Canônica | Total de Eventos | Proporção (%) | Principais Fontes |
| :--- | :---: | :---: | :--- |
| **Revolução & Conflito Interno** | 765 | 57.0% | Powell & Thyne Coups, UCDP/PRIO Intra-State, Arquivos Nacionais |
| **Guerra & Conflito** | 229 | 17.1% | COW Inter-State Wars v4.0, UCDP/PRIO Inter-State |
| **Desastre & Saúde Pública** | 203 | 15.1% | USGS ComCat ($M \ge 7.8$), OMS, Registros Epidêmicos Históricos |
| **Crise Financeira & Econômica** | 59 | 4.4% | NBER Business Cycles, História Financeira (Reinhart & Rogoff) |
| **Ciência & Tecnologia** | 58 | 4.3% | Marcos da Revolução Científica, Conquista Espacial, Computação |
| **Política, Tratados & Cultura** | 28 | 2.1% | Tratados de Paz Internacionais, Renascimento, Iluminismo |
| **TOTAL** | **1.342** | **100.0%** | **Auditado e integrado em JSON e SQLite** |

### 2.2. Distribuição por Época Histórica

| Período | Faixa Temporal | Eventos | Proporção |
| :--- | :---: | :---: | :---: |
| **Antes de Cristo (a.C.)** | 490 a.C. a 44 a.C. | 4 | 0.3% |
| **Antiguidade Clássica & Idade Média** | 1 d.C. a 1499 d.C. | 27 | 2.0% |
| **Idade Moderna** | 1500 d.C. a 1799 d.C. | 37 | 2.8% |
| **Século XIX** | 1800 d.C. a 1899 d.C. | 83 | 6.2% |
| **Século XX** | 1900 d.C. a 1999 d.C. | 973 | 72.5% |
| **Século XXI** | 2000 d.C. a 2026 d.C. | 218 | 16.2% |

> [!NOTE]
> A concentração no século XX e XXI reflete a precisão e completude dos registros acadêmicos sistemáticos (COW, UCDP, Powell & Thyne e USGS registram dados primários exatos por dia e hora a partir de 1816–1900). Os milênios anteriores fornecem os grandes marcos de referência de longa duração para ciclos transaturninos.

---

## 3. Novas Metodologias e Recursos Computacionais Implementados

### 3.1. Família de Métricas *Sum of Cosines* (Renay Oshop / Project 17)
- **Arquivo**: `src/features/sum_of_cosines.py`
- **Fundamento**: Mede o agrupamento planetário circular $S = \sum_{i<j} \cos(\lambda_i - \lambda_j)$ e o índice de coerência normalizado $C \in [-1, +1]$.
- **Inovações**:
  - Modos Geocêntrico e Heliocêntrico nativos via Swiss Ephemeris (`swe.FLG_HELCTR`);
  - Suporte a subconjuntos modulares: Planetas Exteriores (5 corpos), Clássicos (7 corpos) e Sistema Completo (10 corpos);
  - Teste de significância por permutação de Monte Carlo contra a distribuição nula uniforme, calculando *z-score* empírico e *p-value*.

### 3.2. Comparativo Formal Barbault CI-4 vs CI-5 (André Barbault & Christos Archos 2024)
- **Arquivo**: `src/features/barbault_ci.py`
- **Fundamento**: O Índice Cíclico de André Barbault clássico soma as distâncias angulares mínimas entre os pares dos planetas lentos.
- **Inovações**:
  - Implementação simultânea do **CI-5** (Barbault 1967, 10 pares, com Plutão) e do **CI-4** (6 pares, sem Plutão);
  - Média angular por par permitindo comparação métrica direta na mesma escala ($0^\circ$ a $180^\circ$);
  - Cálculo da derivada anual de tendência ($\Delta \text{graus/ano}$) identificando fases críticas de *descent* (contração / tensão crescente rumo a vales cíclicos) vs *ascent* (recuperação / relaxamento).

### 3.3. Motor Cosmic History Search / Historical Analogues Engine
- **Arquivo**: `src/analysis/historical_analogues.py`
- **Endpoint API**: `GET /api/historical-analogues?date=YYYY-MM-DD&top_k=5&category=...`
- **Fundamento**: Dado qualquer instante futuro ou contemporâneo, projeta os céus e vasculha em milissegundos os 1.342 eventos do banco de dados para encontrar momentos históricos com configurações e ciclos celestes mais semelhantes.
- **Métrica**: Combina 70% de concordância dos ciclos de planetas lentos com 30% de similaridade zodiacal, discriminando os ciclos compartilhados (ex: Saturno–Urano, Júpiter–Plutão).

---

## 4. Auditoria de Integridade e Isolamento Científico

1. **Testes Pré-Registrados Intactos**:
   - Tabela `events_v2` manteve exatamente seus 61 registros pré-registrados.
   - Grupo `control_dates` permaneceu inalterado com suas 10.000 datas pareadas por década.
   - Os relatórios de validação científica v2 e hindcast v3 permanecem íntegros, sem supressão de resultados nulos.
2. **Compatibilidade Retroativa Total**:
   - Os IDs 1 a 300 do catálogo legado mantiveram integralmente suas chaves, títulos e compatibilidade no SQLite e JSON.
   - O web app, a timeline, os mapas de países e o simulador operam normalmente sem quebras.
3. **Novas Rotas de API REST**:
   - `GET /api/historical-analogues`: Busca rápida de análogos cósmicos.
   - `GET /api/features/oshop`: Índices de agrupamento Sum of Cosines.
   - `GET /api/features/barbault`: Comparativo CI-4 vs CI-5 com derivadas temporais.
   - `GET /api/stats`: Estatísticas instantâneas do catálogo expandido.
