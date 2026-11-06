# Changelog dos dados

## 6.0.0 — 2026-11-06

**Catálogo (Track A):** 1.342 → **3.406 eventos**. Track B (`events_v2`, N=59–61) inalterado.

- **Esquema v3** (aditivo): `date_precision`, `calendar`, `source_id`, `source_url`, `quality_tier`, `macro_category`,
  `subcategory`, `polarity`, `region`, `magnitude`, `is_start`, `external_ids`, `data_version`.
- **Correções:** 7 eventos a.C. gravados como d.C. (Maratona, Termópilas, Gaugamela, Alexandre, Canas, Cartago, Idos de Março)
  recebem datas `-YYYY-MM-DD`; convenção documentada em `src/core/dates.py` (490 a.C. → ano astronômico −489).
  3 duplicatas removidas (#301→#1, #303→#4, #305→#6).
- **Recálculo integral das cartas** com: arquivos Swiss Ephemeris completos (sem Moshier), casas **Placidus** reais
  (bug `houses_ex2` corrigido — antes todas as cartas caíam em Porphyry) e hora legal histórica por zona IANA
  (hora média local antes da 1ª transição de cada zona).
- **Novas fontes:**
  - NOAA NCEI Significant Earthquakes M ≥ 7,5 — 944 eventos (domínio público) — *controle cético*.
  - Smithsonian GVP erupções VEI ≥ 5 — 150 eventos (citação).
  - Wikidata (CC0) — 682 eventos com ≥ 25 sitelinks e coordenadas (batalhas, tratados, epidemias, massacres…), tier C.
  - Curadoria v6 — 291 eventos (Antiguidade/Medievo, ciência, saúde, diplomacia, sociedade, economia, Brasil/América Latina).
- **Cobertura:** 710 eventos antes de 1800 (era 73), 165 a.C. (era 4); país mais frequente 7,8%.
- **Metas não atingidas** (ver `reports/catalog_audit_v6.md`): polaridade construtiva 417/500; macro-categoria máxima 42,7% (> 35%)
  pela inclusão integral do NCEI como controle cético.
- Exclusões registradas em `data/exclusion_log.md` (159 duplicatas/incompletos).

**Novos arquivos:** `data/ephemeris/natal_grid_1850_2150.npz` (grade do módulo pessoal), `data/gazetteer/cities.sqlite`
(GeoNames CC BY 4.0, 34.204 cidades), `data/calibration/natal_domains_reference.json` (300 nascimentos sintéticos),
`data/interpretations/{pt,en}.yaml`, `data/glossary.yaml`, `data/curated/*.json`.

## 5.0.0 — 2026-11-02
Catálogo expandido para 1.342 eventos (COW, UCDP, Powell & Thyne, USGS, NBER, marcos curados). Ver `DATASET_CARD.md`.
