"""
Testes automatizados para o motor de análise histórica retrospectiva e analogias preditivas.
"""
import pytest
from fastapi.testclient import TestClient

from src.web.app import app
from src.mundane.countries_data import get_country_by_iso
from src.mundane.transits_engine import calculate_country_chart
from src.mundane.historical_analyzer import (
    load_raw_historical_events,
    compute_event_astrological_signature,
    get_country_analyzed_history
)
from src.mundane.analogy_engine import generate_grounded_future_forecast

client = TestClient(app)

def test_historical_events_dataset_integrity():
    events = load_raw_historical_events()
    assert len(events) >= 80, f"Esperado >= 80 eventos históricos autênticos, encontrado {len(events)}"

    seen_ids = set()
    for e in events:
        eid = e["event_id"]
        assert eid not in seen_ids, f"ID duplicado: {eid}"
        seen_ids.add(eid)

        assert e["iso_code"], f"Evento sem iso_code: {eid}"
        assert e["title"], f"Evento sem título: {eid}"
        assert e["date"], f"Evento sem data: {eid}"
        assert e["category"], f"Evento sem categoria: {eid}"
        assert e["description"], f"Evento sem descrição: {eid}"
        assert e["historical_source"], f"Evento sem fonte: {eid}"

        # Validação temporal: eventos regulares devem ser posteriores à fundação (salvo marcos formativos documentados)
        country = get_country_by_iso(e["iso_code"])
        assert country is not None, f"País {e['iso_code']} não encontrado para evento {eid}"
        if not e.get("is_formative"):
            assert e["date"] >= country["date"], f"Evento {eid} em {e['date']} anterior à fundação de {e['iso_code']} em {country['date']}"

def test_brazil_historical_signatures():
    bra = get_country_by_iso("BRA")
    chart = calculate_country_chart(bra)
    history = get_country_analyzed_history(chart)

    assert len(history) >= 20, f"Esperado >= 20 eventos históricos do Brasil, encontrado {len(history)}"

    # Verificar Proclamação da República (1889-11-15)
    rep = next((h for h in history if "1889-11-15" in h["date"]), None)
    assert rep is not None
    assert rep["activation_index_1000"] > 600
    assert "Plutão" in rep["protagonist_headline"] or any("pluto" in t["transit_planet_id"] for t in rep["top_transits"])

    # Verificar Golpe de 1964 (1964-03-31)
    golpe = next((h for h in history if "1964-03-31" in h["date"]), None)
    assert golpe is not None
    assert golpe["activation_index_1000"] > 600

def test_usa_historical_signatures():
    usa = get_country_by_iso("USA")
    chart = calculate_country_chart(usa)
    history = get_country_analyzed_history(chart)

    assert len(history) >= 15

    # Verificar Guerra Civil (1861-04-12)
    civil_war = next((h for h in history if "1861-04-12" in h["date"]), None)
    assert civil_war is not None
    assert civil_war["category"] == "Guerra & Conflito"

    # Verificar Quebra de Wall Street (1929-10-29)
    crash = next((h for h in history if "1929-10-29" in h["date"]), None)
    assert crash is not None
    assert crash["category"] == "Crise Financeira & Econômica"

def test_grounded_future_forecast_generation():
    bra = get_country_by_iso("BRA")
    chart = calculate_country_chart(bra)
    forecasts = generate_grounded_future_forecast(chart)

    assert len(forecasts) >= 4
    for f in forecasts:
        assert f["year_range"]
        assert f["future_transit"]
        assert f["precedent_headline"]
        assert f["grounded_forecast"]
        assert len(f["grounded_forecast"]) > 50

def test_api_historical_events_endpoint():
    response = client.get("/api/countries/BRA/historical-events")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 20
    assert any("Guerra do Paraguai" in e["title"] for e in data["events"])

def test_api_analogies_endpoint():
    response = client.get("/api/countries/BRA/analogies")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 4
    assert "forecasts" in data
