"""
Forecast probabilístico v3 (2026–2060).

Para cada alvo histórico objetivo:
1. Escolhe o melhor modelo astrológico do hindcast (reports/hindcast_v3.json) e registra o skill
   medido fora da amostra (BSS, IC 95%). Se o skill não é positivo, a estimativa recomendada é a
   taxa-base e a interface diz isso.
2. Ajusta o modelo em toda a cobertura histórica e prevê p(evento) por mês até 2060, com intervalo
   (p10–p90) por bootstrap em blocos anuais.
3. Lista os drivers (features com maior contribuição no mês de pico de cada ano) e o calendário
   astronômico exato do ano (aspectos entre planetas lentos, ingressos, eclipses).
4. Busca análogos históricos corrigidos: distância contínua no espaço de fases dos ciclos externos,
   um análogo por bloco de 10 anos, com lift contra a taxa-base (em vez de voto por "mesmo signo").

Saída: data/forecast_v3.json (consumido por /forecast e /api/forecast).
"""

import json
import os
import sqlite3
import sys
from datetime import date, datetime
from typing import Dict, Any, List, Optional

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.features.astro_features import monthly_features
from src.features.targets import monthly_targets
from src.features.astro_events import outer_cycle_calendar, ingresses, eclipses, PT_NAMES, ASPECT_SYMBOL
from src.analysis.hindcast import feature_sets, _fit_predict, EPS, REPORT_JSON as HINDCAST_JSON

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT = os.path.join(ROOT, "data", "forecast_v3.json")
CALENDAR_CACHE = os.path.join(ROOT, "data", "astro_calendar_2026_2060.json")
DB_PATH = os.path.join(ROOT, "db", "history_astrology.db")

FORECAST_TARGETS = {
    "cow_war_onset": "Início de guerra interestatal (COW, 1816–2007)",
    "ucdp_onset_any": "Início de episódio de conflito armado (UCDP/PRIO, 1946–2023)",
    "nber_recession": "Mês em recessão nos EUA (NBER, 1857–2024)",
    "nber_recession_start": "Início de recessão nos EUA (NBER, 1857–2024)",
    "v2_any": "Evento do catálogo objetivo v2 (1800–2025)",
}
ASTRO_MODELS = ["legacy_index", "barbault", "tarnas_outer", "outer_phases", "astro_full"]
FUTURE_START, FUTURE_END = 2026, 2060
N_BOOT = 60


# ----------------------------------------------------------------------------- rótulos
def feature_label(name: str) -> str:
    base = name[:-4] if name.endswith("_max") else name
    suffix = " (pico mensal)" if name.endswith("_max") else ""
    parts = base.split("_")
    def pn(b): return PT_NAMES.get(b, b)
    if base.startswith(("phase_sin2", "phase_cos2")):
        return f"Fase (2º harmônico) do ciclo {pn(parts[2])}–{pn(parts[3])}" + suffix
    if base.startswith(("phase_sin", "phase_cos")):
        return f"Fase do ciclo {pn(parts[2])}–{pn(parts[3])}" + suffix
    if base.startswith(("hphase_sin", "hphase_cos")):
        return f"Fase heliocêntrica {pn(parts[2])}–{pn(parts[3])}" + suffix
    if base.startswith("sep_"):
        return f"Separação angular {pn(parts[1])}–{pn(parts[2])}" + suffix
    if base.startswith("asp_"):
        return f"{pn(parts[1])} {ASPECT_SYMBOL[int(parts[3])]} {pn(parts[2])} (ativação)" + suffix
    if base.startswith("mp_"):
        return f"Meio-ponto {pn(parts[1])}/{pn(parts[2])} ativado por {pn(parts[3])}" + suffix
    table = {
        "barbault_index": "Índice Cíclico de Barbault", "barbault_index_helio": "Índice Cíclico de Barbault (heliocêntrico)",
        "hard_outer_total": "Aspectos duros entre planetas externos", "hard_all_total": "Aspectos duros (todos os corpos)",
        "soft_all_total": "Aspectos harmônicos (todos os corpos)", "conj_outer_total": "Conjunções entre planetas externos",
        "harm4_outer": "Harmônico 4 (externos)", "harm8_outer": "Harmônico 8 (externos)",
        "harm4_all": "Harmônico 4 (todos)", "harm8_all": "Harmônico 8 (todos)",
        "tension_raw_legacy": "Índice de tensão legado (score.yaml)",
        "days_to_solar_eclipse": "Dias até eclipse solar", "days_to_lunar_eclipse": "Dias até eclipse lunar",
        "solar_eclipse_window15": "Janela de eclipse solar (±15 dias)", "lunar_eclipse_window15": "Janela de eclipse lunar (±15 dias)",
    }
    if base in table:
        return table[base] + suffix
    if parts[0] in ("dec", "oob", "retro", "station", "ingress", "cardinal"):
        kind = {"dec": "Declinação de", "oob": "Fora-de-limites:", "retro": "Retrogradação de", "station": "Estação de", "ingress": "Ingresso de", "cardinal": "Signo cardinal:"}[parts[0]]
        return f"{kind} {pn(parts[1])}" + suffix
    if parts[0] == "sign":
        return f"Posição zodiacal de {pn(parts[2])}" + suffix
    return name


# ----------------------------------------------------------------------------- calendário
def build_calendar(force: bool = False) -> Dict[str, Any]:
    if os.path.exists(CALENDAR_CACHE) and not force:
        with open(CALENDAR_CACHE, "r", encoding="utf-8") as f:
            return json.load(f)
    start, end = date(FUTURE_START, 1, 1), date(FUTURE_END, 12, 31)
    aspects = outer_cycle_calendar(start, end)
    ing = []
    for b in ("jupiter", "saturn", "uranus", "neptune", "pluto"):
        ing.extend(ingresses(b, start, end, step_days=2.0))
    ecl = eclipses(start, end)
    cal: Dict[str, Any] = {str(y): {"aspects": [], "ingresses": [], "eclipses": []} for y in range(FUTURE_START, FUTURE_END + 1)}
    for a in aspects:
        cal[a["date"][:4]]["aspects"].append(a)
    for i in ing:
        cal[i["date"][:4]]["ingresses"].append(i)
    for e in ecl:
        cal[e["date"][:4]]["eclipses"].append(e)
    with open(CALENDAR_CACHE, "w", encoding="utf-8") as f:
        json.dump(cal, f, ensure_ascii=False, indent=1)
    return cal


# ----------------------------------------------------------------------------- análogos
def _catalog_events_by_month() -> Dict[int, List[Dict[str, Any]]]:
    out: Dict[int, List[Dict[str, Any]]] = {}
    if not os.path.exists(DB_PATH):
        return out
    conn = sqlite3.connect(DB_PATH)
    for eid, title, cat, d in conn.execute("SELECT id, title, category, date FROM events WHERE date >= '1800-01-01'"):
        try:
            k = int(d[:4]) * 12 + int(d[5:7]) - 1
        except ValueError:
            continue
        out.setdefault(k, []).append({"id": eid, "title": title, "category": cat, "date": d})
    conn.close()
    return out


def analogs_for_month(z_target: np.ndarray, Z_hist: np.ndarray, hist_keys: np.ndarray, hist_y: np.ndarray, base_rate: float, catalog: Dict[int, List[Dict[str, Any]]], k: int = 8) -> Dict[str, Any]:
    """Vizinhos mais próximos no espaço de fases dos ciclos externos, um por bloco de 10 anos."""
    d = np.sqrt(((Z_hist - z_target) ** 2).sum(axis=1))
    order = np.argsort(d)
    chosen, blocks = [], set()
    for i in order:
        blk = int(hist_keys[i] // 12) // 10
        if blk in blocks:
            continue
        blocks.add(blk)
        chosen.append(i)
        if len(chosen) >= k:
            break
    chosen = np.array(chosen)
    # lift: fração de análogos com evento objetivo em ±6 meses vs taxa-base equivalente
    hits = 0
    items = []
    for i in chosen:
        win = slice(max(0, i - 6), min(len(hist_y), i + 7))
        hit = bool(hist_y[win].max() > 0)
        hits += hit
        key = int(hist_keys[i])
        evs = []
        for kk in range(key - 6, key + 7):
            evs.extend(catalog.get(kk, []))
        items.append({"month": f"{key // 12:04d}-{key % 12 + 1:02d}", "distance": round(float(d[i]), 3), "objective_event_within_6m": hit, "catalog_events": evs[:4]})
    base_window = 1.0 - (1.0 - base_rate) ** 13
    rate = hits / max(1, len(chosen))
    return {"analogs": items, "hit_rate_6m": round(rate, 3), "expected_rate_6m": round(float(base_window), 3), "lift": round(rate / base_window, 2) if base_window > 0 else None}


# ----------------------------------------------------------------------------- forecast
def _skill_from_hindcast(hc: Dict[str, Any], tname: str) -> Dict[str, Any]:
    t = hc.get("targets", {}).get(tname)
    if not t:
        return {"model": "outer_phases", "bss": None, "bss_ci95": None, "p_gt0": None, "verdict": "não medido"}
    best = max(ASTRO_MODELS, key=lambda m: t["models"].get(m, {}).get("bss", -9))
    m = t["models"][best]
    # Veredito conservador: IC do BSS inteiramente > 0 E discriminação real (AUC > 0.55).
    # Com 7 alvos x 5 modelos (35 comparações), um IC marginal isolado é esperado ao acaso.
    n_comparisons = len(hc.get("targets", {})) * len(ASTRO_MODELS)
    auc_ok = (m.get("auc") or 0.0) > 0.55
    if m["bss_ci95"][0] > 0 and auc_ok:
        verdict = "skill positivo"
    elif m["bss_ci95"][0] > 0:
        verdict = "BSS>0 sem discriminação (AUC≤0.55) — provável artefato de calibração/multiplicidade"
    elif m["bss"] <= 0:
        verdict = "sem skill demonstrado"
    else:
        verdict = "skill não significativo"
    return {"model": best, "bss": m["bss"], "bss_ci95": m["bss_ci95"], "p_gt0": m["bss_p_gt0"], "auc": m["auc"], "verdict": verdict,
            "n_comparisons": n_comparisons,
            "ar_baseline_bss": t["models"].get("ar_baseline", {}).get("bss"), "test_years": t["test_years"]}


def run_forecast(verbose: bool = True) -> Dict[str, Any]:
    rng = np.random.default_rng(42)
    mf = monthly_features()
    T = monthly_targets()
    names = mf["names"]
    fsets = feature_sets(names)
    X = mf["X"].astype(np.float64)
    months = mf["months"]
    mkey = months[:, 0].astype(np.int64) * 12 + months[:, 1] - 1
    hc = {}
    if os.path.exists(HINDCAST_JSON):
        with open(HINDCAST_JSON, "r", encoding="utf-8") as f:
            hc = json.load(f)

    future = (months[:, 0] >= FUTURE_START) & (months[:, 0] <= FUTURE_END)
    hist_mask_all = (months[:, 0] >= 1800) & (months[:, 0] <= 2025)
    phase_cols = fsets["outer_phases"]
    Zsc = StandardScaler().fit(X[hist_mask_all][:, phase_cols])
    Z_hist = Zsc.transform(X[hist_mask_all][:, phase_cols])
    Z_fut = Zsc.transform(X[future][:, phase_cols])
    hist_keys = mkey[hist_mask_all]
    catalog = _catalog_events_by_month()
    calendar = build_calendar()

    out: Dict[str, Any] = {
        "generated_at": datetime.utcnow().isoformat() + "Z", "horizon": [FUTURE_START, FUTURE_END], "n_bootstrap": N_BOOT,
        "method": "Logística L2 sobre features astrológicas mensais; intervalo p10–p90 por bootstrap em blocos anuais; "
                  "skill medido por hindcast walk-forward (reports/hindcast_v3.md).",
        "targets": {}, "calendar": calendar, "analogs": {},
    }

    # análogos (independentes do alvo): por ano, usa o mês de janeiro... melhor: mês central (julho)
    v2 = (T.targets["v2_any"][np.searchsorted(T.keys, hist_keys)] > 0).astype(float)
    base_v2 = float(v2.mean())
    fut_months = months[future]
    for y in range(FUTURE_START, FUTURE_END + 1):
        j = np.where((fut_months[:, 0] == y) & (fut_months[:, 1] == 7))[0][0]
        out["analogs"][str(y)] = analogs_for_month(Z_fut[j], Z_hist, hist_keys, v2, base_v2, catalog)

    for tname, label in FORECAST_TARGETS.items():
        if tname not in T.targets:
            continue
        skill = _skill_from_hindcast(hc, tname)
        cols = fsets[skill["model"]]
        cov = T.mask(tname)
        ti = np.searchsorted(T.keys, mkey)
        y = (T.targets[tname][ti] > 0).astype(float)
        train = cov[ti]
        Xtr, ytr = X[train][:, cols], y[train]
        Xf = X[future][:, cols]
        base = float(ytr.mean())
        p = _fit_predict(Xtr, ytr, Xf, None)
        # bootstrap em blocos anuais
        yrs = months[train][:, 0]
        uyrs = np.unique(yrs)
        boots = np.empty((N_BOOT, len(Xf)))
        for b in range(N_BOOT):
            pick = rng.choice(uyrs, size=len(uyrs), replace=True)
            idx = np.concatenate([np.where(yrs == yy)[0] for yy in pick])
            boots[b] = _fit_predict(Xtr[idx], ytr[idx], Xf, None)
        lo, hi = np.percentile(boots, [10, 90], axis=0)
        # drivers: contribuição linear no modelo final
        sc = StandardScaler().fit(Xtr)
        clf = LogisticRegression(C=0.01, max_iter=2000).fit(sc.transform(Xtr), ytr)
        contrib = sc.transform(Xf) * clf.coef_[0]
        years_out = []
        for yy in range(FUTURE_START, FUTURE_END + 1):
            m = fut_months[:, 0] == yy
            pm = p[m]
            peak = int(np.argmax(pm))
            row_idx = np.where(m)[0][peak]
            top = np.argsort(-contrib[row_idx])[:4]
            years_out.append({
                "year": yy, "p_mean": round(float(pm.mean()), 4), "p_lo": round(float(lo[m].mean()), 4), "p_hi": round(float(hi[m].mean()), 4),
                "p_peak_month": int(fut_months[m][peak][1]), "p_peak": round(float(pm.max()), 4),
                "ratio_to_base": round(float(pm.mean() / base), 2) if base > 0 else None,
                "monthly": [round(float(v), 4) for v in pm],
                "drivers": [{"feature": names[cols[t]], "label": feature_label(names[cols[t]]), "contribution": round(float(contrib[row_idx, t]), 3)} for t in top if contrib[row_idx, t] > 0],
            })
        out["targets"][tname] = {"label": label, "base_rate": round(base, 4), "coverage": list(T.coverage[tname]), "n_train_months": int(train.sum()),
                                 "positives": int(ytr.sum()), "model": skill["model"], "skill": skill, "years": years_out}
        if verbose:
            top_years = sorted(years_out, key=lambda r: -r["p_mean"])[:3]
            print(f"[{tname}] modelo={skill['model']} BSS={skill['bss']} ({skill['verdict']}) taxa-base={base:.3f} | picos: " + ", ".join(f"{r['year']}={r['p_mean']:.3f}" for r in top_years))

    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    return out


def load_forecast() -> Optional[Dict[str, Any]]:
    if not os.path.exists(OUTPUT):
        return None
    with open(OUTPUT, "r", encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    run_forecast()
    print(f"Forecast salvo em {OUTPUT}")
