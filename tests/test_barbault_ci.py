"""
Testes unitários e comparativos para o Índice Cíclico de André Barbault (CI-4 vs CI-5).
"""

import pytest
import swisseph as swe
from src.features.barbault_ci import (
    angular_distance,
    compute_cyclic_index,
    calculate_barbault_comparison
)

def test_angular_distance():
    assert angular_distance(10.0, 20.0) == 10.0
    assert angular_distance(350.0, 10.0) == 20.0  # Cruzando o ponto 0° de Áries
    assert angular_distance(0.0, 180.0) == 180.0
    assert angular_distance(0.0, 200.0) == 160.0  # Menor arco

def test_compute_cyclic_index_ci4_and_ci5():
    # Posições simuladas
    lons = {
        "jupiter": 0.0,
        "saturn": 30.0,
        "uranus": 60.0,
        "neptune": 90.0,
        "pluto": 120.0
    }

    ci5 = compute_cyclic_index(lons, use_pluto=True)
    assert ci5["version"] == "CI-5"
    assert ci5["num_pairs"] == 10
    assert ci5["max_possible_degrees"] == 1800.0

    ci4 = compute_cyclic_index(lons, use_pluto=False)
    assert ci4["version"] == "CI-4"
    assert ci4["num_pairs"] == 6
    assert ci4["max_possible_degrees"] == 1080.0

    # A média angular por par deve ser positiva e <= 180°
    assert 0.0 < ci5["mean_pair_distance"] < 180.0
    assert 0.0 < ci4["mean_pair_distance"] < 180.0

def test_calculate_barbault_comparison_historical_crisis():
    """Crise do início da Primeira Guerra Mundial (1914-07-28)."""
    tjd = swe.julday(1914, 7, 28, 12.0)
    res = calculate_barbault_comparison(tjd)

    assert "ci5" in res
    assert "ci4" in res
    assert "pluto_contribution_degrees" in res
    assert res["ci5"]["annual_slope"] < 0.0  # Barbault postulou fase descendente
    assert "Fase Descendente" in res["ci5"]["trend"]
