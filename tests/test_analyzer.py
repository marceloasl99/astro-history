import pytest
from src.analyze_correlations import calculate_event_emphasis, calculate_macro_correlations

def test_calculate_event_emphasis_crash_1929():
    res = calculate_event_emphasis(93)
    assert res["event_id"] == 93
    assert "dominant_planet" in res
    assert res["dominant_planet"]["score"] > 0
    assert res["dominant_sign"]["name"] != ""
    assert "modern_astrology_rationale" in res
    assert len(res["modern_astrology_rationale"]) > 100
    assert "ARQUÉTIPO CENTRAL" in res["modern_astrology_rationale"]
    assert "CORROBORAÇÃO" in res["modern_astrology_rationale"]

def test_calculate_event_emphasis_hiroshima():
    res = calculate_event_emphasis(107)
    assert res["event_id"] == 107
    assert res["dominant_planet"]["name"] != ""
    assert res["tension_index"] > 0

def test_macro_correlations():
    macro = calculate_macro_correlations()
    assert macro["total_historical_events"] == 200
    assert "categories_analysis" in macro
    assert "Crise Econômica" in macro["categories_analysis"]
    assert "Guerra & Conflito" in macro["categories_analysis"]
    
    war_cat = macro["categories_analysis"]["Guerra & Conflito"]
    assert war_cat["total_events"] > 0
    assert len(war_cat["top_placements"]) > 0
    assert len(war_cat["modern_astrology_theory"]) > 50
