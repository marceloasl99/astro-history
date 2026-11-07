"""
Suíte de testes de validação de Segurança, Hardening de APIs e Otimização SEO.
Audita o bloqueio estrito de todas as APIs para chamadas externas, cabeçalhos OWASP/CSP,
métodos permitidos, robots.txt e sitemap.xml.
"""

import pytest
import xml.etree.ElementTree as ET
from httpx import AsyncClient, ASGITransport
from src.web.app import app

EXTERNAL_HEADERS = {
    "CF-Connecting-IP": "198.51.100.42",
    "CF-Ray": "9ea87bc1001",
    "CF-IPCountry": "BR"
}

@pytest.mark.anyio
async def test_seo_sitemap_xml():
    """Valida que /sitemap.xml é gerado corretamente no protocolo padrão sitemaps.org."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/sitemap.xml", headers=EXTERNAL_HEADERS)
        assert res.status_code == 200
        assert "application/xml" in res.headers["content-type"]
        assert "public, max-age=" in res.headers.get("cache-control", "")

        # Validar integridade XML
        root = ET.fromstring(res.text)
        assert "urlset" in root.tag
        assert len(root) > 100  # Contém rotas principais, 107 países e eventos

        # Validar presença de URLs canônicas esperadas
        urls = [elem.find("{http://www.sitemaps.org/schemas/sitemap/0.9}loc").text for elem in root]
        assert "https://history.skyastrum.com/" in urls
        assert "https://history.skyastrum.com/events" in urls
        assert "https://history.skyastrum.com/simulator" in urls
        assert "https://history.skyastrum.com/projections" in urls
        assert "https://history.skyastrum.com/countries/BRA" in urls
        assert "https://history.skyastrum.com/countries/USA" in urls


@pytest.mark.anyio
async def test_seo_robots_txt():
    """Valida que /robots.txt protege endpoints de API e aponta para o sitemap."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/robots.txt", headers=EXTERNAL_HEADERS)
        assert res.status_code == 200
        assert "text/plain" in res.headers["content-type"]
        body = res.text
        assert "User-agent: *" in body
        assert "Disallow: /api/" in body
        assert "Disallow: /simulator/recalculate" in body
        assert "Sitemap: https://history.skyastrum.com/sitemap.xml" in body


@pytest.mark.anyio
async def test_all_external_apis_are_strictly_closed():
    """Garante que TODAS as APIs de dados, análogos, simulações e documentações são bloqueadas para tráfego externo."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        blocked_endpoints = [
            ("GET", "/api/stats"),
            ("GET", "/api/events"),
            ("GET", "/api/events/100"),
            ("GET", "/api/future-timeline"),
            ("GET", "/api/projections-2027-2060"),
            ("GET", "/api/energy-peaks-2026-2060"),
            ("GET", "/api/forecast"),
            ("GET", "/api/forecast/year/2026"),
            ("GET", "/api/historical-analogues"),
            ("GET", "/api/features/barbault"),
            ("GET", "/api/features/oshop"),
            ("GET", "/api/countries"),
            ("GET", "/api/countries/BRA"),
            ("GET", "/api/countries/BRA/chart"),
            ("GET", "/api/countries/BRA/transits"),
            ("GET", "/api/natal/chart"),
            ("GET", "/api/natal/transits"),
            ("GET", "/api/natal/progressions"),
            ("POST", "/api/simulate"),
            ("POST", "/simulator/recalculate"),
            ("GET", "/docs"),
            ("GET", "/redoc"),
            ("GET", "/openapi.json"),
            ("GET", "/web/index.html"),
        ]

        for method, endpoint in blocked_endpoints:
            if method == "POST":
                res = await ac.post(endpoint, headers=EXTERNAL_HEADERS, json={})
            else:
                res = await ac.get(endpoint, headers=EXTERNAL_HEADERS)
            assert res.status_code == 404, f"Endpoint {endpoint} deveria estar fechado com 404, mas retornou {res.status_code}"


@pytest.mark.anyio
async def test_security_headers_and_csp():
    """Valida a presença de todos os cabeçalhos de defesa em profundidade recomendados pela auditoria de segurança."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/", headers=EXTERNAL_HEADERS)
        assert res.status_code == 200

        # OWASP Core Headers
        assert res.headers.get("x-frame-options") == "SAMEORIGIN"
        assert res.headers.get("x-content-type-options") == "nosniff"
        assert "1; mode=block" in res.headers.get("x-xss-protection", "")
        assert res.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
        assert "camera=()" in res.headers.get("permissions-policy", "")
        assert "max-age=31536000" in res.headers.get("strict-transport-security", "")
        assert res.headers.get("cross-origin-opener-policy") == "same-origin"
        assert res.headers.get("cross-origin-resource-policy") == "same-origin"

        # Content-Security-Policy (Restrito a 'self' já que todos os assets são locais)
        csp = res.headers.get("content-security-policy", "")
        assert "default-src 'self'" in csp
        assert "script-src 'self'" in csp
        assert "style-src 'self'" in csp

        # Server Signature Masking
        assert res.headers.get("server") == "AstroHistory-Engine"


@pytest.mark.anyio
async def test_disallowed_http_methods_and_payload_limits():
    """Valida rejeição de métodos perigosos (TRACE, TRACK) e payloads excessivos."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Método não permitido
        res_trace = await ac.request("TRACE", "/", headers=EXTERNAL_HEADERS)
        assert res_trace.status_code == 405

        # Payload excessivo (> 2 MB)
        res_payload = await ac.post("/simulator", headers={**EXTERNAL_HEADERS, "Content-Length": "5000000"})
        assert res_payload.status_code == 413


@pytest.mark.anyio
async def test_country_detail_and_gazetteer_safety():
    """Valida segurança na visualização de países e na busca de locais (prevenção XSS e FTS5)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Página de país válida
        res_bra = await ac.get("/countries/BRA", headers=EXTERNAL_HEADERS)
        assert res_bra.status_code == 200
        assert "Brasil" in res_bra.text
        # Garantir que script tags não contenham unescaped raw characters
        assert "</script><script>" not in res_bra.text

        # FTS5 search com caracteres especiais
        res_search = await ac.get("/natal/places?q=S%C3%A3o%20Paulo*%22%27%3B--", headers=EXTERNAL_HEADERS)
        assert res_search.status_code == 200
        data = res_search.json()
        assert "results" in data


@pytest.mark.anyio
async def test_trusted_host_protection():
    """Valida bloqueio de cabeçalhos Host não autorizados (proteção Host Header Injection)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Host legítimo
        res_ok = await ac.get("/", headers={**EXTERNAL_HEADERS, "host": "history.skyastrum.com"})
        assert res_ok.status_code == 200

        # Host malicioso
        res_bad = await ac.get("/", headers={**EXTERNAL_HEADERS, "host": "attacker-domain.evil"})
        assert res_bad.status_code == 400


@pytest.mark.anyio
async def test_enhanced_csp_and_owasp_headers():
    """Valida extensões de CSP e novos cabeçalhos de defesa OWASP."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/", headers=EXTERNAL_HEADERS)
        assert res.status_code == 200

        csp = res.headers.get("content-security-policy", "")
        assert "object-src 'none'" in csp
        assert "upgrade-insecure-requests" in csp
        assert "worker-src 'self' blob:" in csp
        assert "media-src 'self'" in csp

        assert res.headers.get("x-permitted-cross-domain-policies") == "none"
        assert res.headers.get("x-download-options") == "noopen"


@pytest.mark.anyio
async def test_static_files_directory_traversal_and_extension_block():
    """Valida que dotfiles, arquivos sensíveis (.env, .py, .db) e path traversal em /static/ retornam 404."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Dotfile oculto
        res1 = await ac.get("/static/.env", headers=EXTERNAL_HEADERS)
        assert res1.status_code == 404

        # Arquivo de código fonte
        res2 = await ac.get("/static/app.py", headers=EXTERNAL_HEADERS)
        assert res2.status_code == 404

        # Path traversal
        res3 = await ac.get("/static/../../src/web/app.py", headers=EXTERNAL_HEADERS)
        assert res3.status_code == 404


@pytest.mark.anyio
def test_sqlite_trusted_schema_disabled():
    """Garante que PRAGMA trusted_schema está desativado (prevenção contra ataques via triggers/schema)."""
    from src.db import get_connection
    conn = get_connection()
    try:
        val = conn.execute("PRAGMA trusted_schema;").fetchone()[0]
        assert val == 0, f"PRAGMA trusted_schema deveria ser 0, mas é {val}"
    finally:
        conn.close()


@pytest.mark.anyio
async def test_external_rate_limiter():
    """Valida que o rate limiter global bloqueia requisições abusivas originadas de IPs externos."""
    from src.web.app import _GLOBAL_RATE_LIMITER
    test_ip = "203.0.113.99"
    # Esgotar quota do IP de teste
    for _ in range(180):
        _GLOBAL_RATE_LIMITER.allow(test_ip, max_per_minute=180)

    abuse_headers = {
        "CF-Connecting-IP": test_ip,
        "CF-Ray": "abuse-test-1"
    }

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res = await ac.get("/", headers=abuse_headers)
        assert res.status_code == 429
        assert "Rate limit exceeded" in res.json().get("detail", "")
        assert res.headers.get("retry-after") == "60"

