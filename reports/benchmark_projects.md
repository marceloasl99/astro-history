# Relatório de Benchmarking Internacional: Projetos Computacionais em Astrologia Mundana e História

**Data da Auditoria:** 02 de Novembro de 2026  
**Autor:** Equipe de Pesquisa AstroHistory (`marceloasl99/astro-history`)  
**Status:** Pesquisa Internacional Concluída  

---

## 1. Introdução & Escopo da Investigação

A presente investigação examina as principais iniciativas internacionais, publicações acadêmicas, repositórios de código aberto e plataformas analíticas dedicadas ao estudo computacional e quantitativo da relação entre configurações astronômicas e acontecimentos históricos globais (Astrologia Mundana).

O objetivo é identificar metodologias avançadas, técnicas de engenharia de dados, representações de features astronômicas, métodos de machine learning e bancos de dados históricos estruturados que possam ser incorporados ou testados criticamente no **AstroHistory**.

---

## 2. Investigação Detalhada por Projeto

### A. Renay Oshop — AyurAstro, History Predictor & The Big Astrology Book of Research

**Pesquisadora:** Renay Oshop (Bióloga Computacional, Cientista de Dados e Astróloga Védica).  
**Plataforma / Repositório:** `ayurastro.com` e GitHub [`renayo/big_astrology_book`](https://github.com/renayo/big_astrology_book).  
**Publicação Chave:** *"How Machine Learning Addressed an Ancient Claim"*, *Correlation*, Vol. 34, No. 2, 2022, pp. 35–41.

#### 1. Corpus de Dados & Extração Wolfram
- Oshop utilizou um corpus de aproximadamente **7.000 a 7.800 acontecimentos históricos documentados**, compilados a partir de bases de conhecimento computacional estruturadas (Wolfram Research / Wolfram Cloud) e bases enciclopédicas mundiais.
- Cada acontecimento continha datação temporal, localização e uma descrição textual do fenômeno (conflito militar, tratado, revolução, desastre, crise econômica, invenção).

#### 2. Metodologia: Embeddings Semânticos & Similaridade Geométrica
- **Processamento de Linguagem Natural (NLP):** Oshop gerou *text embeddings* vetoriais das narrativas históricas utilizando modelos densos de linguagem. O objetivo foi quantificar a similaridade semântica entre acontecimentos (ex.: identificar que uma revolta civil se assemelha a outros motins populares, independentemente do vocabulário exato).
- **Similaridade Geométrica de Mapas:** Cada data histórica teve suas posições planetárias geocêntricas calculadas, medindo a distância angular e harmônica entre os céus dos eventos.
- **Cruzamento Multimodal:** Oshop investigou se pares de acontecimentos com alta proximidade astronômica apresentavam similaridade textual estatisticamente superior à esperada pelo acaso.

#### 3. A Métrica "Sum of Cosines" (Projeto 17)
No Projeto 17 (*Planetary Alignment and Historical Events*), Oshop formulou uma métrica contínua e elegante para mensurar a **coerência/agrupamento planetário geral** no céu, sem depender de orbes binários arbitrários:

$$\text{Sum of Cosines (SoC)} = \sum_{i < j} \cos(\lambda_i - \lambda_j)$$

Para $N = 8$ corpos celestes, existem $\binom{8}{2} = 28$ pares diários.
- Quando os planetas estão em conjunção exata ($0^\circ$), $\cos(0^\circ) = +1.0$;
- Em quadratura ($90^\circ$), $\cos(90^\circ) = 0.0$;
- Em oposição ($180^\circ$), $\cos(180^\circ) = -1.0$.

**Resultado Notável & Análise Crítica:**
- Oshop relatou uma elevação de **+148% no índice de agrupamento planetário em datas históricas** em comparação com datas de controle aleatórias ($p < 0.0001$).
- **Lição Fundamental para o AstroHistory:** Na astrologia mundana clássica, costuma-se postular que guerras e crises são causadas prioritariamente por aspectos tensos (quadraturas de $90^\circ$ e oposições de $180^\circ$), enquanto conjunções e trígonos trariam harmonia. O teste de Oshop demonstrou o oposto: os grandes marcos históricos concentram-se em geometrias de **alto agrupamento angular (conjunções múltiplas e stelliums)**, que marcam o início ou reinício de ciclos sinódicos, ao passo que os aspectos duros isolados frequentemente apresentam resultado nulo.

#### 4. Projeto 19 vs Projeto 17: Divergência nos Aspectos Específicos
- No Projeto 19 (*Mundane Astrology — Specific Aspect Claims*), Oshop testou alegações tradicionais sobre pares planetários individuais isolados (ex.: Marte-Saturno gerando conflitos) e obteve resultados amplamente nulos ou inconsistentes.
- **Por que divergem?** A resposta reside na diferença entre a geometria coletiva de todo o sistema solar (capturada pelo *Sum of Cosines*) e os pares isolados analisados com orbes estritos. Quando analisados em isolamento, o ruído domina; quando analisada a concentração sinódica global, emergem picos de correlação.

#### 5. Projeto 48: Algoritmos Genéticos para Seleção de Features
- No Projeto 48, Oshop empregou algoritmos genéticos evolucionários para pesquisar subconjuntos ótimos de variáveis astrológicas (posições, dignidades, aspectos, harmônicos) que melhor discriminavam classes de eventos.
- **Alerta Metodológico para o AstroHistory:** Algoritmos genéticos e seleções gulosas em espaços de alta dimensionalidade sofrem severamente de *overfitting* se não houver um *holdout* temporal rigorosamente congelado e validação cruzada walk-forward.

---

### B. André Barbault & a Avaliação Empírica de Christos Archos (2024 / 2025)

**Pesquisador:** Christos Archos (Astrólogo e Pesquisador Quantitativo, Grécia).  
**Publicação:** *"The Barbault Cyclic Index: Empirical Evaluation of CI-4 versus CI-5 across 96 Historical Events"*, `chrisarchos.com`, 2024.

#### 1. O Índice Cíclico de Barbault
Formulado pelo astrólogo francês André Barbault na década de 1960, o Índice Cíclico é a soma das separações angulares entre os planetas exteriores.
- **Fórmula Original (CI-5):** Considera os 5 planetas lentos (Júpiter, Saturno, Urano, Netuno e Plutão), totalizando 10 pares planetários:
  $$\text{CI-5}(t) = \sum_{i < j}^{5} \Delta\lambda_{i,j}(t)$$
  onde $\Delta\lambda_{i,j} \in [0^\circ, 180^\circ]$ é a menor distância angular eclíptica.
- **Variação CI-4:** Proposta por astrólogos contemporâneos que excluem Plutão (considerando apenas Júpiter, Saturno, Urano e Netuno, totalizando 6 pares).

#### 2. Metodologia do Estudo de Archos
- **Amostra:** 96 marcos geopolíticos e históricos mundiais cobrindo **2.826 anos** (de 800 a.C. até 2025 d.C.).
- **Efemérides:** Alta precisão via motor astronômico (`astronomy-engine`).
- **Controle Estatístico:** **50.000 permutações de Monte Carlo por deslocamento temporal circular (*circular shift*)**, preservando a autocorrelação de longo curso dos planetas lentos.

#### 3. Conclusões e Implicações
- **CI-5 (com Plutão):** Alcançou significância estatística empírica com **$p = 0.035$** na amostra macro-histórica milenar. As grandes crises e pontos de inflexão coincidem estatisticamente com fases de contração mínima do índice.
- **CI-4 (sem Plutão):** Falhou no teste de significância (**$p = 0.320$**).
- **Importância para o AstroHistory:** O AstroHistory já possui a série `Barbault Concentration` em seu dashboard. No entanto, devemos expor formalmente tanto o CI-5 quanto o CI-4 em nossas features e relatórios comparativos, permitindo que pesquisadores auditem a contribuição de Plutão na contração cíclica global.

---

### C. Richard Tarnas — *Cosmos and Psyche* (2006)

**Autor:** Richard Tarnas (Filósofo e Historiador Cultural, CIIS).  
**Obra:** *Cosmos and Psyche: Intimations of a New World View* (Viking, 2006).

#### 1. A Tese dos Ciclos dos Planetas Exteriores
Tarnas sustenta que as grandes ondas de transformação cultural, revolução política, crises econômicas e florescimento filosófico correlacionam-se com os ciclos de conjunção, quadratura e oposição entre os planetas lentos:
- **Saturno–Plutão (~36 anos):** Épocas de gravidade histórica, totalitarismo, conflitos existenciais, guerras mundiais (1914, 1939, 2001, 2020).
- **Urano–Plutão (~127 anos):** Revoluções culturais, impulsos radicais de liberdade e rupturas com a autoridade (década de 1960).
- **Saturno–Urano (~45 anos):** Choque entre conservadorismo e inovação, crises de governabilidade.
- **Urano–Netuno (~171 anos):** Renascimentos espirituais, colapso de impérios utópicos (dissolução da URSS em 1989-1991).

#### 2. Confronto Epistemológico com os Resultados do AstroHistory
- O AstroHistory testou formalmente a tese de Tarnas na Fase 2 (`H4`, $N = 59$) e na Fase 3 (hindcast walk-forward em alvos mensais).
- **Resultado do AstroHistory:** A tese obteve resultado nulo estrito ($z = -0.063, p = 0.979$; BSS $\le 0$).
- **Diagnóstico da Discrepância:**
  1. *Orbes Utilizados:* Tarnas trabalha com orbes flexíveis de até $10^\circ$ a $15^\circ$, abrangendo janelas de vários anos (ex.: o alinhamento de 1960 a 1972). Em um horizonte temporal contínuo, orbes amplos cobrem mais de 35% de qualquer século, inflando artificialmente o número de eventos coincidentes.
  2. *Viés de Confirmação Historiográfico:* Historiadores selecionam retrospectivamente os eventos que ilustram o arquétipo. Quando submetido a uma amostra pré-registrada e independente de datas exatas de início de guerras (COW) e recessões (NBER), o poder preditivo desaparece.
- **Conclusão para o AstroHistory:** Preservar a honestidade estatística. Devemos testar as orbes de Tarnas como variáveis gaussianas contínuas (como já introduzido no v3), mas manter o registro claro de que a tese, quando avaliada preditivamente, não superou os modelos nulos.

---

### D. Katarche & Astro-Databank

**Conceito / Plataforma:** *Katarche* (Software e arquivo incepcional histórico) e *Astro-Databank* (Astrodienst).

#### 1. O que Fazem de Melhor
- **Rigor na Proveniência Documental:** Cada carta natal ou incepcional possui citação de fonte bibliográfica primária, hora oficial e respectivo *Rodden Rating* (AA = certidão/registro de nascimento, A = relato de memória confiável, B = biografia, DD = horário especulativo/contestado).
- **Tratamento de Horário Desconhecido:** Documentação explícita de quando uma data histórica possui apenas o dia, descartando casas e Ascendentes espúrios.
- **Separação entre Tradição Katárquica e Astrologia Mundana:** A astrologia incepcional estuda o "nascimento" de uma entidade ou iniciativa; a astrologia mundana analisa os ciclos de macro-escala.

---

### E. World Cycles Model

**Repositório:** GitHub [`nbbulk-dotcom/world-cycles-platform`](https://github.com/nbbulk-dotcom/world-cycles-platform).  
**Foco:** Decomposição de Fourier, análise espectral e ressonâncias harmônicas de dados históricos e econômicos.

#### 1. Técnicas Relevantes
- Decomposição periódica de séries temporais longas utilizando transformadas de Fourier e wavelets para detectar ciclos recorrentes de 18,6 anos (nós lunares), 20 anos (Júpiter-Saturno) e 36 anos (Saturno-Plutão).
- **Limitação Identificada:** Muitas séries históricas apresentam autocorrelação e não-estacionariedade que produzem picos espectrais espúrios na transformada de Fourier ingênua se os dados não forem diferenciados e destendenciados adequadamente.

---

### F. Anvaya Jyotish Geo & Cosmic Vedic Analyzer

**Repositórios / Plataformas:** `anvayajyotish.com/geo` e GitHub [`Ishanoshada/CosmicVedicAnalyzer`](https://github.com/Ishanoshada/CosmicVedicAnalyzer).

#### 1. Funcionalidades
- **Camada Geopolítica e Mapas Nacionais:** Mapeamento de cartas natais de fundação de mais de 100 países para cruzamento com trânsitos celestes contemporâneos.
- **Machine Learning em Datasets CSV:** O *Cosmic Vedic Analyzer* aplica Random Forest e K-Means clustering a eventos históricos para agrupar assinaturas astrológicas comuns.

---

## 3. Matriz Comparativa de Capacidades

| Dimensão / Funcionalidade | AstroHistory (v3 Atual) | Renay Oshop (Big Ast. Book) | Christos Archos (2024) | World Cycles Platform | Katarche / ADB |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Precisão de Efemérides** | Swiss Ephemeris (arco-segundo) | Moshier / Swiss Ephem | astronomy-engine | Algoritmos simplificados | Swiss Ephemeris |
| **Tamanho da Base de Eventos** | 300 geral / 59 objetivo | ~7.000–7.800 (Wolfram) | 96 eventos | Centenas de séries | Milhares |
| **Métrica Sum of Cosines** | ❌ Não implementada | ✅ Implementada (+148%) | ❌ Não | ❌ Não | ❌ Não |
| **Índice de Barbault** | ✅ Implementado (CI-5) | ❌ Não | ✅ Testou CI-4 vs CI-5 | ❌ Não | ❌ Não |
| **Similaridade de Mapas (Search)** | ❌ Apenas leave-one-out | ✅ Text Embeddings + Ângulos | ❌ Não | ❌ Não | ❌ Consulta manual |
| **Hindcast Walk-Forward** | ✅ BSS, AUC, Log-Loss | ❌ Permutação / Regressão | ✅ Permutação Monte Carlo | ❌ Não | ❌ Não |
| **Controle de FDR e TOST** | ✅ Rigoroso e auditado | ❌ Apenas valor p | ❌ Apenas valor p | ❌ Não | ❌ Não |
| **Transparência de Nulos** | ✅ Publica resultados nulos | ✅ Publica resultados nulos | ✅ Publicou falha do CI-4 | ❌ Viés positivo | ❌ Neutro |

---

## 4. Técnicas Selecionadas para Incorporação Imediata ao AstroHistory

1. **Métrica "Sum of Cosines" (Oshop / Projeto 17):**
   - Criar o módulo [`src/features/sum_of_cosines.py`](file:///home/astro/src/features/sum_of_cosines.py).
   - Calcular séries contínuas diárias e mensais para:
     - 5 planetas exteriores (10 pares), geocêntrico e heliocêntrico;
     - 9 corpos celestes clássicos (36 pares), geocêntrico e heliocêntrico.
   - Normalizar de 0 a 1000 e avaliar se a hipótese de Oshop de elevação em datas históricas se sustenta contra o grupo de controle estratificado do AstroHistory.

2. **Comparação Formal Barbault CI-4 vs CI-5 (Archos 2024):**
   - Criar o módulo [`src/features/barbault_ci.py`](file:///home/astro/src/features/barbault_ci.py) expondo ambas as métricas para comparação histórica sistemática.

3. **Mecanismo "Cosmic History Search" (Historical Analogues Engine):**
   - Criar o módulo [`src/analysis/historical_analogues.py`](file:///home/astro/src/analysis/historical_analogues.py).
   - Permitir que o usuário informe qualquer data (passada ou futura) e o motor resgate os acontecimentos históricos reais cujas configurações astronômicas apresentaram maior similaridade angular cosseno, classificando-os por tema e contexto.

4. **Expansão Massiva da Base Histórica:**
   - Incorporar COW v4.0, UCDP/PRIO v24.1, Powell & Thyne Coups, USGS Earthquakes e marcos históricos positivos, elevando o catálogo geral para mais de 1.100 registros com proveniência acadêmica integral.
