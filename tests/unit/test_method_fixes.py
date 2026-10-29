import pytest
from datetime import date
from src.astro_engine import (
    calculate_event_chart,
    calculate_fixed_star_aspects,
    calculate_strict_aspects,
    FIXED_STARS_CATALOG
)
from src.correlation_engine import find_similar_events
from src.core.ephemeris_grid import get_score_for_date, get_year_daily_stats

def test_leave_one_out_matcher():
    """
    P0-3: Garante que find_similar_events NUNCA retorna um evento do mesmo ano
    ou da janela [ano - exclude_window, ano + exclude_window].
    """
    target_chart = {
        "event_id": 9999,
        "date": "1945-08-06",
        "planets": [],
        "aspects": [],
        "star_contacts": [],
        "summary": {"tension_index": 70.0}
    }
    # Testar com exclude_year=1945, exclude_window=1
    res = find_similar_events(target_chart, top_k=5, exclude_year=1945, exclude_window=1)
    matches = res["top_matches"]
    for m in matches:
        match_year = int(m["date"].split("-")[0]) if not m["date"].startswith("-") else -int(m["date"].split("-")[1])
        assert abs(match_year - 1945) > 1, f"Vazamento detectado: match com evento do ano {match_year}"

def test_moon_excluded_when_time_unknown():
    """
    P1-1: Quando o horário do evento é desconhecido, a Lua (~13°/dia)
    não deve entrar no cálculo de aspectos nem distorcer a tensão.
    """
    ev_unknown = {
        "date": "1914-07-28",
        "time": "desconhecido",
        "latitude": 44.8,
        "longitude": 20.4
    }
    chart_unknown = calculate_event_chart(ev_unknown)
    assert not chart_unknown["is_time_known"]

    # Verifica que nenhum aspecto calculado contém a Lua
    aspect_bodies = {a["planet1_id"] for a in chart_unknown["aspects"]} | {a["planet2_id"] for a in chart_unknown["aspects"]}
    assert "moon" not in aspect_bodies, "A Lua não pode gerar aspectos quando a hora é desconhecida!"

def test_fixed_stars_only_conjunctions():
    """
    P1-4: As estrelas fixas só devem ser contabilizadas em Conjunção (0° +/- 0.3°),
    eliminando quadraturas, trígonos e oposições que inflavam aleatoriamente os contatos.
    """
    # Criar um corpo fictício em quadratura exata (90°) com uma estrela
    star = FIXED_STARS_CATALOG[0]  # Algol
    bodies = [{
        "id": "mars",
        "name": "Marte",
        "symbol": "♂",
        "longitude": 0.0
    }]
    fake_star = [{
        "key": "Algol",
        "name": "Algol",
        "bayer": "Beta Persei",
        "significance": "Teste",
        "longitude": 90.0  # 90° de Marte (quadratura)
    }]
    contacts = calculate_fixed_star_aspects(bodies, fake_star, max_orb=0.3)
    assert len(contacts) == 0, "Quadratura com estrela fixa não deve ser contabilizada!"

    # Agora em conjunção exata
    fake_star[0]["longitude"] = 0.1
    conjunctions = calculate_fixed_star_aspects(bodies, fake_star, max_orb=0.3)
    assert len(conjunctions) == 1, "Conjunção dentro do orbe <= 0.3° deve ser contabilizada!"
    assert conjunctions[0]["aspect_name"] == "Conjunção"

def test_ephemeris_grid_query_and_percentiles():
    """
    P1-2 & P1-3: A grade diária vetorizada deve fornecer consultas O(1)
    e estatísticas anuais completas sem teto artificial de 990.
    """
    sample_date = date(1939, 9, 1)
    score = get_score_for_date(sample_date)
    assert 1.0 <= score <= 1000.0

    stats = get_year_daily_stats(1939)
    assert "mean_tension" in stats
    assert "median_tension" in stats
    assert "max_tension" in stats
    assert stats["max_tension"] >= stats["median_tension"] >= stats["min_tension"]
