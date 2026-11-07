import pytest
from fastapi.testclient import TestClient
from src.web.app import app

client = TestClient(app)

def test_static_themes_css():
    response = client.get("/static/css/themes.css")
    assert response.status_code == 200
    css = response.text
    assert "theme-light" in css
    assert "theme-oled" in css
    assert "theme-dark" in css
    assert "#000000" in css
    assert ".theme-btn" in css
    assert ".lang-btn" in css
    assert ".nav-submenu-item" in css
    assert ".nav-submenu-item:hover" in css
    assert ".nav-group-menu.hidden" in css
    assert "display: none !important" in css
    assert "#nav-mobile" in css

def test_static_i18n_js():
    response = client.get("/static/js/i18n.js")
    assert response.status_code == 200
    js = response.text
    assert "setLanguage" in js
    assert "setTheme" in js
    assert "syncChartThemes" in js
    assert "translations" in js
    assert "Guerra & Conflito" in js
    assert "War & Conflict" in js
    assert "let currentTheme = localStorage.getItem('astro_theme') || 'light'" in js
    assert '"Explorar": "Explore"' in js
    assert '"Mapa Natal": "Natal Chart"' in js
    assert '"Pessoas Cadastradas": "Saved Profiles"' in js

def test_base_html_renders_theme_and_lang_controls():
    response = client.get("/")
    assert response.status_code == 200
    html = response.text
    assert 'class="theme-light"' in html
    assert "savedTheme = localStorage.getItem('astro_theme') || 'light'" in html
    assert "/static/css/themes.css" in html
    assert "/static/js/i18n.js" in html
    assert 'data-theme="light"' in html
    assert 'data-theme="dark"' in html
    assert 'data-theme="oled"' in html
    assert 'data-lang="pt"' in html
    assert 'data-lang="en"' in html
    assert "nav-submenu-item" in html
    assert 'id="global-search"' not in html
    assert 'id="nav-desktop"' in html
    assert 'hidden lg:flex' in html
    assert 'id="nav-toggle"' in html
    assert 'id="nav-mobile"' in html
    # Ensure nav bar contains no search input
    nav_html = html.split('<nav')[1].split('</nav>')[0]
    assert 'type="search"' not in nav_html
    assert 'action="/search"' not in nav_html
    assert "Resumo Prospectivo: Picos de Energia Cósmica" in html
    assert "Total de Picos" in html

def test_simulator_alerta_column_styling():
    response = client.get("/simulator")
    assert response.status_code == 200
    html = response.text
    assert 'min-w-[130px] whitespace-nowrap text-center">Alerta<' in html
    assert "whitespace-nowrap text-center align-middle" in html
    assert "leading-normal whitespace-nowrap" in html

def test_projections_page_renders_cleanly():
    response = client.get("/projections")
    assert response.status_code == 200
    html = response.text
    assert "Percentil Anual" in html
    assert "whitespace-nowrap" in html
    assert "Picos de Energia" in html
    assert "148 Picos Mapeados" in html

    # Test internal API endpoint (allowed for testclient / localhost)
    api_res = client.get("/api/energy-peaks-2026-2060")
    assert api_res.status_code == 200
    api_data = api_res.json()
    assert api_data["total"] >= 140
    assert len(api_data["peaks"]) >= 140
    assert api_data["peaks"][0]["year"] == 2026

def test_footer_version_and_no_v2_v3_mentions():
    # Footer version (v7)
    res_home = client.get("/")
    assert res_home.status_code == 200
    assert "v7.0.1" in res_home.text
    assert "Previsão v3" not in res_home.text

    # Forecast page has no v3 in title or heading
    res_forecast = client.get("/forecast")
    assert res_forecast.status_code == 200
    assert "Previsão Probabilística v3" not in res_forecast.text
    assert "Previsão Probabilística" in res_forecast.text

    # Methodology page has no v2 in heading
    res_meth = client.get("/methodology")
    assert res_meth.status_code == 200
    assert "Validação Científica v2" not in res_meth.text
    assert "Validação Científica" in res_meth.text


def test_pessoal_submenu_single_active_item():
    """Garante que no menu superior 'Pessoal', apenas o item ativo recebe 'active-item' (e nunca todas as opções)."""
    res = client.get("/natal")
    assert res.status_code == 200
    html = res.text

    # No menu desktop de Pessoal
    assert 'class="nav-submenu-item active-item" aria-current="page">\n                            <span class="item-title">Mapa Natal</span>' in html
    # Os outros itens do submenu não devem ter 'active-item'
    assert 'href="/natal#saved-people-banner" class="nav-submenu-item " aria-current="false"' in html
    assert 'href="/natal#trânsitos" class="nav-submenu-item " aria-current="false"' in html
    assert 'href="/natal#progressões" class="nav-submenu-item " aria-current="false"' in html
    assert 'href="/natal#previsao" class="nav-submenu-item " aria-current="false"' in html


def test_static_cache_control_and_compiled_tailwind():
    """Garante que o Tailwind estático compilado é servido com Cache-Control e substitui o Play CDN."""
    res_tw = client.get("/static/css/tailwind.min.css")
    assert res_tw.status_code == 200
    assert "public, max-age=" in res_tw.headers.get("Cache-Control", "")
    assert len(res_tw.text) > 10000

    res_th = client.get("/static/css/themes.css")
    assert res_th.status_code == 200
    assert "public, max-age=" in res_th.headers.get("Cache-Control", "")

    res_home = client.get("/")
    assert "/static/css/tailwind.min.css" in res_home.text
    assert "cdn.tailwindcss.com" not in res_home.text


