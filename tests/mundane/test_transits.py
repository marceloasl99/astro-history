"""
Testes automatizados para o motor de cartas natais e trânsitos mundanos.
"""
import pytest
from src.mundane.countries_data import get_country_by_iso
from src.mundane.transits_engine import (
    calculate_country_chart,
    calculate_transits_for_date,
    calculate_activation_timeline
)
from src.mundane.history_and_future import (
    get_country_historical_correlations,
    get_country_future_outlook
)
from src.mundane.mandala_biwheel import generate_biwheel_svg

def test_brazil_chart_calculation():
    bra = get_country_by_iso("BRA")
    chart = calculate_country_chart(bra)

    assert chart["country_iso"] == "BRA"
    assert chart["sun_sign"] == "Virgem"
    # Sol do Brasil em 07/09/1822 fica a aproximadamente 14° de Virgem
    sun = next(p for p in chart["planets"] if p["id"] == "sun")
    assert 13.0 <= sun["degree_in_sign"] <= 15.5
    
    # Regra essencial: Sem casas se horário desconhecido!
    assert chart["is_time_known"] is False
    assert chart["houses"]["houses_available"] is False
    assert chart["houses"]["ascendant"] is None

def test_usa_chart_calculation():
    usa = get_country_by_iso("USA")
    chart = calculate_country_chart(usa)

    assert chart["country_iso"] == "USA"
    assert chart["sun_sign"] == "Câncer"
    # Sol dos EUA em 04/07/1776 fica a aproximadamente 13° de Câncer
    sun = next(p for p in chart["planets"] if p["id"] == "sun")
    assert 12.0 <= sun["degree_in_sign"] <= 14.5
    assert chart["is_time_known"] is True
    assert chart["houses"]["houses_available"] is True
    assert chart["houses"]["ascendant"] is not None

def test_transits_calculation():
    bra = get_country_by_iso("BRA")
    chart = calculate_country_chart(bra)

    # Teste para 15/11/1889 (Proclamação da República)
    trans = calculate_transits_for_date(chart, "1889-11-15")
    assert trans["active_transits_count"] > 0
    assert 0 <= trans["activation_index_1000"] <= 1000

    # Plutão estava conjunto a Júpiter natal do Brasil em 1889
    pluto_jupiter = [t for t in trans["transits"] if t["transit_planet_id"] == "pluto" and t["natal_planet_id"] == "jupiter"]
    assert len(pluto_jupiter) >= 1
    assert pluto_jupiter[0]["aspect_name"] == "Conjunção"

def test_timeline_generation():
    bra = get_country_by_iso("BRA")
    chart = calculate_country_chart(bra)
    timeline = calculate_activation_timeline(chart, start_year=1900, end_year=1910)

    assert len(timeline["years"]) == 11
    assert len(timeline["activation_scores"]) == 11
    assert all(0 <= s <= 1000 for s in timeline["activation_scores"])

def test_historical_correlations_and_future_outlook():
    bra = get_country_by_iso("BRA")
    chart = calculate_country_chart(bra)

    correlations = get_country_historical_correlations("BRA", chart)
    assert len(correlations) >= 3
    assert any("República" in c["title"] for c in correlations)

    future = get_country_future_outlook(chart, start_year=2026, end_year=2050)
    assert len(future["future_cycles"]) >= 3
    assert len(future["pillars"]) == 5
    assert "sovereignty_leadership" in future["pillars"]

def test_biwheel_svg_generation():
    bra = get_country_by_iso("BRA")
    chart = calculate_country_chart(bra)
    trans = calculate_transits_for_date(chart, "2026-11-01")

    svg = generate_biwheel_svg(chart, trans)
    assert svg.startswith("<svg")
    assert svg.endswith("</svg>")
    assert "Carta Solar" in svg
