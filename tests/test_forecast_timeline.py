"""
Testes unitários para o motor unificado de linha do tempo mundana (2026–2060).
Valida consolidação de picos de energia, pontuações (0–1000), categorias canônicas
e integridade de dados para a interface de forecast.
"""

import pytest
from src.analysis.forecast_timeline import (
    build_unified_forecast_data,
    load_categories_meta,
    _format_date_pt,
)


def test_format_date_pt():
    assert _format_date_pt("2026-02-27") == "27/02/2026"
    assert _format_date_pt("2030-11-05") == "05/11/2030"
    assert _format_date_pt("") == ""
    assert _format_date_pt("invalid") == "invalid"


def test_load_categories_meta():
    meta = load_categories_meta()
    assert isinstance(meta, dict)
    # Check that canonical categories exist
    expected_keys = ["WAR_CONFLICT", "REGIME_CRISIS", "ECONOMIC_CRASH"]
    for k in expected_keys:
        assert k in meta, f"Categoria canônica esperada {k} não encontrada nos metadados"
        assert "label_pt" in meta[k]
        assert "theme_color" in meta[k]
        assert "icon" in meta[k]


def test_build_unified_forecast_data_structure():
    data = build_unified_forecast_data()
    assert isinstance(data, dict)
    assert "years" in data
    assert "kpis" in data
    assert "categories_meta" in data
    assert "targets" in data

    kpis = data["kpis"]
    assert kpis["start_year"] == 2026
    assert kpis["end_year"] == 2060
    assert kpis["total_years"] == 35

    years = data["years"]
    assert len(years) == 35  # 2026 to 2060 inclusive
    assert years[0]["year"] == 2026
    assert years[-1]["year"] == 2060

    # Total peaks should be at least 140 (catalog has 148 peaks)
    assert kpis["total_peaks"] >= 140


def test_year_structure_and_scores():
    data = build_unified_forecast_data()
    for y in data["years"]:
        assert "year" in y
        assert 2026 <= y["year"] <= 2060
        assert "tension_score_1000" in y
        assert 0.0 <= y["tension_score_1000"] <= 1000.0
        assert "alert_level" in y
        assert y["alert_level"] in ["Crítico", "Alto", "Moderado", "Estável"]
        assert "alert_color" in y
        assert "peaks" in y
        assert isinstance(y["peaks"], list)

        # 2026 is the primary conjunction Saturn-Neptune
        if y["year"] == 2026:
            assert y["alert_level"] == "Crítico"
            assert y["tension_score_1000"] >= 900.0
            assert "Saturno" in y["cosmic_trigger"] or "Netuno" in y["cosmic_trigger"]


def test_peaks_attributes():
    data = build_unified_forecast_data()
    all_peaks = []
    for y in data["years"]:
        all_peaks.extend(y["peaks"])

    assert len(all_peaks) == data["kpis"]["total_peaks"]

    # Inspect each peak
    for p in all_peaks:
        assert "peak_date" in p
        assert "formatted_date" in p
        assert "/" in p["formatted_date"]
        assert "energy_score_1000" in p
        assert 0.0 <= p["energy_score_1000"] <= 1000.0
        assert "category_key" in p
        assert "category_label" in p
        assert "cosmic_signature" in p


@pytest.mark.anyio
async def test_forecast_page_renders_clean_years_without_fake_dates():
    from httpx import ASGITransport, AsyncClient
    from src.web.app import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/forecast")
        assert res.status_code == 200
        # Check that fake sampling date 01/07/ANO is NOT in the page
        assert "01/07/" not in res.text
        assert "Data de Pico Anual:" not in res.text
        # Check that years, categories, and scores are present
        assert "2026" in res.text
        assert "2060" in res.text
        assert "Cenários Projetados &amp; Vetores Estratégicos" in res.text or "Cenários Projetados & Vetores Estratégicos" in res.text
        assert "Score de Tensão:" in res.text
        assert "Score de Intensidade:" in res.text
