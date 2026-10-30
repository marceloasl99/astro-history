"""
Fases 1–3 (v3): features astrológicas, eventos exatos, alvos e API de forecast.
"""

import os
from datetime import date

import numpy as np
import pytest

from src.features.astro_features import load_raw_grid, derive_daily_features, monthly_features, GRID_FILE, BODY_IDS
from src.features.astro_events import exact_aspects, ingresses, eclipses, stations
from src.features.targets import monthly_targets

pytestmark = pytest.mark.skipif(not os.path.exists(GRID_FILE), reason="grade de features não construída (python -m src.features.astro_features)")


def test_feature_grid_shape_and_ranges():
    g = load_raw_grid()
    assert g["lon"].shape[1] == len(BODY_IDS)
    assert np.all((g["lon"] >= 0) & (g["lon"] < 360))
    assert np.all(np.abs(g["dec"]) < 90)
    assert len(g["solar_eclipses"]) > 800 and len(g["lunar_eclipses"]) > 800


def test_derived_features_consistency():
    X, names = derive_daily_features()
    assert X.shape[0] == len(load_raw_grid()["jd"])
    assert len(names) == X.shape[1] == len(set(names))
    col = {n: i for i, n in enumerate(names)}
    # fases: sin² + cos² = 1
    s, c = X[:, col["phase_sin_saturn_pluto"]], X[:, col["phase_cos_saturn_pluto"]]
    assert np.allclose(s ** 2 + c ** 2, 1.0, atol=1e-4)
    # Barbault: soma de 10 separações em [0, 1800]
    assert np.all((X[:, col["barbault_index"]] >= 0) & (X[:, col["barbault_index"]] <= 1800))
    # ativação gaussiana em [0, 1]; Saturno ☌ Plutão em jan/2020 deve estar ativa
    g = load_raw_grid()
    i = np.where((g["ymd"][:, 0] == 2020) & (g["ymd"][:, 1] == 1) & (g["ymd"][:, 2] == 12))[0][0]
    assert X[i, col["asp_saturn_pluto_0"]] > 0.95
    assert not np.isnan(X).any()


def test_monthly_aggregation():
    mf = monthly_features()
    assert mf["X"].shape[0] == len(mf["months"])
    assert mf["months"][0].tolist() == [1750, 1]
    assert mf["months"][-1].tolist() == [2150, 12]
    assert any(n.endswith("_max") for n in mf["names"])


def test_exact_aspect_dates_match_published_ephemerides():
    sp = exact_aspects("saturn", "pluto", 0.0, date(2019, 6, 1), date(2020, 6, 1), step_days=5.0)
    assert len(sp) == 1 and sp[0]["date"] == "2020-01-12"
    sn = exact_aspects("saturn", "neptune", 0.0, date(2025, 1, 1), date(2027, 12, 31), step_days=5.0)
    assert [e["date"] for e in sn] == ["2026-02-20"]
    assert sn[0]["pass_number"] == 1 and sn[0]["total_passes"] == 1


def test_ingresses_stations_eclipses():
    pl = ingresses("pluto", date(2024, 1, 1), date(2024, 12, 31))
    assert [p["date"] for p in pl] == ["2024-01-21", "2024-09-01", "2024-11-19"]
    assert pl[1]["retrograde"] is True
    ecl = eclipses(date(2024, 1, 1), date(2024, 12, 31))
    assert [(e["date"], e["type"], e["kind"]) for e in ecl if e["type"] == "solar"] == [("2024-04-08", "solar", "total"), ("2024-10-02", "solar", "anular")]
    st = stations("mars", date(2024, 11, 1), date(2025, 3, 31))
    assert [s["kind"] for s in st] == ["retrógrada", "direta"]


def test_targets_coverage_and_rates():
    T = monthly_targets()
    for name in ("cow_war_onset", "nber_recession", "ucdp_onset_any", "v2_any"):
        assert name in T.targets
        m = T.mask(name)
        assert 0 < T.targets[name][m].mean() < 1
    # Grande Depressão: set/1929 é pico NBER -> out/1929 em recessão
    i = T._idx(1929, 10)
    assert T.targets["nber_recession"][i] == 1.0
    assert T.targets["nber_recession"][T._idx(1929, 8)] == 0.0
    # 1ª Guerra Mundial: início em jul/ago 1914 no COW
    assert T.targets["cow_war_onset"][T._idx(1914, 7)] + T.targets["cow_war_onset"][T._idx(1914, 8)] >= 1.0


@pytest.mark.anyio
async def test_forecast_api_routes():
    import httpx
    from src.web.app import app
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/forecast")
        assert r.status_code == 200
        r = await client.get("/api/forecast")
        assert r.status_code in (200, 503)
        if r.status_code == 200:
            body = r.json()
            assert "targets" in body and "calendar" not in body
            tname = next(iter(body["targets"]))
            r2 = await client.get(f"/api/forecast?target={tname}")
            assert r2.status_code == 200 and "years" in r2.json()
            r3 = await client.get("/api/forecast/year/2032")
            assert r3.status_code == 200 and "calendar" in r3.json()
