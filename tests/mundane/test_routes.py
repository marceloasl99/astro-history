"""
Testes de integração das rotas web e API REST para a seção de Astrologia Mundana.
"""
import pytest
from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

def test_countries_hub_route():
    response = client.get("/countries")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Mapas Natais dos Países" in response.text
    assert "Brasil" in response.text
    assert "Estados Unidos" in response.text

def test_countries_hub_compact_and_no_cut_text():
    """Valida que textos longos de eventos são renderizados integralmente e sem classes de corte."""
    response = client.get("/countries")
    assert response.status_code == 200
    html = response.text
    # Nenhum evento ou texto deve ter max-w restritivo ou line-clamp na grade de países
    assert "max-w-[130px]" not in html
    assert "line-clamp" not in html
    # Eventos longos documentados devem aparecer por completo
    assert "Posse de Nelson Mandela (Fim do Apartheid &amp; África do Sul Democrática)" in html
    assert "Declaração de Independência da República Democrática do Vietnã" in html
    assert "Tratado de Paz de São Francisco (Soberania Plena Pós-Guerra)" in html
    # O card deve ser um link direto e compacto
    assert 'href="/countries/BRA"' in html

def test_country_detail_route_brazil():
    response = client.get("/countries/BRA")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Brasil" in response.text
    assert "Grito do Ipiranga" in response.text
    assert "Sem Casas" in response.text
    assert "Mandala Bi-Wheel" in response.text
    assert "countryTimelineChart" in response.text

def test_country_detail_route_usa():
    response = client.get("/countries/USA")
    assert response.status_code == 200
    assert "Estados Unidos" in response.text
    assert "Declaração de Independência" in response.text
    assert "Casas Placidus" in response.text

def test_country_not_found():
    response = client.get("/countries/ZZZ")
    assert response.status_code == 404

def test_api_countries_list():
    response = client.get("/api/countries")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert data["total"] >= 100
    assert any(c["iso_code"] == "BRA" for c in data["countries"])

def test_api_country_transits():
    response = client.get("/api/countries/BRA/transits?date=2026-11-01")
    assert response.status_code == 200
    data = response.json()
    assert data["country_iso"] == "BRA"
    assert "activation_index_1000" in data
    assert "transits" in data
    assert len(data["transits"]) > 0

def test_api_country_timeline():
    response = client.get("/api/countries/BRA/timeline?start=1950&end=1970")
    assert response.status_code == 200
    data = response.json()
    assert len(data["years"]) == 21
    assert len(data["activation_scores"]) == 21

def test_api_country_outlook():
    response = client.get("/api/countries/BRA/outlook")
    assert response.status_code == 200
    data = response.json()
    assert "future_cycles" in data
    assert "pillars" in data
