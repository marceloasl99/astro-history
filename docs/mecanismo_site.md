# Mecanismo do site e considerações de projeto (v3)

Este documento explica, de ponta a ponta, como o AstroHistory calcula o que mostra, por que cada decisão foi tomada e quais são os limites do que o site afirma.

## 1. Visão geral do fluxo

```
Swiss Ephemeris (pyswisseph)
   │
   ├─ Grade diária 1800–2100 (109.938 dias, 9 corpos)  ──► score de tensão (config/score.yaml) ──► percentil 0–1000
   │
   ├─ Grade de features 1750–2150 (146.462 dias, 409 features) ──► índices anuais ──► gráfico do Dashboard
   │                                                              ──► hindcast walk-forward ──► skill (BSS, AUC)
   │                                                              ──► forecast 2026–2060 (p, intervalo, drivers)
   │
   └─ Cartas de eventos (300 do catálogo + simulador) ──► aspectos, estrelas fixas, casas, mandala SVG

Alvos históricos: catálogo objetivo v2 (N=59), COW Guerras v4, NBER, UCDP/PRIO v24.1 ──► séries mensais
```

Toda página do site lê **caches em JSON** gerados por esse pipeline (`data/timeline_1800_2100.json`, `data/projections_2027_2060.json`, `data/forecast_v3.json`, `data/annual_indices.json`, `reports/hindcast_v3.json`). O servidor (FastAPI + Jinja2) não recalcula efemérides por requisição, exceto no simulador.

## 2. Camada astronômica

| Item | Como é feito | Consideração |
|---|---|---|
| Efemérides | Swiss Ephemeris com arquivos `seas/sepl/semo` instalados (precisão de arco-segundos, não o modo Moshier) | Verificado em runtime: o flag de retorno indica `swieph` |
| Instante do evento | `resolve_event_instant`: fuso IANA real por lat/lon (`timezonefinder` + `zoneinfo`) a partir de 1883; antes disso, Hora Média Local exata (longitude/15, sem arredondar). A conversão pode mudar a data civil (23h em Nova York = 04h UT do dia seguinte) | Antes da v3, o fuso era `round(lon/15)`, que errava em até 3 h e não cruzava a meia-noite |
| Calendário | Gregoriano a partir de 1582-10-15 por padrão; `calendar_region` (britain, russia, greece…) muda a data de adoção; `calendar` força | As datas do catálogo seguem a convenção do padrão; o override existe para eventos registrados em "estilo antigo" |
| Hora desconhecida | 82 dos 300 eventos. A carta usa 12:00 UT e a **Lua é excluída** de aspectos e score (ela anda ~13°/dia) | Sem hora, qualquer posição lunar é um chute de ±6° |
| Casas | Placidus; acima do círculo polar, fallback para Porphyry e depois Signos Inteiros | Placidus é indefinido acima de ~66° de latitude |
| Estrelas fixas | 30 estrelas, só **conjunção** com orbe de 0,3°, e só pontuam se a latitude eclíptica da estrela for ≤ 30° | Vega (62°) e Polaris (66°) nunca estão "sobre" um planeta; checar 4 aspectos × 17 corpos gerava ~5 contatos espúrios por mapa |

## 3. Score de tensão (linha vermelha e percentis)

- Fonte única: `src/core/scoring.py` lê `config/score.yaml` (orbes, pesos por classe de par: Saturno–Plutão 260, Urano–Plutão 220, …; decaimento linear da orbe; trígonos subtraem 20 %).
- A **grade diária** (1800–2100, 12:00 UT, 9 corpos: Sol a Plutão) e a **carta do evento** chamam a mesma função. Um teste de paridade garante que a mesma data dá o mesmo score pelos dois caminhos (diferença máxima 0,002).
- O score bruto vira **percentil empírico 0–1000** sobre os 109.938 dias: 850 significa "mais intenso que 85 % dos dias de 1800–2100". Não há teto nem piso artificiais.
- O **pico anual** (linha vermelha do gráfico) é o dia de maior score do ano na grade, não o máximo de quatro datas sazonais, como era até a v2.
- **Consideração:** os pesos são uma codificação da hierarquia arquetípica da astrologia moderna (Tarnas, Barbault), não valores ajustados aos dados. Por isso o índice foi tratado como hipótese e testado, não como verdade.

## 4. Índices anuais do Dashboard (amarelo, azul, roxo)

Derivados da grade de features (`src/analysis/annual_indices.py`), como percentil da média anual em 1800–2100:

- **Risco Bélico** — ativação média de quadraturas e oposições entre Júpiter, Saturno, Urano, Netuno e Plutão (kernel gaussiano, σ = 4–5°).
- **Inovação Científica** — ativação média de trígonos e sextis entre os 9 corpos.
- **Concentração Planetária (Barbault)** — 1800° menos o Índice Cíclico de Barbault (soma das 10 separações entre os externos). Alto = planetas lentos agrupados; Barbault associou os mínimos do índice a 1914–18, 1939–45 e 1982–83.

Cada série é correlacionada com a história por **deslocamento circular** dos anos (10.000 permutações): compara-se a média do índice nos anos com evento contra a distribuição nula, preservando o agrupamento temporal dos eventos e a autocorrelação dos planetas lentos. Reporta z, p bicaudal, **q (FDR Benjamini-Hochberg)** e o lift do quartil superior. Resultado atual: nada sobrevive ao FDR; na amostra objetiva v2 não há sinal em nenhuma série.

## 5. Features astrológicas (409 colunas, 1750–2150)

`src/features/astro_features.py` calcula ao meio-dia UT, por dia:

| Família | Conteúdo | Por que existe |
|---|---|---|
| Fases sinódicas | seno/cosseno (1º e 2º harmônico) do ângulo de cada um dos 10 pares externos, geo e heliocêntrico | Variável contínua: elimina a escolha de orbe e permite estatística circular |
| Barbault | índice cíclico geo e helio | Índice clássico da astrologia mundana |
| Aspectos | ativação gaussiana para 36 pares × 5 ângulos (0, 60, 90, 120, 180) | Substitui o corte binário "dentro/fora da orbe" |
| Harmônicos | comprimento do vetor resultante nos harmônicos 4 e 8 | Concentração de tensão sem listar aspectos (Addey) |
| Declinação | declinação de 8 corpos e fora-de-limites de Mercúrio, Vênus e Marte | Dimensão ignorada pela longitude |
| Movimento | retrogradação, estações, ingressos, signos cardinais | Marcadores usados por todo mundanista |
| Meios-pontos | Marte/Saturno, Saturno/Plutão, Urano/Plutão, Saturno/Netuno, Saturno/Urano ativados por Sol, Marte e Júpiter (eixo de 90°) | Cosmobiologia (Ebertin) |
| Eclipses | dias até o eclipse solar/lunar mais próximo e janela de ±15 dias | Eventos astronômicos exatos e localizáveis |
| Legado | o score de `score.yaml` | Para comparar o índice v2 com os demais |

As features são agregadas por **mês** (média, e máximo para ativações). A Lua fica fora porque a resolução é diária.

`src/features/astro_events.py` obtém **datas exatas** por busca de raiz (brentq) sobre o Swiss Ephemeris: aspectos (com número da passagem dentro do laço retrógrado), ingressos, estações e eclipses (tipo e ponto de máximo). Conferido contra efemérides publicadas (Saturno☌Netuno 20/02/2026 16:54 UT; Saturno☌Plutão 12/01/2020; eclipse total 08/04/2024).

## 6. Alvos históricos e por que são mensais

| Fonte | Cobertura | O que vira alvo |
|---|---|---|
| Catálogo objetivo v2 (UCDP, COW, NBER, Powell & Thyne, Polity5) | 1800–2025 | mês com evento, por classe |
| COW Inter-State War Data v4.0 | 1816–2007 | início, duração e mortes de guerras interestatais |
| NBER | 1857–2024 | mês em recessão nos EUA; mês de início |
| UCDP/PRIO Armed Conflict v24.1 | 1946–2023 | início de episódios; conflitos ≥ 1.000 mortes |

**Considerações:**
- Com 59 eventos o efeito mínimo detectável era 0,33 desvios-padrão; séries mensais dão milhares de pontos e potência real.
- O catálogo de 300 marcos é **curado em retrospecto** (viés de seleção). Ele alimenta a narrativa e a mandala, **nunca o treino**.
- A contagem de eventos cresce ao longo do tempo (mais Estados, mais registro) enquanto os planetas lentos derivam monotonicamente. O hindcast usa climatologia expansiva e estratificação temporal para não confundir época com geometria.

## 7. Hindcast: como o skill é medido

`src/analysis/hindcast.py`, para cada alvo e cada ano t de 1951 até o fim da cobertura:

1. Treina só com meses de anos ≤ t−1, com intervalo de segurança de 12 meses.
2. Prevê os 12 meses de t.
3. Modelos: climatologia (taxa-base expansiva), autorregressivo (taxa do alvo nos 12/36 meses anteriores), índice legado, Barbault, Tarnas (aspectos duros entre externos), fases sinódicas, todas as 409 features, e AR + features. Logística L2 padronizada; a regularização é escolhida por validação temporal interna nos últimos 20 % do treino.
4. Métricas sobre as previsões acumuladas: **Brier Skill Score** contra a climatologia (IC 95 % por bootstrap em blocos anuais), **AUC**, log-loss e curva de confiabilidade.

**Veredito conservador:** "skill positivo" exige IC do BSS inteiramente acima de zero **e** AUC > 0,55. Com 7 alvos × 5 modelos (35 comparações), um IC marginal isolado é esperado ao acaso; foi o caso de `outer_phases` em recessão NBER (BSS +0,127, mas AUC 0,40), tratado como artefato.

**Resultado:** nenhum modelo astrológico supera a climatologia com IC positivo e discriminação real. O baseline autorregressivo domina os alvos persistentes (BSS +0,85 em recessão em curso, +0,83 em guerra em curso) e a astrologia não acrescenta a ele.

## 8. Forecast 2026–2060 (página Previsão v3)

`src/analysis/forecast_v3.py`:
- Usa, por alvo, o melhor modelo astrológico do hindcast, ajustado em toda a cobertura.
- Intervalo p10–p90 por bootstrap em blocos anuais (60 reamostragens).
- **Drivers**: contribuição linear (coeficiente × valor padronizado) das features no mês de pico de cada ano, com rótulos legíveis.
- **Calendário exato** do ano: aspectos entre planetas lentos, ingressos e eclipses, com data e hora UT.
- **Análogos**: vizinhos mais próximos no espaço padronizado das fases dos 10 pares externos, no máximo um por década (quebra a "confusão de época": Plutão fica 12–30 anos no mesmo signo, então análogos por "mesmo signo" eram sempre a mesma geração). O lift compara a taxa de evento objetivo em ±6 meses dos análogos com a esperada.

**Consideração central:** a página mostra o selo de skill **antes** da curva. Quando o IC inclui zero, a estimativa recomendada é a taxa-base, e a curva é exibida só para transparência e auditoria. A cor de alerta vermelho/amarelo/verde dos "Cenários" descreve geometria, não risco, e a página diz isso.

## 9. Simulador e catálogo

- **Simulador**: o formulário envia POST, que redireciona para a URL GET equivalente (`/simulator?date=…&latitude=…`), compartilhável e recarregável. Entrada validada por Pydantic (data, hora, lat/lon dentro de faixas); o mesmo modelo valida `/api/simulate`.
- **Catálogo**: 46 dos 300 marcos coincidem por data com a amostra objetiva v2 e recebem o selo "✓ N=59"; há filtro para vê-los isolados. Anterior/próximo navegam em ordem cronológica, não por id.
- **Similaridade** (`find_similar_events`): exclui o próprio evento e a janela de ±1 ano (leave-one-out). É uma medida de proximidade angular, exibida com nota de que não implica repetição factual.

## 10. Caches, reprodução e deploy

```bash
make features   # grade de features 1750–2150 (~20 s)
make hindcast   # walk-forward completo (~15 min)
make forecast   # data/forecast_v3.json
make timeline   # timeline e projeções (pico diário real, índices anuais)
make test       # 45 testes: regressão golden, paridade grade↔carta, fuso, datas exatas, alvos, API
```

Produção: `uvicorn src.web.app:app` na porta 81 atrás do nginx (serviço `astro-history.service`). `data/features/` está no `.gitignore` (18 MB, reconstruído em segundos); os demais caches são versionados para que o site suba sem recálculo.

## 11. Limites conhecidos

- As features são diárias (Lua excluída); hora desconhecida em 82 eventos do catálogo.
- COW MID (2.400 disputas) e golpes Powell & Thyne não estão integrados (sem URL de download direto).
- Não há mapas nacionais nem previsão por país — a linha de pesquisa mais promissora que resta.
- O baseline de processo pontual (Hawkes) não foi implementado; o AR cobre parte do agrupamento temporal.
- Tailwind é carregado via CDN.
