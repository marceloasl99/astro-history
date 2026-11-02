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
        assert "Catálogo" in res.text
        assert "1.342" in res.text

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
        }, follow_redirects=True)  # v3: POST redireciona para a URL GET compartilhável
        assert res.status_code == 200
        assert "Simulação de Teste Automatizado" in res.text
        assert "/simulator?" in str(res.url) and "date=2026-11-20" in str(res.url)

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
        assert data["total_events"] == 1342
        assert data["calculated_events"] == 1342
        assert data["progress_percent"] == 100.0

        # Methodology page
        res = await ac.get("/methodology")
        assert res.status_code == 200
        assert "Modelos Nulos" in res.text
        assert "CAMINHO A" in res.text

        # Random control comparison API
        res = await ac.get("/api/random-control-comparison/93")
        assert res.status_code == 200
        ctrl_data = res.json()
        assert "random_control_matches" in ctrl_data
        assert "explanation" in ctrl_data

@pytest.mark.anyio
async def test_external_api_access_is_blocked_and_internal_is_allowed():
    """Valida que acessos externos à API via Cloudflare ou IP público são bloqueados (404), enquanto HTML permanece acessível."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        external_headers = {
            "CF-Connecting-IP": "203.0.113.195",
            "CF-Ray": "8da76c891a2b001",
            "CF-IPCountry": "US"
        }

        # 1. Endpoints de documentação Swagger/OpenAPI desabilitados
        res_docs = await ac.get("/docs")
        assert res_docs.status_code == 404

        res_redoc = await ac.get("/redoc")
        assert res_redoc.status_code == 404

        res_openapi = await ac.get("/openapi.json")
        assert res_openapi.status_code == 404

        # 2. Requisições externas a endpoints de API são bloqueadas com 404
        res_api_stats = await ac.get("/api/stats", headers=external_headers)
        assert res_api_stats.status_code == 404

        res_api_events = await ac.get("/api/events", headers=external_headers)
        assert res_api_events.status_code == 404

        res_api_peaks = await ac.get("/api/energy-peaks-2026-2060", headers=external_headers)
        assert res_api_peaks.status_code == 404

        res_api_sim = await ac.post("/api/simulate", json={"date": "2026-11-20"}, headers=external_headers)
        assert res_api_sim.status_code == 404

        # 3. Páginas HTML normais continuam 100% acessíveis externamente
        res_home = await ac.get("/", headers=external_headers)
        assert res_home.status_code == 200

        res_events = await ac.get("/events", headers=external_headers)
        assert res_events.status_code == 200

        res_projections = await ac.get("/projections", headers=external_headers)
        assert res_projections.status_code == 200

        res_simulator = await ac.get("/simulator", headers=external_headers)
        assert res_simulator.status_code == 200

        # 4. Bloqueio de rota de recálculo pesado para tráfego externo
        res_recalc = await ac.post("/simulator/recalculate", headers=external_headers)
        assert res_recalc.status_code == 404

        # 5. Validação de Headers de Segurança (OWASP / Defesa em Profundidade)
        assert res_home.headers.get("x-frame-options") == "SAMEORIGIN"
        assert res_home.headers.get("x-content-type-options") == "nosniff"
        assert "1; mode=block" in res_home.headers.get("x-xss-protection", "")
        assert res_home.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in res_home.headers.get("permissions-policy", "")

        # 6. Teste de IP externo via X-Forwarded-For
        res_xff = await ac.get("/api/stats", headers={"X-Forwarded-For": "198.51.100.25"})
        assert res_xff.status_code == 404
