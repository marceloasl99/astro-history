"""
sum_of_cosines.py
Implementação da família de métricas 'Sum of Cosines' de Renay Oshop (Project 17 do Big Astrology Book).
Mede a coerência angular e o grau de agrupamento/alinhamento planetário no zodíaco.

Fórmula:
    S = sum_{i < j} cos(lambda_i - lambda_j)
    C = S / (N * (N - 1) / 2)  [Normalizado em [-1, +1]]

Valores de C:
    +1.0 : Alinhamento perfeito (stellium completo em um único grau)
     0.0 : Distribuição ortogonal ou uniformemente espalhada
    -0.5 : Distribuição perfeitamente equilibrada (ex: triângulos / polígonos regulares)

Suporta sistemas Geocêntrico e Heliocêntrico, subconjuntos de planetas (exteriores, interiores e todos),
e testes de significância estatística via Monte Carlo / Permutação.
"""

import math
import random
from typing import Dict, Any, List, Optional, Tuple
import swisseph as swe

# Mapeamento de corpos da Swiss Ephemeris
SWE_PLANETS = {
    "sun": swe.SUN,
    "moon": swe.MOON,
    "mercury": swe.MERCURY,
    "venus": swe.VENUS,
    "mars": swe.MARS,
    "jupiter": swe.JUPITER,
    "saturn": swe.SATURN,
    "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE,
    "pluto": swe.PLUTO,
}

OUTER_PLANET_KEYS = ["jupiter", "saturn", "uranus", "neptune", "pluto"]
CLASSICAL_PLANET_KEYS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn"]
FULL_10_PLANET_KEYS = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]
HELIO_PLANET_KEYS = ["mercury", "venus", "earth", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]

def get_planet_longitudes(tjd_ut: float, heliocentric: bool = False, bodies: Optional[List[str]] = None) -> Dict[str, float]:
    """
    Retorna as longitudes eclípticas (0° a 360°) para os corpos especificados.
    """
    if bodies is None:
        bodies = FULL_10_PLANET_KEYS if not heliocentric else ["mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto"]

    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    if heliocentric:
        flags |= swe.FLG_HELCTR

    longitudes = {}
    for b in bodies:
        if b == "earth" and heliocentric:
            # Posição da Terra heliocêntrica = oposto do Sol geocêntrico
            res, _ = swe.calc_ut(tjd_ut, swe.SUN, swe.FLG_SWIEPH)
            longitudes["earth"] = (res[0] + 180.0) % 360.0
            continue

        if b in SWE_PLANETS:
            pid = SWE_PLANETS[b]
            # No modo heliocêntrico, Sol e Lua não são calculados como planetas orbitando o Sol
            if heliocentric and pid in (swe.SUN, swe.MOON):
                continue
            res, _ = swe.calc_ut(tjd_ut, pid, flags)
            longitudes[b] = res[0] % 360.0

    return longitudes

def compute_sum_of_cosines(longitudes: Dict[str, float]) -> Dict[str, float]:
    """
    Calcula a métrica Sum of Cosines e o índice de agrupamento normalizado C.
    Também calcula o vetor resultante circular (R_bar) e variância circular.
    """
    keys = sorted(longitudes.keys())
    n = len(keys)
    if n < 2:
        return {
            "n_bodies": n,
            "sum_of_cosines": 0.0,
            "clustering_index": 0.0,
            "mean_resultant_length": 0.0,
            "circular_variance": 1.0,
            "num_pairs": 0
        }

    sum_cos = 0.0
    num_pairs = 0
    rad_conv = math.pi / 180.0

    # 1. Soma de Cossenos dos pares
    for i in range(n):
        lon_i = longitudes[keys[i]]
        for j in range(i + 1, n):
            lon_j = longitudes[keys[j]]
            delta = abs(lon_i - lon_j) * rad_conv
            sum_cos += math.cos(delta)
            num_pairs += 1

    clustering_index = sum_cos / num_pairs if num_pairs > 0 else 0.0

    # 2. Estatística Circular (Vetor Resultante Médio R_bar)
    sum_x = sum(math.cos(longitudes[k] * rad_conv) for k in keys)
    sum_y = sum(math.sin(longitudes[k] * rad_conv) for k in keys)
    r_bar = math.sqrt(sum_x**2 + sum_y**2) / n
    circ_var = 1.0 - r_bar

    return {
        "n_bodies": n,
        "sum_of_cosines": round(sum_cos, 4),
        "clustering_index": round(clustering_index, 4),
        "mean_resultant_length": round(r_bar, 4),
        "circular_variance": round(circ_var, 4),
        "num_pairs": num_pairs
    }

def calculate_oshop_indices(tjd_ut: float) -> Dict[str, Any]:
    """
    Calcula a suíte completa de métricas de Oshop para uma data juliana:
    - Geo All (10 corpos)
    - Geo Outer (Júpiter a Plutão)
    - Geo Classical (7 planetas)
    - Helio Outer
    - Helio All
    """
    geo_all_lons = get_planet_longitudes(tjd_ut, heliocentric=False, bodies=FULL_10_PLANET_KEYS)
    geo_outer_lons = {k: geo_all_lons[k] for k in OUTER_PLANET_KEYS if k in geo_all_lons}
    geo_class_lons = {k: geo_all_lons[k] for k in CLASSICAL_PLANET_KEYS if k in geo_all_lons}

    helio_lons = get_planet_longitudes(tjd_ut, heliocentric=True)
    helio_outer_lons = {k: helio_lons[k] for k in OUTER_PLANET_KEYS if k in helio_lons}

    return {
        "tjd_ut": tjd_ut,
        "geo_full_10": compute_sum_of_cosines(geo_all_lons),
        "geo_outer_5": compute_sum_of_cosines(geo_outer_lons),
        "geo_classical_7": compute_sum_of_cosines(geo_class_lons),
        "helio_all": compute_sum_of_cosines(helio_lons),
        "helio_outer_5": compute_sum_of_cosines(helio_outer_lons),
    }

def test_permutation_significance(
    target_clustering: float,
    num_bodies: int = 5,
    num_permutations: int = 10000,
    seed: int = 42
) -> Dict[str, Any]:
    """
    Testa se o clustering observado difere significativamente de ângulos distribuídos aleatoriamente no círculo [0, 360).
    Permite verificar empiricamente a taxa de falsos positivos e z-score de qualquer configuração.
    """
    rng = random.Random(seed)
    rad_conv = math.pi / 180.0
    num_pairs = num_bodies * (num_bodies - 1) // 2

    perm_scores = []
    for _ in range(num_permutations):
        angles = [rng.uniform(0, 360) for _ in range(num_bodies)]
        s = 0.0
        for i in range(num_bodies):
            for j in range(i + 1, num_bodies):
                s += math.cos((angles[i] - angles[j]) * rad_conv)
        perm_scores.append(s / num_pairs)

    mean_perm = sum(perm_scores) / len(perm_scores)
    var_perm = sum((x - mean_perm)**2 for x in perm_scores) / (len(perm_scores) - 1)
    std_perm = math.sqrt(var_perm)

    z_score = (target_clustering - mean_perm) / std_perm if std_perm > 0 else 0.0
    # p-value unilateral (probabilidade de observar clustering >= target_clustering ao acaso)
    p_value = sum(1 for x in perm_scores if x >= target_clustering) / len(perm_scores)

    return {
        "target_clustering": round(target_clustering, 4),
        "null_mean": round(mean_perm, 4),
        "null_std": round(std_perm, 4),
        "z_score": round(z_score, 4),
        "p_value": round(p_value, 5),
        "permutations": num_permutations
    }
