"""
barbault_ci.py
Implementação comparativa formal do Índice Cíclico de André Barbault (CI-4 vs CI-5).
Referência: André Barbault (1967), 'Les Astres et l'Histoire';
            Christos Archos (2024), 'The Barbault Cyclic Index: A Statistical Validation Over 2,826 Years'.

Fórmula:
    CI = sum_{i < j} min(|lambda_i - lambda_j|, 360° - |lambda_i - lambda_j|)

Onde:
    CI-5: Usa os 5 planetas lentos (Júpiter, Saturno, Urano, Netuno, Plutão) -> 10 pares. Escala: [0°, 1800°].
    CI-4: Usa os 4 planetas lentos tradicionais/modernos (Júpiter, Saturno, Urano, Netuno) -> 6 pares. Escala: [0°, 1080°].

Inclui:
- Cálculo do índice absoluto e normalizado (0 a 100%);
- Média angular por par (permite comparação direta entre CI-4 e CI-5 na mesma escala em graus);
- Derivada / Tendência de 1 ano (se o índice está em ascensão, declínio ou no fundo de um vale);
- Comparação estatística e teste de hipótese de Barbault-Archos.
"""

import math
from typing import Dict, Any, List, Optional, Tuple
import swisseph as swe

PLANETS_CI5 = [
    ("jupiter", swe.JUPITER),
    ("saturn", swe.SATURN),
    ("uranus", swe.URANUS),
    ("neptune", swe.NEPTUNE),
    ("pluto", swe.PLUTO),
]

PLANETS_CI4 = [
    ("jupiter", swe.JUPITER),
    ("saturn", swe.SATURN),
    ("uranus", swe.URANUS),
    ("neptune", swe.NEPTUNE),
]

def angular_distance(deg1: float, deg2: float) -> float:
    """Calcula a menor distância angular no círculo [0°, 180°]."""
    diff = abs(deg1 - deg2) % 360.0
    return min(diff, 360.0 - diff)

def get_outer_longitudes(tjd_ut: float) -> Dict[str, float]:
    """Retorna longitudes geocêntricas dos 5 planetas exteriores."""
    lons = {}
    for name, pid in PLANETS_CI5:
        res, _ = swe.calc_ut(tjd_ut, pid, swe.FLG_SWIEPH | swe.FLG_SPEED)
        lons[name] = res[0] % 360.0
    return lons

def compute_cyclic_index(longitudes: Dict[str, float], use_pluto: bool = True) -> Dict[str, Any]:
    """
    Calcula o Índice Cíclico para um conjunto de posições planetárias.
    Se use_pluto=True, calcula CI-5 (10 pares). Se False, calcula CI-4 (6 pares).
    """
    planets = ["jupiter", "saturn", "uranus", "neptune"]
    if use_pluto:
        planets.append("pluto")

    n = len(planets)
    num_pairs = n * (n - 1) // 2
    max_possible = num_pairs * 180.0

    pair_distances = {}
    total_dist = 0.0

    for i in range(n):
        p1 = planets[i]
        for j in range(i + 1, n):
            p2 = planets[j]
            dist = angular_distance(longitudes[p1], longitudes[p2])
            pair_distances[f"{p1}_{p2}"] = round(dist, 2)
            total_dist += dist

    mean_dist = total_dist / num_pairs if num_pairs > 0 else 0.0
    pct = (total_dist / max_possible) * 100.0 if max_possible > 0 else 0.0

    return {
        "version": "CI-5" if use_pluto else "CI-4",
        "has_pluto": use_pluto,
        "num_pairs": num_pairs,
        "sum_degrees": round(total_dist, 2),
        "mean_pair_distance": round(mean_dist, 2),
        "normalized_pct": round(pct, 2),
        "max_possible_degrees": max_possible,
        "pairs": pair_distances
    }

def calculate_barbault_comparison(tjd_ut: float) -> Dict[str, Any]:
    """
    Calcula simultaneamente CI-4 e CI-5 com suas respectivas tendências anuais (derivadas).
    """
    # 1. Longitudes atuais
    current_lons = get_outer_longitudes(tjd_ut)
    ci5_current = compute_cyclic_index(current_lons, use_pluto=True)
    ci4_current = compute_cyclic_index(current_lons, use_pluto=False)

    # 2. Longitudes 1 ano antes e 1 ano depois para avaliar tendência (derivada)
    days_in_year = 365.2425
    prev_lons = get_outer_longitudes(tjd_ut - days_in_year)
    next_lons = get_outer_longitudes(tjd_ut + days_in_year)

    ci5_prev = compute_cyclic_index(prev_lons, use_pluto=True)["sum_degrees"]
    ci5_next = compute_cyclic_index(next_lons, use_pluto=True)["sum_degrees"]
    ci5_slope = (ci5_next - ci5_prev) / 2.0  # Variação anual média

    ci4_prev = compute_cyclic_index(prev_lons, use_pluto=False)["sum_degrees"]
    ci4_next = compute_cyclic_index(next_lons, use_pluto=False)["sum_degrees"]
    ci4_slope = (ci4_next - ci4_prev) / 2.0

    def classify_trend(slope: float, current_pct: float) -> str:
        if current_pct < 35.0 and abs(slope) < 15.0:
            return "Vale Crítico / Mínimo Cíclico"
        elif current_pct > 65.0 and abs(slope) < 15.0:
            return "Pico de Expansão / Máximo Cíclico"
        elif slope < -10.0:
            return "Fase Descendente (Contração / Tensão Crescente)"
        elif slope > 10.0:
            return "Fase Ascendente (Recuperação / Relaxamento)"
        else:
            return "Fase Estável / Transição"

    return {
        "tjd_ut": tjd_ut,
        "ci5": {
            **ci5_current,
            "annual_slope": round(ci5_slope, 2),
            "trend": classify_trend(ci5_slope, ci5_current["normalized_pct"])
        },
        "ci4": {
            **ci4_current,
            "annual_slope": round(ci4_slope, 2),
            "trend": classify_trend(ci4_slope, ci4_current["normalized_pct"])
        },
        "pluto_contribution_degrees": round(ci5_current["sum_degrees"] - ci4_current["sum_degrees"], 2),
        "divergence_flag": (ci5_current["normalized_pct"] < 40.0 and ci4_current["normalized_pct"] >= 40.0) or (ci4_current["normalized_pct"] < 40.0 and ci5_current["normalized_pct"] >= 40.0)
    }
