"""
Testes automatizados para a Linha do Tempo Multidimensional com plotagem de categorias
(Guerra, Economia, Regime e Comoção Social) e separação de Histórico (Passado) e Futuro.
"""
import pytest
from fastapi.testclient import TestClient
from src.web.app import app
from src.mundane.countries_data import get_country_by_iso
from src.mundane.transits_engine import calculate_country_chart, calculate_activation_timeline

client = TestClient(app)

def test_timeline_categorized_series_brazil():
    """Valida o cálculo das séries temporais decompostas por categoria para o Brasil."""
    country = get_country_by_iso("BRA")
    assert country is not None
    chart = calculate_country_chart(country)
    timeline = calculate_activation_timeline(chart, start_year=1800, end_year=2060)

    # Chaves principais
    assert "years" in timeline
    assert "series" in timeline
    assert "historical_events" in timeline
    assert "future_peaks" in timeline
    assert "category_meta" in timeline
    assert timeline["split_year"] == 2026
    assert timeline["foundation_year"] == 1822

    total_years = len(timeline["years"])
    assert total_years == 261

    # Validação das 4 séries temáticas + consolidada
    series = timeline["series"]
    for cat in ["total", "WAR_CONFLICT", "ECONOMIC_CRASH", "REGIME_CRISIS", "SOCIAL_UPHEAVAL"]:
        assert cat in series
        assert len(series[cat]) == total_years
        assert all(0 <= score <= 1000 for score in series[cat])

    # Fatos históricos vinculados à linha do tempo
    hist_events = timeline["historical_events"]
    assert len(hist_events) >= 15
    for evt in hist_events:
        assert "year" in evt
        assert "date" in evt
        assert "title" in evt
        assert "category_key" in evt
        assert evt["category_key"] in ["WAR_CONFLICT", "ECONOMIC_CRASH", "REGIME_CRISIS", "SOCIAL_UPHEAVAL"]
        assert 0 <= evt["score"] <= 1000

    # Picos futuros vinculados à linha do tempo
    peaks = timeline["future_peaks"]
    assert len(peaks) > 0
    for peak in peaks:
        assert "year" in peak
        assert peak["year"] >= 2026
        assert "category_key" in peak
        assert "headline" in peak

def test_api_country_timeline_categorized():
    """Valida que o endpoint REST /api/countries/{iso_code}/timeline retorna o payload multidimensional."""
    response = client.get("/api/countries/BRA/timeline")
    assert response.status_code == 200
    data = response.json()

    assert "series" in data
    assert "WAR_CONFLICT" in data["series"]
    assert "ECONOMIC_CRASH" in data["series"]
    assert "REGIME_CRISIS" in data["series"]
    assert "SOCIAL_UPHEAVAL" in data["series"]
    assert len(data["historical_events"]) > 0
    assert len(data["future_peaks"]) > 0

def test_country_detail_renders_timeline_controls():
    """Verifica se a página /countries/BRA renderiza os botões de seleção de período e categoria."""
    response = client.get("/countries/BRA")
    assert response.status_code == 200
    html = response.text

    # Controles de Período (Passado vs Futuro)
    assert 'timeline-period-btn' in html
    assert 'data-period="all"' in html
    assert 'data-period="past"' in html
    assert 'data-period="future"' in html
    assert 'Linha Completa' in html
    assert 'Projeção Futura (2026–2060)' in html

    # Controles de Categoria
    assert 'timeline-cat-btn' in html
    assert 'data-cat="total"' in html
    assert 'data-cat="WAR_CONFLICT"' in html
    assert 'data-cat="ECONOMIC_CRASH"' in html
    assert 'data-cat="REGIME_CRISIS"' in html
    assert 'data-cat="SOCIAL_UPHEAVAL"' in html
    assert 'data-cat="multi"' in html

    # KPIs Dinâmicos
    assert 'kpi-past-peak' in html
    assert 'kpi-future-peak' in html
    assert 'kpi-archetype-name' in html

    # Validação rigorosa de ausência da entidade literal &bull;
    assert '&bull;' not in html
    assert '&bull' not in html
