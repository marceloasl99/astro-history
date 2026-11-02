"""
Testes unitários e matemáticos para a família de métricas Sum of Cosines (Renay Oshop / Project 17).
"""

import math
import pytest
from src.features.sum_of_cosines import (
    compute_sum_of_cosines,
    calculate_oshop_indices,
    test_permutation_significance as run_permutation_test,
    get_planet_longitudes
)

def test_sum_of_cosines_perfect_stellium():
    """Todos os planetas exatamente no mesmo grau (0°) devem produzir clustering = +1.0."""
    lons = {"p1": 45.0, "p2": 45.0, "p3": 45.0, "p4": 45.0}
    res = compute_sum_of_cosines(lons)
    assert res["n_bodies"] == 4
    assert res["num_pairs"] == 6
    assert abs(res["clustering_index"] - 1.0) < 1e-4
    assert abs(res["mean_resultant_length"] - 1.0) < 1e-4
    assert abs(res["circular_variance"] - 0.0) < 1e-4

def test_sum_of_cosines_exact_opposition():
    """Dois corpos em oposição exata (180°) devem produzir clustering = -1.0."""
    lons = {"sun": 0.0, "moon": 180.0}
    res = compute_sum_of_cosines(lons)
    assert res["n_bodies"] == 2
    assert res["num_pairs"] == 1
    assert abs(res["clustering_index"] - (-1.0)) < 1e-4

def test_sum_of_cosines_quadrature():
    """Dois corpos em quadratura exata (90°) devem produzir cosseno = 0.0."""
    lons = {"mars": 0.0, "saturn": 90.0}
    res = compute_sum_of_cosines(lons)
    assert abs(res["clustering_index"] - 0.0) < 1e-4

def test_calculate_oshop_indices_geocentric_and_heliocentric():
    """Testa cálculo completo de Oshop para data histórica conhecida (Hiroshima: 1945-08-06)."""
    # JD 2431673.46875 = 1945-08-06 08:15 UTC
    tjd = 2431673.46875
    indices = calculate_oshop_indices(tjd)
    
    assert "geo_full_10" in indices
    assert "geo_outer_5" in indices
    assert "helio_outer_5" in indices
    
    # Outer 5 deve conter exatamente 5 corpos e 10 pares
    outer = indices["geo_outer_5"]
    assert outer["n_bodies"] == 5
    assert outer["num_pairs"] == 10
    assert -1.0 <= outer["clustering_index"] <= 1.0
    assert 0.0 <= outer["mean_resultant_length"] <= 1.0

def test_permutation_significance():
    """Testa o gerador de testes de hipótese por permutação."""
    perm = run_permutation_test(0.80, num_bodies=5, num_permutations=500, seed=42)
    assert perm["target_clustering"] == 0.80
    assert abs(perm["null_mean"]) < 0.10  # A média nula no círculo completo é próxima de 0
    assert perm["z_score"] > 2.0  # 0.80 é um valor muito alto de clustering
    assert perm["p_value"] < 0.05
