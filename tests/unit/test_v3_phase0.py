"""
Fase 0 (v3): precisão de cálculo.
- Paridade entre a grade diária e a carta do evento (função de score única).
- Fuso horário histórico real (IANA) e Hora Média Local com virada de dia.
- Fallback de casas em latitude polar.
- Estrelas longe da eclíptica não pontuam.
"""

from datetime import date
import swisseph as swe

from src.astro_engine import (
    calculate_event_chart,
    resolve_event_instant,
    calculate_houses,
    calculate_chart_tension_1000,
)
from src.core.ephemeris_grid import get_score_for_date, get_daily_grid, BODIES_CORE
from src.core.scoring import raw_tension_from_longitudes, raw_tension_from_array, load_score_config
from src.core.timezones import local_to_ut


def test_scoring_parity_grid_vs_chart():
    """A carta de um dia ao meio-dia UT deve ter o MESMO percentil da grade diária."""
    for d in [date(1914, 7, 28), date(1929, 10, 24), date(2001, 9, 11), date(2045, 3, 3)]:
        chart = calculate_event_chart({"date": d.isoformat(), "time": "12:00", "latitude": 0.0, "longitude": 0.0})
        assert chart["utc_offset_hours"] == 0.0
        assert abs(chart["summary"]["tension_index_1000"] - get_score_for_date(d)) <= 0.2


def test_vectorized_scoring_matches_scalar_and_stored_grid():
    g = get_daily_grid()
    ids = [b[0] for b in BODIES_CORE]
    sample = slice(50000, 50200)
    vec = raw_tension_from_array(g["longitudes"][sample], ids)
    for k, row in enumerate(g["longitudes"][sample]):
        scalar = raw_tension_from_longitudes({i: float(v) for i, v in zip(ids, row)})
        assert abs(scalar - vec[k]) < 1e-6
        assert abs(scalar - float(g["raw_scores"][sample][k])) < 0.01  # ruído float32


def test_config_is_the_source_of_truth():
    cfg = load_score_config()
    assert cfg["scoring"]["hard"]["saturn_pluto"] == 260.0
    assert cfg["aspects"]["square"]["orb"] == 3.0


def test_iana_timezone_new_york_2001():
    r = resolve_event_instant("2001-09-11", "08:46", -74.0060, 40.7128)
    assert r["tz_source"] == "iana:America/New_York"
    assert r["utc_offset_hours"] == -4.0  # EDT
    y, m, d, h = swe.revjul(r["tjd_ut"])
    assert (y, m, d) == (2001, 9, 11)
    assert abs(h - (12 + 46 / 60)) < 1e-3


def test_lmt_before_standard_time_and_day_rollover():
    # 1815, Waterloo: LMT exata (4.4° E -> +0.29 h), sem arredondar para o fuso inteiro
    r = resolve_event_instant("1815-06-18", "11:30", 4.4, 50.68)
    assert r["tz_source"] == "lmt"
    assert abs(r["utc_offset_hours"] - 4.4 / 15.0) < 1e-3
    # Virada de dia: 23:30 local em Tóquio (LMT +9.3h) = 14:12 UT do MESMO dia; 01:00 local = dia anterior em UT
    conv = local_to_ut(1850, 1, 10, 1.0, 35.68, 139.69)
    assert (conv["year"], conv["month"], conv["day"]) == (1850, 1, 9)
    conv2 = local_to_ut(2001, 9, 11, 23.0, 40.7128, -74.0060)
    assert (conv2["year"], conv2["month"], conv2["day"]) == (2001, 9, 12)


def test_calendar_region_override():
    # 1752-09-02 em Londres ainda era calendário juliano; na Itália já era gregoriano
    uk = resolve_event_instant("1752-09-02", "desconhecido", -0.12, 51.5, calendar_region="britain")
    it = resolve_event_instant("1752-09-02", "desconhecido", 12.5, 41.9)
    assert uk["calendar"] == "julian"
    assert it["calendar"] == "gregorian"
    assert abs(uk["tjd_ut"] - it["tjd_ut"]) == 11.0


def test_houses_polar_fallback():
    jd = swe.julday(2000, 12, 21, 12.0)
    h = calculate_houses(jd, 78.22, 15.63, True)  # Longyearbyen, Svalbard
    assert h["houses_available"] is True
    assert h["ascendant"] is not None
    assert len(h["cusps"]) >= 12


def test_far_from_ecliptic_star_does_not_score():
    base = {"planets": [], "aspects": [], "star_contacts": []}
    near = dict(base, star_contacts=[{"star_key": "Algol", "body_id": "mars", "orb": 0.0, "near_ecliptic": True}])
    far = dict(base, star_contacts=[{"star_key": "Algol", "body_id": "mars", "orb": 0.0, "near_ecliptic": False}])
    assert calculate_chart_tension_1000(near)["conflict_risk_index_1000"] > 0.0
    assert calculate_chart_tension_1000(far)["conflict_risk_index_1000"] == 0.0
