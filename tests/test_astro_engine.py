import pytest
from src.astro_engine import (
    parse_date_to_julian_day,
    degree_to_sign_info,
    calculate_natal_bodies,
    calculate_strict_aspects,
    calculate_fixed_stars,
    calculate_fixed_star_aspects,
    calculate_event_chart,
    FIXED_STARS_CATALOG
)

def test_julian_day_calculation():
    jd, is_known = parse_date_to_julian_day("2001-09-11", "08:46", -74.01)
    assert jd > 2450000.0
    assert is_known is True

    jd_ancient, is_known_ancient = parse_date_to_julian_day("0490-09-12", "desconhecido", 23.96)
    assert jd_ancient > 0
    assert is_known_ancient is False

def test_degree_to_sign_info():
    aries = degree_to_sign_info(0.5)
    assert aries["sign_name"] == "Áries"
    assert aries["element"] == "Fogo"
    assert aries["modality"] == "Cardinal"

    scorpio = degree_to_sign_info(210.5)
    assert scorpio["sign_name"] == "Escorpião"
    assert scorpio["element"] == "Água"
    assert scorpio["modality"] == "Fixo"

def test_fixed_stars_catalog_count():
    assert len(FIXED_STARS_CATALOG) == 30
    star_keys = [s["key"] for s in FIXED_STARS_CATALOG]
    assert "Algol" in star_keys
    assert "Sirius" in star_keys
    assert "Aldebaran" in star_keys
    assert "Regulus" in star_keys
    assert "Antares" in star_keys

def test_strict_aspects_orb_3():
    ev = {
        "id": 93,
        "title": "Crash de 1929",
        "date": "1929-10-24",
        "time": "10:30",
        "latitude": 40.7069,
        "longitude": -74.0113
    }
    chart = calculate_event_chart(ev)
    # Todos os aspectos devem respeitar estritamente o orbe de 3.0 graus
    for a in chart["aspects"]:
        assert a["orb"] <= 3.0, f"Aspecto ultrapassou orbe de 3.0°: {a}"
        assert a["aspect_name"] in ["Conjunção", "Oposição", "Quadratura", "Trígono"]

    # 17 corpos (10 planetas + 4 asteroides + 3 pontos)
    assert len(chart["planets"]) == 17
    ids = [b["id"] for b in chart["planets"]]
    assert "ceres" in ids
    assert "pallas" in ids
    assert "juno" in ids
    assert "vesta" in ids
    assert "lilith" in ids

    # 30 estrelas calculadas
    assert len(chart["fixed_stars"]) == 30

    # Todos os contatos de estrelas fixas devem respeitar o orbe de 0.3 graus
    for sc in chart["star_contacts"]:
        assert sc["orb"] <= 0.3, f"Contato com estrela ultrapassou orbe de 0.3°: {sc}"
