"""Testes do módulo pessoal: carta natal, scanner de trânsitos, ciclos, progressões, domínios e exportações."""
import numpy as np
import pytest
import swisseph as swe

from src.natal.models import BirthInput
from src.natal.chart import calculate_natal_chart, house_of
from src.natal.transits import Targets, scan_transits, lifetime_axis, wrap180, scan_house_ingresses
from src.natal.cycles import label_cycles
from src.natal.domains import classify_windows, monthly_domain_series, annual_totals, scored_series, key_years, point_domain_vector
from src.natal.progressions import progressed_jd, progressed_chart, moon_timeline
from src.natal.exports import ics_calendar, windows_csv
from src.natal.config import natal_config
from src.natal.gazetteer import search_places, available as gaz_available

EINSTEIN = BirthInput(date="1879-03-14", time="11:30", lat=48.4, lon=9.9833, place="Ulm")
SP1990 = BirthInput(date="1990-05-14", time="08:35", lat=-23.5505, lon=-46.6333, tz="America/Sao_Paulo")


@pytest.fixture(scope="module")
def chart_sp():
    return calculate_natal_chart(SP1990)


@pytest.fixture(scope="module")
def scan_sp(chart_sp):
    cfg = natal_config()
    axis = lifetime_axis(chart_sp["tjd_ut"], 100)
    tg = Targets(axis, {k: v for k, v in chart_sp["points"].items() if k in cfg["targets"]["natal_default"]})
    res = scan_transits(tg, birth_jd=chart_sp["tjd_ut"], bodies=cfg["transit_bodies"]["lifetime"])
    classify_windows(res["windows"], {b["id"]: b["house"] for b in chart_sp["bodies"]})
    return axis, res


# ------------------------------------------------------------------ carta natal
def test_einstein_reference_positions():
    """Astrodatabank (AA): Sol 23°30' Peixes, Lua 14°31' Sagitário, ASC 11°38' Câncer (Ulm, 11:30 LMT)."""
    ch = calculate_natal_chart(EINSTEIN)
    assert ch["instant"]["tz_source"] == "lmt"
    bodies = {b["id"]: b for b in ch["bodies"]}
    assert bodies["sun"]["formatted"].startswith("23°30'") and bodies["sun"]["sign_name"] == "Peixes"
    assert bodies["moon"]["formatted"].startswith("14°3") and bodies["moon"]["sign_name"] == "Sagitário"
    assert ch["angles"]["asc"]["formatted"].startswith("11°38'") and ch["angles"]["asc"]["sign_name"] == "Câncer"
    assert ch["houses"]["system"] == "Placidus"


def test_placidus_differs_from_porphyry():
    from src.natal.chart import calculate_houses_system
    p = calculate_houses_system(2407422.95, 48.4, 9.98, "P")
    o = calculate_houses_system(2407422.95, 48.4, 9.98, "O")
    assert p["system"] == "Placidus" and o["system"] == "Porphyry"
    assert abs(p["cusp_degrees"][1] - o["cusp_degrees"][1]) > 1.0
    assert abs(p["angles"]["asc"]["longitude"] - o["angles"]["asc"]["longitude"]) < 1e-6


def test_polar_fallback():
    from src.natal.chart import calculate_houses_system
    h = calculate_houses_system(2451545.0, 78.2, 15.6, "P")  # Svalbard
    assert h["houses_available"] and "fallback" in h["system"]


def test_unknown_time_mode():
    inp = BirthInput(date="1990-05-14", time_known=False, lat=-23.55, lon=-46.63)
    ch = calculate_natal_chart(inp)
    assert ch["precision"] == "unknown_time" and ch["angles"] is None
    assert not ch["houses"]["houses_available"]
    assert 10.0 < ch["moon_range"]["amplitude"] < 16.0
    assert all(b["house"] is None for b in ch["bodies"])


def test_house_of():
    cusps = [float(i * 30) for i in range(12)]
    assert house_of(15.0, cusps) == 1 and house_of(359.9, cusps) == 12 and house_of(30.0, cusps) == 2


def test_dst_and_historical_time(chart_sp):
    # São Paulo em maio de 1990: sem horário de verão → UTC-3
    assert chart_sp["instant"]["utc_offset_hours"] == -3.0
    from src.core.timezones import local_to_ut
    assert local_to_ut(1890, 1, 1, 12.0, -22.9, -43.2)["tz_source"] == "lmt"          # Rio antes de 1914
    assert local_to_ut(1990, 1, 14, 8.5, -23.55, -46.63)["utc_offset_hours"] == -2.0  # DST 1990


# ------------------------------------------------------------------ scanner
def test_wrap180_properties():
    x = np.linspace(-1000, 1000, 5001)
    w = wrap180(x)
    assert np.all(w >= -180) and np.all(w < 180)
    assert np.allclose(np.sin(np.radians(w)), np.sin(np.radians(x)))


def test_scan_counts_and_passes(scan_sp):
    axis, res = scan_sp
    W = res["windows"]
    assert 3000 < len(W) < 8000
    assert all(w["start_jd"] <= w["end_jd"] for w in W)
    assert all(h["jd"] >= w["start_jd"] - 1 and h["jd"] <= w["end_jd"] + 1 for w in W for h in w["hits"])
    bodies = {w["transit_body"] for w in W}
    assert "moon" not in bodies and {"saturn", "pluto", "jupiter"} <= bodies
    assert any(w["n_passes"] >= 2 for w in W if w["transit_body"] in ("saturn", "uranus", "pluto"))


def test_exact_hit_is_exact(scan_sp):
    """Em cada passagem exata, a separação real (Swiss Ephemeris) deve ser ≈ ângulo do aspecto."""
    axis, res = scan_sp
    from src.natal.bodies import SWE_IDS
    checked = 0
    for w in res["windows"]:
        if w["transit_body"] in ("saturn", "jupiter", "pluto") and w["hits"]:
            lon_t = swe.calc_ut(w["hits"][0]["jd"], SWE_IDS[w["transit_body"]])[0][0]
            lon_p = SP1990_POINTS[w["natal_point"]]
            sep = abs(wrap180(lon_t - lon_p))
            target = w["angle"] if w["angle"] <= 180 else 360 - w["angle"]
            assert abs(sep - target) < 0.05, (w["transit_body"], w["aspect"], w["natal_point"], sep)
            checked += 1
            if checked > 60:
                break
    assert checked > 20


SP1990_POINTS = calculate_natal_chart(SP1990)["points"]


def test_orbs_by_body(scan_sp):
    axis, res = scan_sp
    cfg = natal_config()
    for w in res["windows"]:
        base = cfg["transit_orbs"][w["transit_body"]]
        bonus = cfg["target_bonus"].get(w["natal_point"], 0.0)
        assert w["orb_max"] == pytest.approx(base + bonus, abs=0.01)


def test_saturn_return_age(scan_sp):
    axis, res = scan_sp
    cyc = label_cycles(res["windows"])
    sr = [c for c in cyc if c["key"] == "saturn_conjunction" and c["age"] > 1]
    assert sr and 28.5 <= sr[0]["age"] <= 30.5
    uo = [c for c in cyc if c["key"] == "uranus_opposition"]
    assert uo and 39 <= uo[0]["age"] <= 45
    nr = [c for c in cyc if c["key"] == "mean_node_conjunction" and c["age"] > 1]
    assert nr and 17.5 <= nr[0]["age"] <= 19.5


def test_episodes_group_retrograde_passes(scan_sp):
    axis, res = scan_sp
    eps = [e for e in res["episodes"] if e["transit_body"] == "saturn" and e["natal_point"] == "saturn" and e["aspect"] == "conjunction"]
    assert any(e["n_passes"] >= 3 for e in eps)


def test_house_ingresses(chart_sp, scan_sp):
    axis, _ = scan_sp
    hi = scan_house_ingresses(chart_sp["houses"]["cusp_degrees"], axis, ["jupiter", "pluto"], chart_sp["tjd_ut"])
    jup = next(h for h in hi if h["body"] == "jupiter")
    assert 90 <= len(jup["ingresses"]) <= 220
    for g in jup["ingresses"]:
        assert 1 <= g["to_house"] <= 12 and g["to_house"] != g["from_house"]


def test_progressed_mode_targets_move(chart_sp):
    from src.natal.progressions import progressed_series
    axis = lifetime_axis(chart_sp["tjd_ut"], 30)
    ser = progressed_series(chart_sp, SP1990, axis, ["sun", "moon"])
    sun_arc = wrap180(ser["sun"][-1] - ser["sun"][0])
    assert 28 < sun_arc < 32                 # ≈ 1°/ano
    moon_arc = np.degrees(np.unwrap(np.radians(ser["moon"])))[-1] - ser["moon"][0]
    assert 350 < moon_arc < 440              # ≈ 13°/ano → ~1,1 voltas em 30 anos


def test_moon_transits_only_short_range(chart_sp):
    cfg = natal_config()
    axis = lifetime_axis(chart_sp["tjd_ut"], 100, range_from=2026, range_to=2026)
    tg = Targets(axis, {k: chart_sp["points"][k] for k in ("sun", "asc")})
    res = scan_transits(tg, birth_jd=chart_sp["tjd_ut"], bodies=["moon"])
    moon = [w for w in res["windows"] if w["transit_body"] == "moon"]
    assert len(moon) > 20 and all(w["aspect"] in ("conjunction", "opposition") for w in moon)
    axis_long = lifetime_axis(chart_sp["tjd_ut"], 10)
    res2 = scan_transits(Targets(axis_long, {"sun": chart_sp["points"]["sun"]}), birth_jd=chart_sp["tjd_ut"], bodies=["moon"])
    assert "moon_skipped_long_range" in res2["notes"]


# ------------------------------------------------------------------ domínios
def test_domain_vectors_sum_to_one():
    for pid in ("sun", "moon", "asc", "mc", "venus", "pluto"):
        v = point_domain_vector(pid, 10)
        assert abs(sum(v.values()) - 1.0) < 1e-3


def test_monthly_series_and_key_years(scan_sp):
    axis, res = scan_sp
    mo = monthly_domain_series(res["windows"], axis)
    an = annual_totals(mo)
    assert len(mo["months"]) >= 1200 and len(an["years"]) >= 100
    sc = scored_series(mo, an)
    assert all(0 <= v <= 1000 for v in sc["annual_total_1000"])
    ky = key_years(an, sc, res["windows"])
    assert ky and all(k["top"] for k in ky)


# ------------------------------------------------------------------ progressões
def test_progressed_jd_convention(chart_sp):
    b = chart_sp["tjd_ut"]
    assert progressed_jd(b, b + 10 * 365.24219) == pytest.approx(b + 10.0, abs=1e-6)


def test_progressed_chart_and_moon_timeline(chart_sp):
    pc = progressed_chart(chart_sp, SP1990, chart_sp["tjd_ut"] + 36 * 365.24219)
    sun_p = pc["points"]["sun"]
    assert 34 < wrap180(sun_p - chart_sp["points"]["sun"]) < 38
    assert pc["angles"] and pc["angles"]["method"] == "solar_arc"
    axis = lifetime_axis(chart_sp["tjd_ut"], 30)
    mt = moon_timeline(chart_sp, SP1990, axis)
    assert 10 <= len(mt["sign_ingresses"]) <= 15        # ~12 ingressos em 30 anos
    assert all(a["age"] > 0.05 for a in mt["aspects"])


# ------------------------------------------------------------------ exportações e gazetteer
def test_exports(scan_sp):
    axis, res = scan_sp
    W = res["windows"][:50]
    csv = windows_csv(W)
    assert csv.splitlines()[0].startswith("id,transit_body") and len(csv.splitlines()) == 51
    ics = ics_calendar(W, "Teste")
    assert ics.startswith("BEGIN:VCALENDAR") and ics.count("BEGIN:VEVENT") == sum(w["n_passes"] for w in W)
    assert ics.rstrip().endswith("END:VCALENDAR")


@pytest.mark.skipif(not gaz_available(), reason="gazetteer não construído")
def test_gazetteer_search():
    r = search_places("sao paulo", 3)
    assert r and r[0]["name"] == "São Paulo" and r[0]["tz"] == "America/Sao_Paulo"
    assert search_places("Londres", 2)[0]["name"] == "London"


def test_birth_input_roundtrip():
    inp = BirthInput(date="1990-05-14", time="08:35", lat=-23.5505, lon=-46.6333, bodies=["saturn", "pluto"], orbs={"pluto": 1.5})
    q = inp.query_params()
    back = BirthInput.from_query(q)
    assert back == inp
    with pytest.raises(Exception):
        BirthInput(date="1990-13-01", time="08:35", lat=0, lon=0)
    with pytest.raises(Exception):
        BirthInput(date="1990-05-14", time="08:35", lat=0, lon=0, orbs={"pluto": 50})
