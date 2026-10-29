import pytest
from httpx import ASGITransport, AsyncClient
from src.web.app import app

@pytest.mark.anyio
async def test_api_routes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Home page
        res = await ac.get("/")
        assert res.status_code == 200
        assert "AstroHistory" in res.text

        # Events catalog
        res = await ac.get("/events")
        assert res.status_code == 200
        assert "Catálogo dos 300 Fatos" in res.text

        # Event detail (1929 Crash #93)
        res = await ac.get("/events/93")
        assert res.status_code == 200
        assert "Crash da Bolsa de Nova York" in res.text
        assert "Mandala Zodiacal" in res.text

        # Correlations hub
        res = await ac.get("/correlations")
        assert res.status_code == 200
        assert "Hub de Correlações" in res.text

        # Simulator GET
        res = await ac.get("/simulator")
        assert res.status_code == 200

        # Simulator POST
        res = await ac.post("/simulator", data={
            "title": "Simulação de Teste Automatizado",
            "date": "2026-11-20",
            "time": "14:00",
            "city": "Brasília",
            "country": "Brasil",
            "latitude": -15.79,
            "longitude": -47.88
        })
        assert res.status_code == 200
        assert "Simulação de Teste Automatizado" in res.text

        # Projections 2027-2060 page
        res = await ac.get("/projections")
        assert res.status_code == 200
        assert "Cenários &amp; Portais Cósmicos (2027–2060)" in res.text or "Cenários" in res.text
        assert "2027" in res.text
        assert "2060" in res.text

        # Projections 2027-2060 API
        res = await ac.get("/api/projections-2027-2060")
        assert res.status_code == 200
        proj_data = res.json()
        assert proj_data["total_years"] == 34
        assert len(proj_data["projections"]) == 34
        assert proj_data["projections"][0]["year"] == 2027
        assert proj_data["projections"][-1]["year"] == 2060
        assert "peak_date" in proj_data["projections"][0]
        assert len(proj_data["projections"][0]["seasonal_gates"]) == 4

        # JSON API stats
        res = await ac.get("/api/stats")
        assert res.status_code == 200
        data = res.json()
        assert data["total_events"] == 300
        assert data["calculated_events"] == 300
        assert data["progress_percent"] == 100.0
