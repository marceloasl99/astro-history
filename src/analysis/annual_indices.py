"""
Índices anuais (0–1000) derivados da grade de features e sua correlação com a história.

Séries (percentil da média anual na janela 1800–2100):
- conflict_1000   : "Risco Bélico"  — ativação média de aspectos duros (90°/180°) entre planetas externos
- innovation_1000 : "Inovação"      — ativação média de aspectos harmônicos (60°/120°) entre todos os corpos
- barbault_1000   : "Concentração Planetária (Barbault)" — nova categoria: 1800° menos o Índice Cíclico de Barbault
                    (quanto maior, mais concentrados os 5 externos; Barbault associou mínimos do índice a crises coletivas)

Correlação com a história: para cada categoria do catálogo (e para o catálogo objetivo v2) compara-se a média do
índice nos anos com evento contra o nulo N3 (deslocamento circular dos anos, 10.000 permutações), que preserva o
agrupamento temporal dos eventos e a autocorrelação dos planetas lentos. Reporta z, p bicaudal e lift do quartil superior.
Saída: data/annual_indices.json
"""

import json
import os
import sqlite3
import sys
from collections import defaultdict
from typing import Dict, Any, List

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.features.astro_features import load_raw_grid, derive_daily_features
from src.analysis.multiplicity import benjamini_hochberg

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUTPUT = os.path.join(ROOT, "data", "annual_indices.json")
DB_PATH = os.path.join(ROOT, "db", "history_astrology.db")
YEAR_START, YEAR_END = 1800, 2100

SERIES = {
    "conflict_1000": {"label": "Risco Bélico", "feature": "hard_outer_total", "invert": False,
                      "description": "Ativação média anual de quadraturas e oposições entre Júpiter, Saturno, Urano, Netuno e Plutão (kernel gaussiano)."},
    "innovation_1000": {"label": "Inovação Científica", "feature": "soft_all_total", "invert": False,
                        "description": "Ativação média anual de trígonos e sextis entre os 9 corpos."},
    "barbault_1000": {"label": "Concentração Planetária (Barbault)", "feature": "barbault_index", "invert": True,
                      "description": "1800° − Índice Cíclico de Barbault (soma das 10 separações entre os externos). Alto = planetas lentos concentrados."},
}

_CACHE = None


def compute_annual_series() -> Dict[str, Any]:
    g = load_raw_grid()
    X, names = derive_daily_features(g)
    col = {n: i for i, n in enumerate(names)}
    years_all = g["ymd"][:, 0].astype(int)
    years = np.arange(YEAR_START, YEAR_END + 1)
    out = {"years": years.tolist(), "series": {}}
    for key, spec in SERIES.items():
        daily = X[:, col[spec["feature"]]].astype(np.float64)
        if spec["invert"]:
            daily = 1800.0 - daily
        annual = np.array([daily[years_all == y].mean() for y in years])
        ranks = np.argsort(np.argsort(annual))
        pct = np.round((ranks + 1) / len(annual) * 1000.0, 1)
        out["series"][key] = {"label": spec["label"], "description": spec["description"],
                              "raw": np.round(annual, 3).tolist(), "percentile_1000": pct.tolist()}
    return out


def _events_by_year() -> Dict[str, List[int]]:
    groups: Dict[str, List[int]] = defaultdict(list)
    if not os.path.exists(DB_PATH):
        return groups
    conn = sqlite3.connect(DB_PATH)
    for cat, d in conn.execute("SELECT category, date FROM events WHERE date >= '1800-01-01' AND date <= '2025-12-31'"):
        groups[cat].append(int(d[:4]))
        groups["Todos os 300 marcos"].append(int(d[:4]))
    try:
        for d, in conn.execute("SELECT event_date FROM events_v2 WHERE date_precision='day' AND event_date BETWEEN '1800-01-01' AND '2025-12-31'"):
            groups["Catálogo objetivo v2 (N=59)"].append(int(d[:4]))
    except Exception:
        pass
    conn.close()
    return groups


def circular_shift_years(series: np.ndarray, years: np.ndarray, event_years: List[int], n_perm: int = 10000, seed: int = 42) -> Dict[str, Any]:
    rng = np.random.default_rng(seed)
    hist = (years >= 1800) & (years <= 2025)
    s, yrs = series[hist], years[hist]
    idx = np.array(sorted({int(np.where(yrs == y)[0][0]) for y in event_years if y in set(yrs.tolist())}))
    if len(idx) < 3:
        return {}
    obs = float(s[idx].mean())
    n = len(s)
    shifts = rng.integers(1, n, size=n_perm)
    null = np.array([s[(idx + k) % n].mean() for k in shifts])
    z = (obs - null.mean()) / (null.std(ddof=1) or 1.0)
    p = float((1 + np.sum(np.abs(null - null.mean()) >= abs(obs - null.mean()))) / (n_perm + 1))
    q75 = np.percentile(s, 75)
    lift = float(np.mean(s[idx] >= q75) / 0.25)
    return {"n_event_years": int(len(idx)), "observed_mean": round(obs, 1), "null_mean": round(float(null.mean()), 1),
            "null_sd": round(float(null.std(ddof=1)), 1), "z": round(float(z), 3), "p_two_sided": round(p, 4),
            "top_quartile_lift": round(lift, 2)}


def compute_history_correlations(annual: Dict[str, Any]) -> Dict[str, Any]:
    years = np.array(annual["years"])
    groups = _events_by_year()
    out: Dict[str, Any] = {}
    for key, ser in annual["series"].items():
        s = np.array(ser["percentile_1000"])
        out[key] = {cat: circular_shift_years(s, years, yrs) for cat, yrs in sorted(groups.items())}
    # Controle de múltiplas comparações (BH) sobre toda a família de testes
    cells = [(k, c) for k, d in out.items() for c, r in d.items() if r]
    _, q = benjamini_hochberg([out[k][c]["p_two_sided"] for k, c in cells], q=0.05)
    for (k, c), qv in zip(cells, q):
        out[k][c]["q_fdr"] = round(float(qv), 4)
        out[k][c]["significant_q05"] = bool(qv < 0.05)
    return out


def build(force: bool = False) -> Dict[str, Any]:
    global _CACHE
    if _CACHE is not None and not force:
        return _CACHE
    if os.path.exists(OUTPUT) and not force:
        with open(OUTPUT, "r", encoding="utf-8") as f:
            _CACHE = json.load(f)
            return _CACHE
    annual = compute_annual_series()
    annual["history_correlation"] = compute_history_correlations(annual)
    annual["method"] = ("Percentil (0–1000) da média anual na janela 1800–2100. Correlação com a história: média do índice nos anos "
                        "com evento vs nulo de deslocamento circular dos anos (10.000 permutações); p bicaudal; lift = fração de anos "
                        "de evento no quartil superior dividida por 0,25.")
    with open(OUTPUT, "w", encoding="utf-8") as f:
        json.dump(annual, f, ensure_ascii=False)
    _CACHE = annual
    return annual


def get_year(year: int) -> Dict[str, float]:
    data = build()
    try:
        i = data["years"].index(year)
    except ValueError:
        return {k: 500.0 for k in SERIES}
    return {k: data["series"][k]["percentile_1000"][i] for k in SERIES}


if __name__ == "__main__":
    d = build(force=True)
    for key, corr in d["history_correlation"].items():
        print(f"\n== {d['series'][key]['label']} ==")
        for cat, r in corr.items():
            if r:
                print(f"  {cat:32s} n={r['n_event_years']:3d} obs={r['observed_mean']:6.1f} nulo={r['null_mean']:6.1f}±{r['null_sd']:5.1f} z={r['z']:+.2f} p={r['p_two_sided']:.3f} lift Q4={r['top_quartile_lift']:.2f}")
