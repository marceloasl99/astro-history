import pytest
from src.correlation_engine import get_category_correlations, find_similar_events
from src.astro_engine import calculate_event_chart

def test_category_correlations():
    corrs = get_category_correlations()
    assert "by_category" in corrs
    assert "Crise Econômica" in corrs["by_category"]
    assert "Guerra & Conflito" in corrs["by_category"]

    econ = corrs["by_category"]["Crise Econômica"]
    assert econ["total_events"] > 0
    assert econ["average_tension"] > 0

def test_find_similar_events():
    sim_ev = {
        "title": "Evento Simulado de Teste",
        "date": "2026-10-28",
        "time": "12:00",
        "latitude": -23.5505,
        "longitude": -46.6333
    }
    chart = calculate_event_chart(sim_ev)
    result = find_similar_events(chart, top_k=5)

    assert "top_matches" in result
    assert len(result["top_matches"]) == 5
    assert result["top_matches"][0]["match_percent"] > 0
    assert result["dominant_matching_category"] != ""
    assert len(result["historical_synthesis"]) > 50
