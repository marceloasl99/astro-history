"""
Testes para o motor de Detecção de Picos de Energia Astrológica & Tendências Cíclicas Recorrentes (2026–2050),
e validação da ausência de 'Nicholas Campion' nas telas públicas de países.
"""
import pytest
from fastapi.testclient import TestClient
from src.web.app import app
from src.mundane.countries_data import get_country_by_iso
from src.mundane.transits_engine import calculate_country_chart
from src.mundane.energy_peaks import (
    detect_energy_peaks_and_recurrences,
    ENERGY_CATEGORIES,
    classify_transit_recurrence_theme
)

client = TestClient(app)

def test_no_campion_in_rendered_html():
    """Valida rigorosamente que o nome 'Nicholas Campion' não é exibido nas páginas dos países."""
    resp_hub = client.get("/countries")
    assert resp_hub.status_code == 200
    assert "Nicholas Campion" not in resp_hub.text
    assert "campion" not in resp_hub.text.lower()

    resp_bra = client.get("/countries/BRA")
    assert resp_bra.status_code == 200
    assert "Nicholas Campion" not in resp_bra.text

    resp_usa = client.get("/countries/USA")
    assert resp_usa.status_code == 200
    assert "Nicholas Campion" not in resp_usa.text

def test_classify_transit_recurrence_theme():
    """Valida o mapeamento categórico de aspectos planetários para temas históricos."""
    # Marte ou Urano/Plutão com Marte -> Conflito
    assert classify_transit_recurrence_theme("mars", "sun", "tenso") == "WAR_CONFLICT"
    assert classify_transit_recurrence_theme("pluto", "mars", "tenso") == "WAR_CONFLICT"

    # Saturno/Plutão com Júpiter/Vênus -> Quebra Econômica
    assert classify_transit_recurrence_theme("saturn", "jupiter", "tenso") == "ECONOMIC_CRASH"
    assert classify_transit_recurrence_theme("pluto", "venus", "tenso") == "ECONOMIC_CRASH"

    # Sol ou Saturno afetados -> Crise Institucional / Governo
    assert classify_transit_recurrence_theme("uranus", "sun", "tenso") == "REGIME_CRISIS"
    assert classify_transit_recurrence_theme("pluto", "saturn", "tenso") == "REGIME_CRISIS"

    # v6: Novas categorias e controles céticos
    assert classify_transit_recurrence_theme("uranus", "saturn", "tenso") == "NATURAL_DISASTER"
    assert classify_transit_recurrence_theme("neptune", "moon", "tenso") == "HEALTH_EPIDEMIC"
    assert classify_transit_recurrence_theme("jupiter", "sun", "harmonico") == "DIPLOMACY_PEACE"
    assert classify_transit_recurrence_theme("uranus", "mercury", "harmonico") == "SCIENCE_INNOVATION"

    # Lua ou Quíron afetados -> Comoção Social
    assert classify_transit_recurrence_theme("saturn", "moon", "tenso") == "SOCIAL_UPHEAVAL"

def test_detect_energy_peaks_brazil():
    """Testa o cálculo dos picos de energia e tendências recorrentes para o Brasil."""
    country = get_country_by_iso("BRA")
    assert country is not None
    chart = calculate_country_chart(country)
    peaks = detect_energy_peaks_and_recurrences(chart)

    assert len(peaks) > 0
    valid_categories = set(ENERGY_CATEGORIES.keys())

    for peak in peaks:
        assert "window_range" in peak
        assert "sample_date" in peak
        assert "activation_index_1000" in peak
        assert 0 <= peak["activation_index_1000"] <= 1000
        assert peak["category_key"] in valid_categories
        assert "icon" in peak
        assert "protagonist_transit" in peak
        assert "precedent_title" in peak
        assert "past_manifestation" in peak
        assert "future_recurrence_tendency" in peak
        # Validação do texto de tendência projetada
        assert len(peak["future_recurrence_tendency"]) > 20

def test_detect_energy_peaks_usa():
    """Testa o cálculo dos picos de energia e tendências recorrentes para os EUA."""
    country = get_country_by_iso("USA")
    assert country is not None
    chart = calculate_country_chart(country)
    peaks = detect_energy_peaks_and_recurrences(chart)

    assert len(peaks) > 0
    for peak in peaks:
        assert peak["category_key"] in ENERGY_CATEGORIES
        assert peak["activation_index_1000"] > 0

def test_api_country_energy_peaks_endpoint():
    """Testa o endpoint REST GET /api/countries/{iso_code}/energy-peaks."""
    response = client.get("/api/countries/BRA/energy-peaks")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "peaks" in data
    assert data["total"] == len(data["peaks"])
    assert data["total"] > 0

    first_peak = data["peaks"][0]
    assert "category_key" in first_peak
    assert "protagonist_transit" in first_peak
    assert "future_recurrence_tendency" in first_peak

def test_country_detail_renders_energy_peaks():
    """Verifica se o HTML da rota /countries/{iso_code} inclui o componente do Radar de Picos de Energia."""
    response = client.get("/countries/BRA")
    assert response.status_code == 200
    html = response.text

    assert "Radar de Picos de Energia & Tendências Cíclicas" in html
    assert "O Que Aconteceu no Passado" in html
    assert "O Que Tende a Acontecer Novamente" in html
    assert "Recorrência Cíclica" in html
    assert "Potencial Energético" in html
