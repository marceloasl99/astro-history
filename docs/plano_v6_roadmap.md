# Plano de Evolução AstroHistory v6 — Roadmap

**Data:** 06/11/2026
**Status:** PROPOSTA — nada implementado. Documento de planejamento para revisão antes de qualquer execução.
**Documento companheiro:** [`spec_modulo_pessoal_natal_transitos.md`](spec_modulo_pessoal_natal_transitos.md) (especificação técnica do módulo pessoal).
**Versão alvo:** `v6.0.0`

---

## 0. Resumo executivo

O AstroHistory v5 é uma plataforma madura em três pilares: astronomia de precisão (Swiss Ephemeris), rigor estatístico (modelos nulos, hindcast walk-forward) e uma interface web completa. O plano v6 evolui a plataforma em **quatro frentes**, nesta ordem:

| Frente | Objetivo | Resultado esperado |
| :--- | :--- | :--- |
| **A. Dados** | Mais eventos históricos, mais períodos (antes de 1800, Antiguidade), mais categorias, melhor equilíbrio. | Catálogo de ~1.342 → **2.500–3.000 eventos**; pré-1800 de 73 → **≥ 600**; taxonomia em 2 níveis com polaridade. |
| **B. Acurácia** | Efemérides completas, tempo histórico por país, novos alvos preditivos com skill medido. | Precisão Swiss Ephemeris integral; **8 categorias** estimadas (hoje 4) com badge de skill; pré-registro v4. |
| **C. Navegação & UX** | Site mais intuitivo sem perder nenhuma camada técnica. | Nav em 4 áreas, busca global, catálogo facetado, glossário, i18n por chaves, acessibilidade AA. |
| **D. Módulo Pessoal** | Mapa natal individual + trânsitos de toda a vida (datas exatas) + progressões secundárias. | Páginas `/natal`, `/natal/chart`, `/natal/transits`, `/natal/progressions`; motor vetorizado < 1,5 s por vida inteira. |

**Invariantes (o que não muda):** a amostra analítica congelada (`events_v2`, N=59–61), o `config/score.yaml` que define o score de tensão, a reprodutibilidade dos resultados v3/v5 (hindcast, modelos nulos), a licença AGPL-3.0, o modelo de segurança (APIs apenas internas), os três temas e o bilinguismo PT/EN.

**Esforço estimado:** 16–20 semanas de trabalho sequencial; as frentes A/B, C e D podem avançar em paralelo após a Fase 0 (ver §8).

---

## 1. Diagnóstico do estado atual (verificado no servidor em 06/11/2026)

### 1.1 Dados

| Indicador | Valor atual | Observação |
| :--- | ---: | :--- |
| Eventos no catálogo (`events`) | 1.342 | Track A (exploratório). |
| Amostra analítica (`events_v2`) | 59–61 | Track B, congelada. |
| Eventos com hora conhecida | 389 (29%) | 953 sem hora → sem casas, Lua aproximada. |
| Eventos antes de 1800 | ~73 (5,4%) | Século XX concentra 973 (72,5%). |
| Eventos a.C. | 4 | Antiguidade praticamente ausente. |
| Categoria dominante | *Revolução & Conflito Interno*: 765 (57%) | Reflexo dos 462 golpes Powell & Thyne. |
| Categorias sub-representadas | *Ciência & Tecnologia*: 58; *Política, Tratados & Cultura*: 28 | Polaridade construtiva quase inexistente. |
| País mais frequente | Estados Unidos: 98 (7,3%) | Dentro da regra de 20%. |
| Colunas de proveniência na tabela `events` | Nenhuma | `source`, `date_precision`, `quality_tier` existem só no JSON/plano, não no esquema SQL. |

### 1.2 Motor astronômico

| Item | Estado | Impacto |
| :--- | :--- | :--- |
| Arquivos Swiss Ephemeris em `/usr/share/libswe/ephe` | Apenas `seas_*` (asteroides) e `semo_*` (Lua, 0–4200 d.C.). **Não há `sepl_*`/`seplm_*` (planetas).** | Planetas calculados pelo fallback **Moshier** (precisão ~0,1″ para 3000 a.C.–3000 d.C., mas não é a efeméride suíça completa anunciada no README). Lua a.C. sem `semom_*` também cai em Moshier. |
| Corpos | Sol…Plutão, Ceres, Pallas, Juno, Vesta, Quíron, Lilith média, Nodo verdadeiro | Completo para astrologia moderna. |
| Casas | Placidus; fallback Porphyry e Signos Inteiros acima do círculo polar | Sem escolha de sistema pelo usuário. |
| Aspectos (pesquisa) | 0°, 90°, 120°, 180°, orbe fixa 3° (`score.yaml`) | Congelado por pré-registro — manter. |
| Aspectos (trânsitos de países) | 5 maiores, orbe fixa 2,5° (sextil 2,0°) | Orbe uniforme, sem distinção por velocidade do planeta. |
| Amostragem da linha de ativação de países | **1 ponto por ano (1º de julho)** | Perde trânsitos rápidos e passagens retrógradas; inadequado para datas exatas. |
| Fusos históricos | LMT antes de 1883 (corte global) | Correto para EUA; vários países adotaram hora legal depois (Brasil: 1914). |
| Calendário | Tabela `GREGORIAN_ADOPTION` por país | Verificar cobertura (Rússia 1918, Grécia 1923, Turquia 1926…). |
| Progressões / geocodificação | Inexistentes | Usuário digita latitude/longitude manualmente. |

### 1.3 Interface

- Navegação plana com 8 itens (`Dashboard, Catálogo, Países, Simulador, Correlações, Previsão, Cenários, Metodologia`); sem agrupamento, sem busca global.
- Vocabulário técnico exposto sem glossário (orbe, BSS, percentil 1000, TOST, FDR, Índice Cíclico).
- Catálogo de 1.342 eventos com filtro por categoria e texto; sem facetas de período, região, precisão ou polaridade.
- i18n em `static/js/i18n.js` por **correspondência de texto em português** (25 KB), sem chaves `data-i18n`; traduções aplicadas no cliente após o render (risco de "flash").
- Três temas (claro, escuro, OLED) bem resolvidos; Chart.js sincronizado.

### 1.4 Infra, qualidade e consistência

- Serviço `astro-history.service` roda `uvicorn` como **root** em **`0.0.0.0:81`**; nginx na porta 80 sem referência ao projeto. A proteção de `/api/*` depende exclusivamente do middleware da aplicação.
- 96 funções de teste em `tests/` (README anuncia 100).
- `pyproject.toml` declara versão `3.0.0`; README anuncia `5.0.0`.
- Sem rate limiting em rotas de cálculo pesado (`/simulator`, `/api/simulate`).

---

## 2. Princípios do plano

1. **Dois circuitos continuam separados.** Track A (exploração, análogos, UI) cresce livremente; Track B (teste de hipótese) permanece imutável. Qualquer novo teste estatístico nasce de um **pré-registro novo** (`docs/hipoteses_v4.md`) escrito *antes* de rodar.
2. **Honestidade epistêmica em toda a UI.** Onde houver estimativa de categoria futura ou leitura simbólica pessoal, o skill medido (ou a ausência dele) aparece ao lado, com link para a metodologia.
3. **Configuração como fonte de verdade.** `score.yaml` fica congelado; o módulo pessoal e os trânsitos ganham `config/natal.yaml` próprio, auditável e versionado.
4. **Precisão astronômica antes de precisão interpretativa.** Efemérides completas, tempo local correto e datas exatas são pré-requisito de qualquer narrativa.
5. **Sem dependência externa em tempo de execução.** Geocodificação, efemérides, tiles e bibliotecas ficam no servidor (coerente com o modelo de segurança atual e com a privacidade de dados de nascimento).
6. **Nada se perde.** Toda página, série, tabela e teste atual continua acessível; mudanças de UX reorganizam, não removem.

---

## 3. Frente A — Dados históricos

### 3.1 Metas quantitativas (Track A)

| Meta | Hoje | Alvo v6 |
| :--- | ---: | ---: |
| Total de eventos | 1.342 | 2.500–3.000 |
| Antes de 1800 | 73 | ≥ 600 |
| Antes de 1 d.C. | 4 | ≥ 100 |
| Eventos de polaridade construtiva (ciência, tratados, direitos, saúde positiva) | ~86 | ≥ 500 |
| Participação máxima de uma categoria | 57% | ≤ 35% |
| Participação máxima de um país | 7,3% | ≤ 15% |
| Registros com `source_id` + `source_url` + `date_precision` | 0% (SQL) | 100% |
| Eventos com `quality_tier` A ou B | — | ≥ 85% |

### 3.2 Fontes candidatas

Critérios: licença compatível com redistribuição de **fatos datados** (CC0/CC BY/domínio público/uso acadêmico), datação com precisão declarada, coordenadas obtíveis.

| # | Fonte | Período | Categoria | Licença | Volume útil (est.) | Prioridade |
| :-- | :--- | :--- | :--- | :--- | ---: | :---: |
| 1 | **NOAA NCEI Significant Earthquake Database** | 2150 a.C.–hoje | Desastre natural | Domínio público (US Gov) | 600–900 (M ≥ 7,5 ou ≥ 1.000 mortes) | Alta |
| 2 | **Smithsonian Global Volcanism Program** (erupções VEI ≥ 5) | Holoceno | Desastre natural | Livre com citação | ~150 | Alta |
| 3 | **NCEI Global Historical Tsunami DB** | 2000 a.C.–hoje | Desastre natural | Domínio público | ~200 (validade ≥ 3) | Média |
| 4 | **Brecke Conflict Catalog** (Georgia Tech / Clio Infra) | 1400–2000 | Guerra & conflito | Acadêmico aberto (verificar) | ~800 (≥ 32 mortes em batalha, filtrar por magnitude) | Alta |
| 5 | **Wikidata** (batalhas, tratados, independências, com qualificador de precisão de data) | Toda a história | Múltiplas | CC0 | Ilimitado; usar como camada C auditada | Alta |
| 6 | **Reinhart & Rogoff / HBS Global Crises Data** | 1800–2016 | Economia | Acadêmico aberto | ~300 (crises bancárias, defaults, cambiais) | Alta |
| 7 | **Jordà-Schularick-Taylor Macrohistory DB** | 1870–2020 | Economia | Livre com citação | ~90 recessões/crises em 18 países | Média |
| 8 | **Polity5 / V-Dem** (transições de regime) | 1800–2023 | Política | Livre com citação | ~400 | Média |
| 9 | **Archigos** (saídas irregulares de líderes) | 1875–2015 | Política | Aberto | ~250 | Média |
| 10 | **PA-X Peace Agreements Database** (Edimburgo) | 1990–2023 | Tratados & paz | Pesquisa não comercial (verificar compatibilidade AGPL) | ~200 acordos-quadro | Média |
| 11 | **UN Treaty Collection** (tratados multilaterais, data de adoção) | 1945–hoje | Tratados & paz | Público | ~150 | Média |
| 12 | **Nobel Prize API** (datas de descoberta citadas) + **NASA NSSDCA** (lançamentos pioneiros) | 1901–hoje / 1957–hoje | Ciência & tecnologia | Público / domínio público | ~250 | Alta |
| 13 | **Our World in Data / V-Dem** (sufrágio, abolição, direitos civis) | 1790–hoje | Sociedade & cultura | CC BY | ~150 | Média |
| 14 | **Curadoria Antiguidade & Medievo** (fontes clássicas com datas astronômicas: eclipses de Tucídides, cronologia romana, cronologia chinesa) + **Pleiades** (coordenadas) | 1000 a.C.–1500 | Múltiplas | CC BY | ~250, maioria `date_precision = year/month` | Média |
| 15 | **Pandemias e epidemias históricas** (compilações revisadas por pares; declarações OMS/PHEIC) | 430 a.C.–hoje | Saúde | Acadêmico | ~80 | Alta |
| 16 | **Brasil & América Latina** (Senado, IBGE, CPDOC — fatos públicos) | 1500–hoje | Múltiplas | Público | ~150 | Opcional |

**Excluídos por licença:** EM-DAT (restrição de redistribuição), dicionários de batalhas comerciais.

### 3.3 Esquema v3 da tabela `events`

Migração aditiva (nenhuma coluna removida; IDs existentes preservados):

```sql
ALTER TABLE events ADD COLUMN date_precision TEXT DEFAULT 'day';   -- day | month | year | decade
ALTER TABLE events ADD COLUMN calendar TEXT DEFAULT 'gregorian';     -- gregorian | julian | proleptic
ALTER TABLE events ADD COLUMN source_id TEXT;                        -- chave em sources_manifest.yml
ALTER TABLE events ADD COLUMN source_url TEXT;
ALTER TABLE events ADD COLUMN quality_tier TEXT;                     -- A primário | B dataset acadêmico | C enciclopédico auditado
ALTER TABLE events ADD COLUMN macro_category TEXT;                   -- 7 macro (ver 3.4)
ALTER TABLE events ADD COLUMN subcategory TEXT;                      -- ~25 sub
ALTER TABLE events ADD COLUMN polarity TEXT;                         -- disruptive | constructive | structural | neutral
ALTER TABLE events ADD COLUMN region TEXT;                           -- continente/região
ALTER TABLE events ADD COLUMN magnitude REAL;                        -- Mw, VEI, mortes, PIB%, etc. (normalizado por subcategoria)
ALTER TABLE events ADD COLUMN is_start INTEGER DEFAULT 1;            -- início (1) vs término/pico (0)
ALTER TABLE events ADD COLUMN external_ids TEXT;                     -- JSON {wikidata: Q..., cow: ..., usgs: ...}
ALTER TABLE events ADD COLUMN data_version TEXT;                     -- versão do catálogo que inseriu/alterou
```

Regras:
- Apenas `date_precision = 'day'` entra em qualquer cálculo diário de score; `month/year` aparecem no catálogo e em análogos com rótulo "data aproximada" e são excluídos de testes.
- Datas a.C. e julianas convertidas para JD com calendário explícito; **verificar** a convenção de ano zero no parser atual (`resolve_event_instant`) com testes dedicados (ex.: 12/09/-0490 Maratona).
- `category` (6 rótulos PT atuais) permanece para compatibilidade da UI; `macro_category` + `subcategory` tornam-se o eixo principal de filtro.

### 3.4 Taxonomia em dois níveis

| Macro (`macro_category`) | Subcategorias (`subcategory`) | Polaridades |
| :--- | :--- | :--- |
| `politics_geopolitics` | guerra interestatal, guerra civil/conflito interno, golpe, revolução/levante, independência, colapso de império/regime, eleição-marco, assassinato político | disruptive / constructive / structural |
| `economics_finance` | crash de bolsa, crise bancária, default soberano, crise cambial, hiperinflação, reforma monetária, recessão (início) | disruptive / structural |
| `health_epidemics` | pandemia (início), epidemia regional, declaração OMS, descoberta/vacina, erradicação | disruptive / constructive |
| `natural_disasters` | terremoto, erupção, tsunami, furacão/ciclone, inundação, seca/fome | disruptive |
| `science_technology` | descoberta fundamental, invenção, exploração espacial, computação/IA, medicina | constructive |
| `society_culture` | direitos civis, abolição, sufrágio, reforma educacional, marco cultural, religião | constructive / structural |
| `diplomacy_peace` | tratado de paz, tratado de desarmamento, organização internacional, reconciliação | constructive |

Mapeamento das 6 categorias atuais → macro: *Revolução & Conflito Interno* → `politics_geopolitics` (sub: golpe/revolução); *Guerra & Conflito* → `politics_geopolitics` (sub: guerra); *Desastre & Saúde Pública* → `natural_disasters` ou `health_epidemics` (split por fonte USGS vs. pandemias); *Crise Financeira* → `economics_finance`; *Ciência & Tecnologia* → `science_technology`; *Política, Tratados & Cultura* → `diplomacy_peace` ou `society_culture` (curadoria manual dos 28).

### 3.5 Pipeline de importação

1. `scripts/import_<fonte>.py` por fonte, idempotente, lendo `data/external/<fonte>/` e escrevendo `data/staging/<fonte>.json` no esquema v3.
2. `scripts/merge_catalog.py`: deduplicação por (data ± 1 dia, país, similaridade de título ≥ 0,85 — `difflib`/`rapidfuzz`) e por `external_ids`; conflitos vão para `data/exclusion_log.md` com motivo.
3. `scripts/recalculate_charts.py`: recalcula `chart_json`, `tension_index`, signos para todos os eventos (reaproveita `calculate_event_chart`), em lote com barra de progresso; ~3.000 eventos ≈ 1–2 min.
4. `scripts/audit_catalog.py`: relatório de equilíbrio (categoria, século, país, precisão, tier) → `reports/catalog_audit_v6.md`; falha se metas de §3.1 não forem atingidas.
5. `data/sources_manifest.yml` atualizado automaticamente (contagens, períodos, licenças) + `data/CHANGELOG_DATA.md` + `DATA_VERSION` (ex.: `6.0.0`).
6. `make expand-data` encadeia tudo; `make audit-data` só audita.

### 3.6 "Estimar outras categorias"

Hoje a plataforma estima 4 categorias de energia para países (Guerra, Quebra Econômica, Crise de Regime, Comoção Social) e atribui 1 categoria dominante por ano nas projeções 2027–2060. O plano amplia para **8 categorias estimáveis**, cada uma com (i) definição operacional, (ii) alvo mensal objetivo para o hindcast, (iii) mapeamento astrológico mundano explícito em config, (iv) badge de skill (BSS/AUC) na UI.

| Categoria estimada | Alvo objetivo para hindcast (Camada C) | Mapeamento mundano (config, auditável) |
| :--- | :--- | :--- |
| Guerra / conflito militar | COW onset + UCDP onset (já existe) | Marte, Plutão, Urano em tensão; eixo Áries/Libra |
| Crise econômica / financeira | NBER + R&R crises bancárias/cambiais | Júpiter, Vênus, Saturno em tensão; eixo Touro/Escorpião |
| Crise institucional / regime | Powell & Thyne + Archigos saídas irregulares | Sol, Saturno, Plutão; Capricórnio |
| Comoção social / movimentos de massa | Levantes (Brecke/UCDP não estatal) + marcos de direitos | Lua, Urano; Aquário |
| **Desastre natural** (novo) | NCEI terremotos M ≥ 7,5 + GVP VEI ≥ 5 | Marte/Urano/Plutão em signos de terra — **controle cético**: se o modelo "prevê" terremotos tão bem quanto guerras, é ruído |
| **Saúde / epidemias** (novo) | Pandemias e declarações OMS | Netuno, Quíron, Virgem/Peixes |
| **Ciência / inovação** (novo) | Nobel + lançamentos pioneiros | Urano, Mercúrio, Aquário/Gêmeos; polaridade construtiva |
| **Diplomacia / paz** (novo) | PA-X + UN Treaty + fim de guerras COW | Júpiter, Vênus, Libra/Sagitário em harmonia |

Entregáveis: `config/categories.yaml` (definições, pesos, cores, ícones), novos alvos em `src/features/targets.py`, nova rodada de `hindcast` e `forecast_v3` com os 8 alvos, `ENERGY_CATEGORIES` estendido em `energy_peaks.py`, página de projeções mostrando **probabilidades por categoria** (não só a dominante) + badge de skill + k análogos históricos por categoria.

### 3.7 Critérios de aceite da Frente A

- Metas de §3.1 atingidas e verificadas por `make audit-data`.
- `pytest` verde, incluindo `tests/regression/test_golden_baseline.py` inalterado (Track B intacto).
- `DATASET_CARD.md` v3 e `sources_manifest.yml` atualizados; todas as licenças listadas.
- Nenhum evento sem `source_id`, `date_precision`, `quality_tier`.

---

## 4. Frente B — Acurácia astronômica e metodológica

### 4.1 Efemérides completas

- Instalar `sepl_*.se1` (planetas, 0–5400 d.C.) e `seplm_*.se1` (planetas a.C.), `semom_*.se1` (Lua a.C.) a partir do repositório oficial `aloistr/swisseph` (`ephe/`, licença AGPL — compatível). Alvo mínimo: 3000 a.C.–3000 d.C.
- Adicionar `scripts/install_ephemeris.sh` + verificação de integridade (SHA-256) + teste que falha se o cálculo cair em Moshier (`swe.calc_ut` retorna flag `SEFLG_MOSEPH`).
- Teste de regressão numérica: comparar 20 posições de referência (JPL Horizons / `swetest`) com tolerância 1″ para planetas, 5″ para Lua; documentar eventuais deslocamentos no baseline (esperado ≤ 0,1″, sem efeito nos scores).
- Quíron: válido em 675–4650 d.C.; fora disso, omitir com aviso (hoje provavelmente lança warning silencioso).

### 4.2 Tempo

- **Hora legal por fuso:** substituir o corte global de 1883 pela **primeira transição do fuso IANA** (`zoneinfo` expõe transições; antes dela, LMT pela longitude). Cobre Brasil (1914), França (1891), Japão (1888), Rússia (1919/1924), etc.
- **Calendário por país:** auditar e completar `GREGORIAN_ADOPTION` (Grã-Bretanha 1752, Suécia 1753, Japão 1873, Egito 1875, China 1912, Bulgária 1916, Rússia 1918, Grécia 1923, Turquia 1926) com testes.
- **ΔT:** manter modelo embutido do Swiss Ephemeris; documentar a incerteza para datas a.C. (minutos a horas → afeta Lua e casas, não planetas lentos).
- **Ano zero / datas a.C.:** teste explícito da convenção astronômica (ano 0 = 1 a.C.) em `parse_date_to_julian_day` e no formato `-0490-09-12`.
- **Precisão declarada por carta:** cada carta exibe um selo (`Hora exata` / `Hora estimada` / `Meio-dia, sem casas` / `Data aproximada`) alimentado por `date_precision` e `is_time_known`.

### 4.3 Configuração de orbes e aspectos

- `config/score.yaml`: **congelado** (pesquisa, Track B, grade 1800–2100).
- `config/natal.yaml` (novo): orbes por planeta em trânsito, aspectos maiores + menores opcionais, sistema de casas, corpos ativos — usado pelo módulo pessoal **e** oferecido como "modo preciso" nos trânsitos de países (sem alterar o modo atual de 2,5°).
- Trânsitos de países: amostragem **mensal** (não anual) na linha de ativação, mantendo o gráfico anual como agregação; cache em `data/countries_transits_cache/`.

### 4.4 Estatística

- `docs/hipoteses_v4.md`: pré-registro dos novos alvos (§3.6), janelas, baselines (climatologia, AR), métricas (BSS, AUC, log-loss), correção FDR **conjunta** sobre os 8 alvos × famílias de features.
- Análise de **sensibilidade de orbe** (1°, 2°, 3°, 4°) e de **conjunto de aspectos** (4 vs 5 vs com menores) sobre os resultados existentes → `reports/sensibilidade_orbes_v6.md`; a UI de metodologia ganha uma seção "Robustez".
- Gráficos de calibração (reliability diagrams) por alvo na página `/forecast`.
- Teste cego de análogos: botão "embaralhar datas" no Simulador mostra análogos de uma data aleatória lado a lado (ferramenta pedagógica contra viés de confirmação).

### 4.5 Critérios de aceite da Frente B

- Flag Moshier ausente em 100% dos cálculos dentro de 3000 a.C.–3000 d.C.
- Testes de tempo/calendário cobrindo ≥ 12 países.
- `hipoteses_v4.md` com hash registrado em commit **antes** do primeiro `make hindcast` com novos alvos.
- Relatórios de sensibilidade publicados.

---

## 5. Frente C — Navegação e experiência

### 5.1 Arquitetura de informação

Nova navegação em 4 áreas (mega-menu no desktop, barra inferior de 5 ícones no mobile):

```
Explorar      Analisar          Pessoal                 Sobre
├ Início      ├ Simulador       ├ Mapa Natal            ├ Metodologia
├ Catálogo    ├ Correlações     ├ Trânsitos da Vida     ├ Dados & Fontes
├ Países      ├ Previsão        └ Progressões           ├ Glossário
└ Linha do    └ Cenários                                ├ Sobre o projeto / FAQ
  tempo                                                 └ GitHub
```

- URLs atuais preservadas; redirecionamentos 301 só se algo for renomeado.
- Breadcrumb em todas as páginas internas (`Explorar › Catálogo › Evento #812`).
- Rodapé com mapa do site e versão de dados (`DATA_VERSION`).

### 5.2 Página inicial

- Topo: uma frase em linguagem simples com o achado principal ("Testamos X eventos contra Y permutações; os ciclos planetários não superam a taxa-base") + três cartões de entrada: **Explorar a história**, **Testar uma data**, **Ver meu mapa**.
- Caixa de **busca global** (eventos, países, anos, termos do glossário) com atalho `/`.
- Painéis técnicos atuais (gráfico 1800–2100, picos, previsão) mantidos abaixo, em blocos colapsáveis com "o que este gráfico mostra".

### 5.3 Catálogo facetado

- Facetas: macro-categoria, subcategoria, polaridade, período (slider de século/década), região/país, precisão de data, tier de fonte, hora conhecida, faixa de tensão.
- Visões: lista (atual), **linha do tempo por densidade** (barras por década), **mapa** (TopoJSON Natural Earth hospedado localmente; sem tiles externos).
- Ordenação, paginação (50/página) e URL com estado de filtros.
- Página de evento: bloco "Como ler esta carta" + selo de precisão (§4.2) + fonte e licença visíveis.

### 5.4 Camada pedagógica

- `/glossario`: ~60 termos bilíngues (orbe, aspecto, trígono, Índice Cíclico de Barbault, Σcos de Oshop, percentil 1000, BSS, AUC, TOST, FDR, hindcast, walk-forward, progressão secundária, Lua progredida, retorno de Saturno…). Cada termo tem âncora; a UI usa `<abbr data-term>` com popover.
- Disclosure progressiva: resumo → "Detalhes técnicos" (collapsible) em todas as páginas analíticas.
- Cabeçalho padrão de página: título, subtítulo, "O que esta página mostra", última atualização dos dados.
- Tour guiado opcional na primeira visita (3–4 passos, dispensável, `localStorage`).

### 5.5 Internacionalização

- Migrar de correspondência de texto para **chaves** (`data-i18n="catalog.title"`), com dicionários `static/i18n/pt.json` e `en.json`.
- Render **server-side** do idioma (parâmetro `?lang=` ou cookie) via filtro Jinja `t()`; o JS só troca sem recarregar. Elimina o flash de tradução.
- Novas páginas (módulo pessoal, glossário) nascem com chaves.

### 5.6 Acessibilidade e desempenho

- Alvo Lighthouse ≥ 90 em Performance/Acessibilidade/Boas práticas nos três temas.
- Contraste AA verificado por tema; foco visível; `aria-*` em menus, abas e gráficos (tabela alternativa para cada gráfico); `prefers-reduced-motion`.
- Vendorizar Tailwind (build) e Chart.js/D3 em `static/vendor/` (sem CDN em runtime); lazy-load de gráficos abaixo da dobra; cache HTTP para JSONs pré-computados.

### 5.7 Páginas novas

- `/dados-fontes`: gerada de `sources_manifest.yml` (fonte, período, licença, contagem, link), com gráfico de cobertura por século e categoria.
- `/glossario`, `/sobre` (equipe, citação, licença, changelog).
- `/natal/*` (Frente D).

### 5.8 Critérios de aceite da Frente C

- Toda rota v5 continua respondendo 200.
- Lighthouse ≥ 90 nas 6 páginas principais, 3 temas, mobile e desktop.
- 100% dos textos de UI via chaves i18n; teste automatizado de chaves faltantes.
- Teste de usabilidade informal com 3 pessoas leigas: encontrar um evento, entender um gráfico, gerar um mapa — sem ajuda.

---

## 6. Frente D — Módulo Pessoal (resumo)

Especificação completa em [`spec_modulo_pessoal_natal_transitos.md`](spec_modulo_pessoal_natal_transitos.md). Em síntese:

- **Mapa natal** (zodíaco tropical, Placidus padrão com opções, 10 planetas + Quíron + Nodo + Lilith + asteroides opcionais, regências modernas), com roda SVG, tabelas e "como ler".
- **Trânsitos de toda a vida sobre o mapa natal** (nascimento → 100 anos), varredura **diária** vetorizada sobre grade de efemérides 1850–2150, **datas exatas** de cada passagem (incluindo passagens retrógradas), janelas de entrada/saída de orbe, aplicativo/separativo.
- **Orbes por velocidade**: Plutão/Netuno/Urano 1,0°, Saturno 1,5°, Júpiter 2,0°, Marte 3,0°, Sol/Mercúrio/Vênus 4,0°, Nodo 1,5°, Quíron 1,0°; **Lua em trânsito desconsiderada** (opção desligada por padrão). Lua natal é alvo normal; Lua progredida é eixo central das progressões.
- **Ciclos de vida** rotulados (retornos de Saturno/Júpiter/Quíron/nodal, oposição de Urano, quadratura de Netuno/Plutão).
- **8 domínios de vida** (identidade, lar/família, mente/estudos, relacionamentos, carreira, finanças, saúde/rotina, propósito/transformação) com intensidade mensal calibrada em escala 0–1000 por população sintética → mapa de calor da vida e "anos-chave".
- **Progressões secundárias**: carta progredida em qualquer data, linha do tempo da Lua progredida (signos, casas natais, fases, aspectos ao natal), ingressos do Sol/planetas progredidos, e **modo "trânsitos ao mapa progredido"** (alvos móveis).
- **Privacidade**: cálculo stateless, dados na URL (permalink), sem persistência nem logs de parâmetros; LGPD explícita.
- **Enquadramento**: módulo rotulado como leitura simbólica da astrologia moderna; sem alegação preditiva; coerente com os resultados do próprio site.

---

## 7. Infraestrutura, segurança e qualidade

| Item | Ação | Fase |
| :--- | :--- | :---: |
| Bind do serviço | `uvicorn --host 127.0.0.1`; nginx (porta 80/443) como proxy com `real_ip` da Cloudflare; bloquear 81 externamente | 0 |
| Usuário do serviço | Criar `astro` sem shell; `User=astro`, `ProtectSystem=strict`, `ReadWritePaths=/home/astro/data` | 0 |
| Rate limiting | `slowapi` ou nginx `limit_req` em `/simulator`, `/natal/*`: 30 req/min/IP; tamanho máximo de query 4 KB | 4 |
| Logs | `uvicorn --no-access-log` + nginx `log_format` sem `$args` para `/natal/*` | 4 |
| Cache | Grade de efemérides em memória (lazy, ~12–24 MB); LRU de resultados por hash de entrada (memória, TTL 10 min, sem disco) | 4 |
| Testes | 96 → ≥ 180; cobertura de `src/natal/` ≥ 90%; testes de performance com budget | 1–6 |
| CI | `ruff` + `pytest` + instalação de efemérides completas no runner (cache) | 0 |
| Versões | Unificar `pyproject.toml`, README, CITATION (`6.0.0`) | 6 |
| Docker | Imagem com efemérides completas; `docker-compose` com nginx em vez de Caddy ou manter Caddy — decidir | 6 |

---

## 8. Fases, cronograma e marcos

| Fase | Conteúdo | Duração | Marco de saída |
| :---: | :--- | :---: | :--- |
| **0. Preparação** | Efemérides completas (§4.1); `natal.yaml`/`categories.yaml` esboçados; esquema v3 desenhado; `hipoteses_v4.md` publicado; hardening do serviço (§7); snapshot de baseline de testes | 1 sem | Testes verdes com efemérides completas; serviço em loopback |
| **1. Dados** | Importadores das fontes de prioridade alta (NCEI, GVP, Brecke, R&R, Nobel/NASA, pandemias, Wikidata auditado); merge/dedup; recálculo; auditoria; DATASET_CARD v3 | 3–4 sem | ≥ 2.500 eventos; metas §3.1; Track B intacto |
| **2. Acurácia & categorias** | Fusos/calendário por país; novos alvos e hindcast com 8 categorias; energia de países estendida; sensibilidade de orbes; amostragem mensal | 2–3 sem | `/forecast` e `/projections` com 8 categorias + badges de skill |
| **3. UX & navegação** | IA nova, busca global, catálogo facetado, glossário, i18n por chaves, acessibilidade, vendorização, páginas novas | 3 sem | Lighthouse ≥ 90; teste de usabilidade aprovado |
| **4. Módulo pessoal — MVP** | Gazetteer offline, grade de efemérides, carta natal, varredura de trânsitos, ciclos, domínios + calibração, linha da vida, mapa de calor, "Agora", exportações | 4–5 sem | `/natal/transits` completo para hora conhecida e desconhecida |
| **5. Progressões** | Carta progredida, Lua progredida, ingressos, biwheel, trânsitos ao progredido | 2–3 sem | `/natal/progressions` completo |
| **6. Interpretações & release** | Biblioteca de textos PT/EN, polimento, README/README_PT/docs v6, CITATION, tag `v6.0.0` | 1–2 sem | Release publicado |

**Total:** 16–20 semanas sequenciais. Paralelismo possível: Fase 1 ∥ Fase 3; Fase 4 pode começar após a Fase 0 se a prioridade do módulo pessoal subir.

---

## 9. Riscos e mitigações

| Risco | Probabilidade | Impacto | Mitigação |
| :--- | :---: | :---: | :--- |
| Licenças de dados incompatíveis com AGPL/redistribuição (PA-X, Brecke) | Média | Médio | Verificar antes de importar; redistribuir apenas fatos datados com atribuição; manter lista de exclusões |
| Qualidade de datas da Antiguidade (calendários, ano zero) | Alta | Médio | `date_precision` + `calendar` obrigatórios; excluir de testes; testes unitários de conversão |
| Efemérides completas mudam valores de baseline | Baixa | Baixo | Diferença esperada ≤ 0,1″; atualizar golden baseline com justificativa documentada |
| Explosão de categorias sem skill → sensação de "previsão" | Média | Alto | Badge de skill obrigatório; pré-registro; FDR conjunta; controle cético (terremotos) |
| Desempenho do módulo pessoal (vida inteira, 12 corpos × 14 pontos × 5 aspectos) | Média | Alto | Grade pré-computada + numpy; refinamento só nos hits; budget < 1,5 s testado em CI |
| Dados de nascimento (LGPD) | Baixa | Alto | Stateless, sem logs de parâmetros, sem persistência, aviso claro, rate limit |
| Escopo das interpretações (centenas de textos) | Alta | Médio | Composição por templates (arquétipo × aspecto × ponto) + ~60 textos manuais prioritários; restante em v6.1 |
| Regressão de UX ao reorganizar navegação | Média | Médio | Preservar URLs; testes de rotas; feature flag `NAV_V6` para alternar durante o desenvolvimento |
| Hora de nascimento desconhecida gera falsa precisão | Alta | Médio | Modo explícito "sem hora": sem ângulos/casas, Lua com faixa, textos ajustados |

---

## 10. Decisões assumidas neste plano (revisáveis)

1. Ordem: fundamentos (A, B, C) antes do módulo pessoal (D), como solicitado — com paralelismo opcional.
2. Track B e `score.yaml` permanecem congelados; novos testes só via pré-registro v4.
3. Taxonomia em dois níveis (7 macro + ~25 sub) com polaridade; os 6 rótulos atuais ficam como campo legado.
4. Orbes padrão do módulo pessoal: lentos 1,0°–1,5°, Júpiter 2,0°, Marte 3,0°, Sol/Mercúrio/Vênus 4,0°; Lua em trânsito desligada por padrão.
5. Placidus como sistema padrão; Koch, Signos Inteiros, Igual e Porphyry como opções.
6. Progressões secundárias com "1 dia = 1 ano trópico" (365,24219 d); MC progredido por arco solar (Naibod opcional).
7. Nodo verdadeiro na carta natal; **Nodo médio** como corpo em trânsito (evita falsos hits pela oscilação do nodo verdadeiro).
8. Módulo pessoal stateless e server-rendered; sem conta de usuário, sem banco.
9. Geocodificação offline com GeoNames (`cities15000`, CC BY) + `timezonefinder`.
10. 8 domínios de vida fixos em config; calibração 0–1000 por população sintética (coerente com o percentil 1000 do site).

---

## 11. Perguntas abertas (não bloqueiam o início da Fase 0)

1. **Acesso público ao módulo pessoal:** aberto a qualquer visitante (com rate limit) ou protegido por token/senha simples enquanto estiver em beta?
2. **Aspectos em trânsito:** apenas os 5 maiores, ou incluir menores (quincúncio 150°, semiquadratura 45°, sesquiquadratura 135°) com metade da orbe, desligados por padrão?
3. **Prioridade temporal dos dados:** densificar 1500–1900 (mais fontes, melhor datação) antes de investir na Antiguidade?
4. **Tom das interpretações:** psicológico/reflexivo (Greene, Sasportas) ou mais descritivo/evento (Hand)? Define o estilo dos ~60 textos manuais.
5. **Vênus a 4°:** manter como os demais rápidos ou reduzir para 3°?
6. **Progressões de ângulos:** arco solar (padrão proposto) vs. Naibod em ascensão reta — qual deve ser o padrão?
7. **Eclipses sobre pontos natais e retornos solares/lunares completos:** entram em v6.0 ou v6.1?
8. **Docker:** manter Caddy do compose ou alinhar com o nginx do servidor?

---

## 12. Checklist de aceite da v6.0.0

- [ ] Efemérides completas instaladas; nenhum cálculo via Moshier no intervalo 3000 a.C.–3000 d.C.
- [ ] Catálogo ≥ 2.500 eventos, metas de §3.1, `make audit-data` verde.
- [ ] Track B (`events_v2`, golden baseline) byte-a-byte inalterado.
- [ ] 8 categorias estimadas com badge de skill; `hipoteses_v4.md` pré-registrado.
- [ ] Nav em 4 áreas, busca global, catálogo facetado, glossário, `/dados-fontes`.
- [ ] i18n por chaves em 100% da UI; Lighthouse ≥ 90.
- [ ] `/natal/chart`, `/natal/transits`, `/natal/progressions` funcionais, < 1,5 s por vida inteira, exportações CSV/ICS/JSON.
- [ ] Serviço em loopback, usuário dedicado, rate limit, logs sem parâmetros.
- [ ] ≥ 180 testes verdes; versões unificadas em `6.0.0`; README/README_PT/CITATION atualizados.
