import pytest
from httpx import ASGITransport, AsyncClient
from src.future_engine import (
    calculate_single_year,
    generate_future_timeline_1800_2100,
    generate_future_timeline_2026_2060
)
from src.web.app import app

def test_single_future_year_2026():
    y2026 = calculate_single_year(2026)
    assert y2026["year"] == 2026
    # Validar escala de 0 a 1000
    assert 0 <= y2026["tension_index_1000"] <= 1000
    assert 0 <= y2026["conflict_risk_index_1000"] <= 1000
    assert 0 <= y2026["tech_innovation_index_1000"] <= 1000
    assert 0 <= y2026["resonance_index"] <= 100
    assert y2026["alert_level"] in [
        "Percentil Superior (P90+)",
        "Percentil Moderado",
        "Percentil Basal",
        # Compatibilidade com labels legados
        "Crítico / Ruptura Histórica",
        "Alto / Tensão Intensa",
        "Moderado / Transição",
        "Estável / Céu Calmo"
    ]
    assert "Plutão" in y2026["cosmic_trigger"]
    assert len(y2026["scenarios_and_possibilities"]) > 50

def test_full_timeline_1800_2100():
    timeline_data = generate_future_timeline_1800_2100(force_refresh=False)
    assert timeline_data["total_years_calculated"] == 301
    assert timeline_data["start_year"] == 1800
    assert timeline_data["end_year"] == 2100
    assert len(timeline_data["timeline"]) == 301

    # Validar continuidade sequencial de 1800 a 2100
    years = [t["year"] for t in timeline_data["timeline"]]
    assert years == list(range(1800, 2101))

    # Validar integração de fatos históricos reais
    assert timeline_data["historical_events_count"] >= 100
    hist_years = [t["year"] for t in timeline_data["timeline"] if t["is_historical"]]
    assert 1914 in hist_years
    assert 1939 in hist_years
    assert 1945 in hist_years
    assert 2001 in hist_years
    assert 2020 in hist_years

    # Validar alta resolução e discrepância dinâmica (diferença nos picos >= 150 pts e médias anuais >= 400 pts)
    tensions = [t["tension_index_1000"] for t in timeline_data["timeline"]]
    min_t = min(tensions)
    max_t = max(tensions)
    assert min_t >= 0.0
    assert max_t <= 1000.0
    assert (max_t - min_t) >= 150.0, f"Discrepância de pico insuficiente: min={min_t}, max={max_t}"

    avg_tensions = [t.get("avg_tension_1000", t["tension_index_1000"]) for t in timeline_data["timeline"]]
    assert (max(avg_tensions) - min(avg_tensions)) >= 400.0, f"Discrepância de média anual insuficiente"

@pytest.mark.anyio
async def test_api_future_timeline():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/api/future-timeline")
        assert res.status_code == 200
        data = res.json()
        assert data["total_years_calculated"] == 301
        assert len(data["timeline"]) == 301

        # Testar se a página web do simulador renderiza o novo gráfico e tabela
        res_page = await ac.get("/simulator")
        assert res_page.status_code == 200
        assert "Linha do Tempo Cosmológica & Simulador (1800–2100)" in res_page.text
        assert "historicalFutureChart" in res_page.text
        assert "timelineTable" in res_page.text
        assert "Escala de Alta Resolução (0 a 1000 Pontos)" in res_page.text
