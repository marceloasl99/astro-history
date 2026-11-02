"""
Testes automatizados para a base de dados canônica dos países.
"""
import pytest
from src.mundane.countries_data import (
    load_countries_data,
    get_all_countries,
    get_country_by_iso,
    get_continents,
    search_countries
)

def test_countries_database_integrity():
    countries = get_all_countries()
    assert len(countries) >= 100, f"Esperado >= 100 países, encontrado {len(countries)}"
    
    seen_isos = set()
    for c in countries:
        iso = c["iso_code"]
        assert iso not in seen_isos, f"Código ISO duplicado: {iso}"
        seen_isos.add(iso)
        assert len(iso) == 3, f"ISO inválido: {iso}"
        assert c["name_pt"], f"País sem nome_pt: {iso}"
        assert c["name_en"], f"País sem name_en: {iso}"
        assert c["date"], f"País sem data de fundação: {iso}"
        assert "is_time_known" in c, f"Falta flag is_time_known em {iso}"
        assert "historical_justification" in c, f"Falta justificativa histórica em {iso}"
        assert len(c["historical_justification"]) > 20, f"Justificativa muito curta em {iso}"
        assert -90.0 <= c["latitude"] <= 90.0, f"Latitude inválida em {iso}"
        assert -180.0 <= c["longitude"] <= 180.0, f"Longitude inválida em {iso}"

def test_brazil_canonical_entry():
    bra = get_country_by_iso("BRA")
    assert bra is not None
    assert bra["name_pt"] == "Brasil"
    assert bra["date"] == "1822-09-07"
    assert bra["foundation_event"] == "Independência do Brasil (Grito do Ipiranga)"
    assert bra["is_time_known"] is False
    assert "Ipiranga" in bra["historical_justification"]

def test_usa_canonical_entry():
    usa = get_country_by_iso("USA")
    assert usa is not None
    assert usa["name_pt"] == "Estados Unidos"
    assert usa["date"] == "1776-07-04"
    assert usa["is_time_known"] is True

def test_continents_and_filtering():
    continents = get_continents()
    assert "América do Sul" in continents
    assert "Europa" in continents
    assert "Ásia" in continents

    sa_countries = search_countries(continent="América do Sul")
    assert any(c["iso_code"] == "BRA" for c in sa_countries)
    assert any(c["iso_code"] == "ARG" for c in sa_countries)
    assert not any(c["iso_code"] == "USA" for c in sa_countries)

    search_res = search_countries(query="brasil")
    assert len(search_res) == 1
    assert search_res[0]["iso_code"] == "BRA"
