# Pré-registro v4 — Novos alvos preditivos e categorias estimáveis (AstroHistory v6)

**Data de registro:** 06/11/2026 (antes de qualquer execução de `make hindcast` com os alvos abaixo)
**Status:** congelado ao ser commitado nesta branch; alterações posteriores exigem nova versão (v4.1…).
**Antecedentes:** `docs/hipoteses.md` (v2, N1–N3) e `docs/hipoteses_v3.md` (hindcast walk-forward).

## 1. Pergunta

> Os índices astrológicos mundanos (tensão de aspectos, Índice Cíclico de Barbault, Σcos de Oshop, fases dos ciclos externos)
> têm skill preditivo fora da amostra para **novas classes de eventos** — desastres naturais, epidemias, marcos científicos,
> tratados de paz e crises bancárias — além das classes já testadas (guerra, recessão, golpe)?

Expectativa declarada **a priori** (coerente com v2/v3): **nenhum alvo** terá BSS significativamente > 0 contra a climatologia
após correção FDR conjunta. Em particular, o alvo de **terremotos** funciona como **controle cético**: qualquer "skill" ali
indica artefato do método, não efeito astrológico.

## 2. Alvos mensais (Camada C — séries objetivas)

| Alvo | Definição operacional (mês = 1 se…) | Fonte | Cobertura |
|---|---|---|---|
| `ncei_quake_m75` | ≥ 1 terremoto M ≥ 7,5 com data diária | NOAA NCEI | 1850–2024 |
| `gvp_eruption_vei5` | ≥ 1 erupção VEI ≥ 5 com data diária/mensal | Smithsonian GVP | 1800–2024 |
| `pandemic_onset` | início de pandemia/epidemia ou declaração OMS (`health_epidemics`, precisão dia) | catálogo v3 (curado + Wikidata) | 1850–2024 |
| `science_milestone` | ≥ 1 marco de `science_technology` (precisão dia) | catálogo v3 (curado) | 1850–2024 |
| `peace_treaty` | ≥ 1 tratado/acordo de `diplomacy_peace` (precisão dia) | catálogo v3 (curado + Wikidata + UNTC) | 1850–2024 |
| `rr_banking_crisis_onset` | início de crise bancária/cambial/default (`economics_finance`, sub ∈ {banking_crisis, currency_crisis, sovereign_default, stock_crash}) | catálogo v3 (curado) | 1850–2024 |
| `cow_war_end` | término de guerra interestatal | COW v4 | 1816–2007 |

Alvos legados mantidos: `v2_any`, `cow_war_onset`, `cow_war_ongoing`, `nber_recession`, `nber_recession_start`, `ucdp_onset_any`.

## 3. Features e modelos

Idênticos ao v3 (`src/features/astro_features.py`, `src/analysis/hindcast.py`): climatologia, AR(12) baseline,
`legacy_index`, `barbault`, `tarnas_outer`, `outer_phases`, `astro_full`, `ar_plus_astro`. Regularização e janela de teste (≥ 1951,
gap 12 meses) inalteradas. Nenhum ajuste de hiperparâmetro por alvo.

## 4. Métricas e decisão

- BSS vs. climatologia (IC 95% bootstrap em blocos anuais), AUC, log-loss.
- **Critério de skill:** BSS > 0 com IC 95% inteiramente acima de 0 **e** q < 0,05 após FDR (Benjamini-Hochberg) sobre a família
  {alvos novos × conjuntos de features astrológicas} (7 × 5 = 35 testes).
- **Controle cético:** se `ncei_quake_m75` ou `gvp_eruption_vei5` passarem o critério, o resultado de qualquer outro alvo é
  rotulado como *não interpretável* até revisão metodológica.
- Robustez: reexecução com orbes 1°, 2°, 4° (além dos 3° padrão) para `astro_full`; resultados em `reports/sensibilidade_orbes_v6.md`.

## 5. Vazamentos e exclusões

- Alvos derivados do catálogo v3 excluem eventos com `date_precision != 'day'`.
- Eventos do catálogo usados nos alvos **não** entram em nenhuma feature.
- A amostra `events_v2` (Track B) permanece intocada.

## 6. Uso na interface

Cada categoria estimada em `/forecast` e `/projections` exibe o **badge de skill** (BSS, IC, veredito) do alvo correspondente
(`config/categories.yaml → hindcast_targets`). Categorias sem alvo testado exibem "não testado".
