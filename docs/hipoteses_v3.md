# Pré-registro v3 — Previsão probabilística com astrologia mundana moderna

**Objetivo:** melhorar a *precisão* da estimativa do futuro, onde precisão significa **skill medido fora da amostra** (regras de pontuação próprias) e **incerteza calibrada**, não um índice mais elaborado.

## 1. O que muda em relação ao v2

| Dimensão | v2 (Marco M2) | v3 |
|---|---|---|
| Alvo | 59 eventos pontuais (catálogo v2) | Séries **mensais** de bases objetivas: COW Guerras Interestatais v4 (1816–2007), NBER (1857–2024), UCDP/PRIO v24.1 (1946–2023), catálogo v2 (1800–2025) |
| Sinal | 1 índice manual (9 corpos, orbe 3°) | 409 features: fases sinódicas (seno/cosseno) dos 10 pares externos, Índice Cíclico de Barbault (geo/helio), ativação de aspectos com kernel gaussiano, harmônicos 4/8, declinação e fora-de-limites, retrogradação/estações/ingressos, meios-pontos, proximidade a eclipses, índice legado |
| Modelo | Comparação de médias (z) | Logística L2 com regularização escolhida por validação temporal interna; baselines obrigatórios (climatologia e autorregressivo) |
| Validação | Modelos nulos N1–N3 sobre o índice | **Hindcast walk-forward** a partir de 1951 com gap de 12 meses; BSS contra climatologia com IC por bootstrap em blocos anuais; AUC; log-loss; curva de confiabilidade |
| Saída | Percentil anual e cor de alerta | p(evento) mensal e anual com intervalo p10–p90, razão contra a taxa-base, drivers com datas exatas, análogos com lift, **selo de skill** |
| Cálculo | Fuso = round(lon/15); duas fórmulas de score | Fuso IANA histórico / LMT exata; função de score única (`config/score.yaml`) com teste de paridade |

## 2. Hipóteses pré-registradas (v3)

- **H5 (skill):** ao menos um modelo astrológico (`legacy_index`, `barbault`, `tarnas_outer`, `outer_phases`, `astro_full`) obtém BSS > 0 com IC 95% inteiramente positivo em ao menos um alvo objetivo, no hindcast walk-forward.
- **H6 (incremento sobre o passado recente):** `ar_plus_astro` supera `ar_baseline` em BSS com IC positivo para a diferença, em ao menos um alvo.
- **H7 (orbe larga de Tarnas):** as features de fase (sem orbe) e as ativações gaussianas com σ = 4–5° para pares externos não revertem o resultado nulo do v2 obtido com orbe de 3°.

## 3. Regras de decisão

- A curva do modelo só é apresentada como "previsão" quando H5 vale para aquele alvo; caso contrário a interface marca "sem skill demonstrado" e recomenda a taxa-base.
- Nenhuma feature, peso ou método entra no forecast sem melhorar o BSS no hindcast.
- **Holdout congelado:** 2010–2025 não é usado para escolher features ou hiperparâmetros fora do laço walk-forward (que, por construção, só vê o passado de cada ano).

## 4. Resultado da primeira execução

Ver `reports/hindcast_v3.md` (gerado por `make hindcast`). Resumo:

- Nenhum modelo astrológico supera a climatologia com IC positivo **e** discriminação real (AUC > 0,55) em nenhum alvo.
- O único IC marginalmente positivo (`outer_phases` em `nber_recession`: BSS +0,127, IC [0,003; 0,247]) vem acompanhado de AUC 0,40 — o ganho de Brier é efeito de calibração/variância, não de discriminação — e, com 35 comparações (7 alvos × 5 modelos), um IC desse tipo é esperado ao acaso. É tratado como **não confirmado**.
- O baseline autorregressivo domina nos alvos persistentes (recessão em curso BSS +0,85; guerra em curso +0,83), e a astrologia não acrescenta a ele (`ar_plus_astro` ≤ `ar_baseline`).
- H5 e H6 **não confirmadas**; H7 confirmada (o nulo do v2 se mantém com fases contínuas e orbes largas).

## 5. Reprodução

```bash
make features   # grade diária 1750–2150 (≈20 s)
make hindcast   # walk-forward, todos os alvos (≈20–30 min)
make forecast   # data/forecast_v3.json (2026–2060)
make timeline   # caches da UI com o pico diário real do ano
```
