"""
Testes unitários para o motor de previsão pessoal (2026–2050),
confluências de trânsitos no mapa natal e na progressão secundária,
e novas rotas web do módulo pessoal.
"""

import pytest
from httpx import ASGITransport, AsyncClient

from src.natal.models import BirthInput
from src.natal.service import build_profile, build_progressions, now_jd
from src.natal.personal_forecast import generate_personal_forecast, DOMAIN_TRANSLATIONS, _format_date_pt
from src.natal.web_routes import _biwheel_transits, _calculate_transits_to_progressed
from src.web.app import app

SP1990 = BirthInput(date="1990-05-14", time="08:35", lat=-23.5505, lon=-46.6333, tz="America/Sao_Paulo")


def test_format_date_pt():
    assert _format_date_pt("2026-03-15") == "15/03/2026"
    assert _format_date_pt("") == ""


def test_generate_personal_forecast_structure():
    fc = generate_personal_forecast(SP1990, start_year=2026, end_year=2050)
    assert isinstance(fc, dict)
    assert fc["start_year"] == 2026
    assert fc["end_year"] == 2050
    assert fc["total_years"] == 25
    assert "timeline" in fc
    assert len(fc["timeline"]) == 25  # 2026 to 2050 inclusive
    assert "critical_years" in fc
    assert "domain_translations" in fc
    assert "birth_date" in fc
    assert "current_age" in fc


def test_generate_personal_forecast_years():
    fc = generate_personal_forecast(SP1990, start_year=2026, end_year=2050)
    scores = [y["score_1000"] for y in fc["timeline"]]
    # O gráfico NÃO pode ser uma reta plana
    assert len(set(scores)) > 5, "Scores não devem formar uma reta plana"
    assert not all(s == 350.0 for s in scores), "Scores não devem ser o fallback estático de 350.0"

    for y in fc["timeline"]:
        assert 2026 <= y["year"] <= 2050
        assert "score_1000" in y
        assert 0.0 <= y["score_1000"] <= 1000.0
        assert "impact_level" in y
        assert y["impact_level"] in ["Ponto de Virada", "Alta Ativação", "Moderado", "Estabilidade"]
        assert "top_domain_key" in y
        assert "domains" in y
        for domain_key in DOMAIN_TRANSLATIONS:
            assert domain_key in y["domains"]
            assert 0.0 <= y["domains"][domain_key] <= 1000.0
        assert "events" in y
        assert isinstance(y["events"], list)
        assert len(y["events"]) > 0, f"Ano {y['year']} deve trazer dados de acontecimentos"
        assert "annual_synthesis" in y


def test_generate_personal_forecast_historical_einstein():
    einstein = BirthInput(date="1879-03-14", time="11:30", lat=48.4, lon=9.9833, tz="Europe/Berlin", place="Ulm")
    # Padrão para figura histórica: Auge Adulto (1900–1924)
    fc = generate_personal_forecast(einstein)
    assert fc["is_historical"] is True
    assert fc["start_year"] == 1900
    assert fc["end_year"] == 1924
    assert len(fc["timeline"]) == 25
    scores = [y["score_1000"] for y in fc["timeline"]]
    assert len(set(scores)) > 5, "Scores de Einstein não devem ser uma reta"
    assert all(len(y["events"]) > 0 for y in fc["timeline"]), "Todos os anos devem trazer dados"
    assert len(fc["preset_windows"]) == 4

    # Teste de projeção cósmica para 2026-2050 para Einstein
    fc_future = generate_personal_forecast(einstein, start_year=2026, end_year=2050)
    assert fc_future["start_year"] == 2026
    assert fc_future["end_year"] == 2050
    scores_future = [y["score_1000"] for y in fc_future["timeline"]]
    assert len(set(scores_future)) > 5, "Projeção 2026-2050 para Einstein não deve ser uma reta"
    assert any(len(y["events"]) > 0 for y in fc_future["timeline"]), "Deve conter eventos em 2026-2050"


def test_biwheel_transits_generation():
    profile = build_profile(SP1990)
    ref_jd = now_jd()
    svg = _biwheel_transits(profile["chart"], profile["now"]["active"], SP1990, ref_jd)
    assert isinstance(svg, str)
    assert svg.startswith("<svg")
    assert "</svg>" in svg
    assert "Casas Placidus" in svg


def test_calculate_transits_to_progressed():
    prog = build_progressions(SP1990)
    ref_jd = now_jd()
    hits = _calculate_transits_to_progressed(prog["current"]["bodies"], ref_jd, "pt")
    assert isinstance(hits, list)
    # If there are any transit hits to progressed points
    for hit in hits:
        assert "transit_id" in hit
        assert "progressed_id" in hit
        assert "aspect_name" in hit
        assert "aspect_symbol" in hit
        assert "orb" in hit


@pytest.mark.anyio
async def test_natal_forecast_web_route():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Sem query params -> redireciona amigavelmente para /natal
        res_empty = await ac.get("/natal/forecast", follow_redirects=False)
        assert res_empty.status_code == 303
        assert res_empty.headers["location"] == "/natal"

        # Forecast route with SP1990 query params
        url = "/natal/forecast?date=1990-05-14&time=08:35&lat=-23.5505&lon=-46.6333&place=Sao+Paulo"
        res = await ac.get(url)
        assert res.status_code == 200
        assert "Previsão Pessoal &amp; Ciclos de Vida" in res.text or "Previsão Pessoal & Ciclos de Vida" in res.text
        assert "2026" in res.text
        assert "2050" in res.text
        assert "Radar dos 8 Domínios de Vida" in res.text

        # Forecast route para Einstein (histórico)
        url_einstein = "/natal/forecast?date=1879-03-14&time=11:30&lat=48.4&lon=9.9833&tz=Europe/Berlin&place=Ulm"
        res_einstein = await ac.get(url_einstein)
        assert res_einstein.status_code == 200
        assert "Ciclo Biográfico de Auge" in res_einstein.text
        assert "1900" in res_einstein.text
        assert "1924" in res_einstein.text


@pytest.mark.anyio
async def test_natal_chart_and_progressions_web_routes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Chart route
        url_chart = "/natal/chart?date=1990-05-14&time=08:35&lat=-23.5505&lon=-46.6333&place=Sao+Paulo"
        res_chart = await ac.get(url_chart)
        assert res_chart.status_code == 200
        assert "Natal × Trânsitos Hoje" in res_chart.text
        assert "wheelSelector" in res_chart.text
        assert "view-wheel-transits" in res_chart.text

        # Progressions route
        url_prog = "/natal/progressions?date=1990-05-14&time=08:35&lat=-23.5505&lon=-46.6333&place=Sao+Paulo"
        res_prog = await ac.get(url_prog)
        assert res_prog.status_code == 200
        assert "Confluência Cósmica" in res_prog.text


@pytest.mark.anyio
async def test_natal_saved_people_ui_elements():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Form page has saved people banner and save checkbox
        res_form = await ac.get("/natal")
        assert res_form.status_code == 200
        assert "saved-people-banner" in res_form.text
        assert "save-locally-checkbox" in res_form.text
        assert "natal_saved.js" in res_form.text

        # Chart page has saved people switcher and save button
        url = "/natal/chart?date=1990-05-14&time=08:35&lat=-23.5505&lon=-46.6333&place=Sao+Paulo"
        res_chart = await ac.get(url)
        assert res_chart.status_code == 200
        assert "natal-saved-dropdown-container" in res_chart.text
        assert "btn-save-current-person" in res_chart.text
        assert "natal-saved-dropdown-text" in res_chart.text
