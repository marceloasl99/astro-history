"""
Módulo de Grade Diária de Efemérides (1800–2100).
Pré-computa posições planetárias e scores de tensão diários (ao meio-dia UT)
para os ~110.000 dias entre 01/01/1800 e 31/12/2100.
Permite consultas vetorizadas e mapeamento de percentil empírico sem teto arbitrário.
"""

import os
import sys
from datetime import date, timedelta
from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import swisseph as swe

# Garantir que caminhos de efemérides estejam configurados
EPHE_PATHS = [
    "/usr/share/libswe/ephe",
    "/usr/share/swisseph",
    "/usr/local/share/swisseph"
]
for p in EPHE_PATHS:
    if os.path.exists(p):
        swe.set_ephe_path(p)
        break

GRID_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "ephemeris"))
GRID_FILE = os.path.join(GRID_DIR, "daily_grid_1800_2100.npz")

BODIES_CORE = [
    ("sun", swe.SUN, 2.0),
    ("mercury", swe.MERCURY, 1.2),
    ("venus", swe.VENUS, 1.2),
    ("mars", swe.MARS, 1.5),
    ("jupiter", swe.JUPITER, 1.5),
    ("saturn", swe.SATURN, 1.8),
    ("uranus", swe.URANUS, 2.0),
    ("neptune", swe.NEPTUNE, 1.8),
    ("pluto", swe.PLUTO, 2.2),
]

OUTER_BODIES = {"pluto", "neptune", "uranus", "saturn"}

ASPECT_ANGLES = [(0.0, 1.0, "Conjunção"), (90.0, 2.0, "Quadratura"), (120.0, -1.5, "Trígono"), (180.0, 2.5, "Oposição")]

from src.core.scoring import raw_tension_from_longitudes, raw_tension_from_array  # noqa: E402

def compute_raw_tension_from_longitudes(longitudes: np.ndarray, max_orb: float = 3.0) -> float:
    """
    Tensão cósmica bruta contínua (sem saturação) entre os 9 corpos principais.
    Delega para a função única em src/core/scoring.py (config/score.yaml).
    """
    body_names = [b[0] for b in BODIES_CORE]
    lons = {name: float(longitudes[i]) for i, name in enumerate(body_names)}
    return raw_tension_from_longitudes(lons, max_orb=max_orb)

_GRID_CACHE: Optional[Dict[str, Any]] = None

def build_daily_grid(start_year: int = 1800, end_year: int = 2100) -> Dict[str, Any]:
    """Pré-computa efemérides e tensões diárias de 1800 a 2100."""
    os.makedirs(GRID_DIR, exist_ok=True)

    start_date = date(start_year, 1, 1)
    end_date = date(end_year, 12, 31)
    total_days = (end_date - start_date).days + 1

    julian_days = np.empty(total_days, dtype=np.float64)
    # 9 corpos: sun, mercury, venus, mars, jupiter, saturn, uranus, neptune, pluto
    longitudes = np.empty((total_days, len(BODIES_CORE)), dtype=np.float32)
    raw_scores = np.empty(total_days, dtype=np.float32)

    curr = start_date
    cal_flag = swe.GREG_CAL

    swe_ids = [b[1] for b in BODIES_CORE]

    for idx in range(total_days):
        y, m, d = curr.year, curr.month, curr.day
        jd = swe.julday(y, m, d, 12.0, cal_flag)
        julian_days[idx] = jd

        lons = np.empty(len(BODIES_CORE), dtype=np.float32)
        for b_i, s_id in enumerate(swe_ids):
            res, _ = swe.calc_ut(jd, s_id)
            lons[b_i] = res[0]

        longitudes[idx] = lons
        curr += timedelta(days=1)

    raw_scores[:] = raw_tension_from_array(longitudes, [b[0] for b in BODIES_CORE]).astype(np.float32)

    # Ordenar scores para rank percentil empírico exato
    sorted_scores = np.sort(raw_scores)

    np.savez_compressed(
        GRID_FILE,
        julian_days=julian_days,
        longitudes=longitudes,
        raw_scores=raw_scores,
        sorted_scores=sorted_scores,
        start_year=np.int32(start_year),
        end_year=np.int32(end_year),
        total_days=np.int32(total_days)
    )

    data = {
        "julian_days": julian_days,
        "longitudes": longitudes,
        "raw_scores": raw_scores,
        "sorted_scores": sorted_scores,
        "start_date": start_date,
        "end_date": end_date,
        "total_days": total_days
    }
    return data

def get_daily_grid() -> Dict[str, Any]:
    """Carrega a grade diária em memória (com cache em nível de processo)."""
    global _GRID_CACHE
    if _GRID_CACHE is not None:
        return _GRID_CACHE

    if not os.path.exists(GRID_FILE):
        print(f"Grade diária {GRID_FILE} não encontrada. Construindo agora...")
        _GRID_CACHE = build_daily_grid()
        return _GRID_CACHE

    loaded = np.load(GRID_FILE)
    _GRID_CACHE = {
        "julian_days": loaded["julian_days"],
        "longitudes": loaded["longitudes"],
        "raw_scores": loaded["raw_scores"],
        "sorted_scores": loaded["sorted_scores"],
        "start_date": date(int(loaded["start_year"]), 1, 1),
        "end_date": date(int(loaded["end_year"]), 12, 31),
        "total_days": int(loaded["total_days"])
    }
    return _GRID_CACHE

def raw_score_to_percentile_1000(raw_score: float) -> float:
    """
    Converte um score bruto contínuo no percentil empírico exato (escala 0-1000).
    Exemplo: percentil 85.0% -> 850.0 pontos.
    Elimina qualquer saturação ou teto artificial de 990.
    """
    grid = get_daily_grid()
    sorted_scores = grid["sorted_scores"]
    n = len(sorted_scores)
    # Busca binária
    idx = np.searchsorted(sorted_scores, raw_score, side="right")
    percentile = (idx / n) * 1000.0
    return round(float(np.clip(percentile, 1.0, 1000.0)), 1)

def get_day_index(d: date) -> Optional[int]:
    """Retorna o índice do dia na grade ou None se fora de 1800-2100."""
    grid = get_daily_grid()
    start_date = grid["start_date"]
    if d < start_date or d > grid["end_date"]:
        return None
    return (d - start_date).days

def get_score_for_date(d: date) -> float:
    """Consulta rápida O(1) do score em escala 0-1000 para qualquer data entre 1800 e 2100."""
    idx = get_day_index(d)
    grid = get_daily_grid()
    if idx is not None and 0 <= idx < grid["total_days"]:
        raw = float(grid["raw_scores"][idx])
        return raw_score_to_percentile_1000(raw)
    else:
        # Fora do range de 1800-2100 (antiguidade / medieval)
        # Calcula sob demanda
        jd = swe.julday(d.year, d.month, d.day, 12.0)
        lons = np.empty(len(BODIES_CORE), dtype=np.float32)
        for b_i, (_, s_id, _) in enumerate(BODIES_CORE):
            res, _ = swe.calc_ut(jd, s_id)
            lons[b_i] = res[0]
        raw = compute_raw_tension_from_longitudes(lons)
        return raw_score_to_percentile_1000(raw)

def get_year_daily_stats(year: int) -> Dict[str, float]:
    """
    Calcula as estatísticas empíricas reais da janela de 365/366 dias do ano
    (média, mediana, máximo e percentil 90) a partir da grade diária.
    """
    d_start = date(year, 1, 1)
    d_end = date(year, 12, 31)
    idx_start = get_day_index(d_start)
    idx_end = get_day_index(d_end)

    grid = get_daily_grid()
    if idx_start is not None and idx_end is not None:
        raw_slice = grid["raw_scores"][idx_start : idx_end + 1]
    else:
        # Fallback para anos fora da grade
        days_in_year = (d_end - d_start).days + 1
        raw_slice = np.empty(days_in_year, dtype=np.float32)
        curr = d_start
        for i in range(days_in_year):
            jd = swe.julday(curr.year, curr.month, curr.day, 12.0)
            lons = np.empty(len(BODIES_CORE), dtype=np.float32)
            for b_i, (_, s_id, _) in enumerate(BODIES_CORE):
                res, _ = swe.calc_ut(jd, s_id)
                lons[b_i] = res[0]
            raw_slice[i] = compute_raw_tension_from_longitudes(lons)
            curr += timedelta(days=1)

    scores_1000 = np.array([raw_score_to_percentile_1000(float(r)) for r in raw_slice])

    return {
        "mean_tension": round(float(np.mean(scores_1000)), 1),
        "median_tension": round(float(np.median(scores_1000)), 1),
        "max_tension": round(float(np.max(scores_1000)), 1),
        "p90_tension": round(float(np.percentile(scores_1000, 90)), 1),
        "min_tension": round(float(np.min(scores_1000)), 1)
    }

_ANNUAL_CACHE: Optional[Dict[int, Dict[str, Any]]] = None

def _get_annual_cache() -> Dict[int, Dict[str, Any]]:
    global _ANNUAL_CACHE
    if _ANNUAL_CACHE is not None:
        return _ANNUAL_CACHE

    grid = get_daily_grid()
    sorted_all_daily = grid["sorted_scores"]
    p90_threshold_score = float(np.percentile(sorted_all_daily, 90.0))

    year_data = {}
    annual_means = []
    years = list(range(1800, 2101))

    for yr in years:
        d_start = date(yr, 1, 1)
        d_end = date(yr, 12, 31)
        idx_start = get_day_index(d_start)
        idx_end = get_day_index(d_end)

        raw_slice = grid["raw_scores"][idx_start : idx_end + 1]
        mean_raw = float(np.mean(raw_slice))
        annual_means.append(mean_raw)

        days_above_p90 = int(np.sum(raw_slice >= p90_threshold_score))
        daily_percentiles = np.searchsorted(sorted_all_daily, raw_slice, side="right") / len(sorted_all_daily) * 1000.0

        year_data[yr] = {
            "year": yr,
            "mean_raw": mean_raw,
            "days_in_year": len(raw_slice),
            "days_above_p90": days_above_p90,
            "expected_days_above_p90": round(len(raw_slice) * 0.1, 1),
            "daily_mean_percentile": round(float(np.mean(daily_percentiles)), 1),
            "daily_median_percentile": round(float(np.median(daily_percentiles)), 1),
            "daily_p90_percentile": round(float(np.percentile(daily_percentiles, 90.0)), 1),
            "daily_max_percentile": round(float(np.max(daily_percentiles)), 1),
            "daily_min_percentile": round(float(np.min(daily_percentiles)), 1),
        }

    sorted_means = np.sort(annual_means)
    n_years = len(sorted_means)

    for yr in years:
        m_raw = year_data[yr]["mean_raw"]
        idx = np.searchsorted(sorted_means, m_raw, side="right")
        annual_pct = round(float(np.clip((idx / n_years) * 1000.0, 1.0, 1000.0)), 1)
        year_data[yr]["annual_percentile_1000"] = annual_pct

        if annual_pct >= 800.0:
            tier = "Percentil Superior"
            badge = "indigo"
        elif annual_pct >= 300.0:
            tier = "Percentil Moderado"
            badge = "sky"
        else:
            tier = "Percentil Basal"
            badge = "emerald"

        year_data[yr]["tier_label"] = tier
        year_data[yr]["tier_color"] = badge

    _ANNUAL_CACHE = year_data
    return _ANNUAL_CACHE

def get_calibrated_year_metrics(year: int) -> Dict[str, Any]:
    """Retorna as métricas anuais calibradas (sem clamp, escala uniforme) para o ano."""
    cache = _get_annual_cache()
    if year in cache:
        return cache[year]
    return {
        "year": year,
        "annual_percentile_1000": 500.0,
        "daily_mean_percentile": 500.0,
        "daily_median_percentile": 500.0,
        "daily_p90_percentile": 500.0,
        "daily_max_percentile": 500.0,
        "daily_min_percentile": 500.0,
        "days_above_p90": 36,
        "expected_days_above_p90": 36.5,
        "tier_label": "Percentil Moderado",
        "tier_color": "sky"
    }

if __name__ == "__main__":
    print("Construindo grade diária 1800-2100...")
    g = build_daily_grid()
    print(f"Grade construída com {g['total_days']} dias.")
    sample_d = date(1914, 7, 28)
    print(f"Score em {sample_d}: {get_score_for_date(sample_d)}")
    print(f"Estatísticas anuais de 1914: {get_year_daily_stats(1914)}")
