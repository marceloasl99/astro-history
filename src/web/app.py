"""
Aplicação Web FastAPI rodando na porta 81 (0.0.0.0:81).
Oferece o Dashboard completo de Astrologia Moderna com os 3.406 marcos históricos mundiais,
visualização de mapas astrais em mandala SVG e simulador de correlações futuras.
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, PlainTextResponse, Response
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os
import json

from src.web.seo import build_sitemap_xml, get_robots_txt

from src.db import (
    get_events_stats,
    get_all_events,
    get_event_by_id,
    init_db,
    get_connection,
    get_validated_sample_dates
)
from src.astro_engine import calculate_event_chart
from src.correlation_engine import get_category_correlations, find_similar_events
from src.web.mandala import generate_mandala_svg
from src.analyze_correlations import calculate_event_emphasis
from src.future_engine import (
    generate_future_timeline_1800_2100,
    generate_future_timeline_2026_2060,
    get_projections_2027_2060
)
from src.analysis.forecast_v3 import load_forecast
from src.analysis.forecast_timeline import build_unified_forecast_data
from src.mundane.energy_peaks import load_energy_peaks_catalog

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

import ipaddress

app = FastAPI(
    title="AstroHistory - Astrologia Moderna & 3.406 Fatos Históricos Mundiais",
    description="Plataforma Internacional de Correlação Astrológica Histórica com Swiss Ephemeris",
    version="7.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan
)

def _is_internal_client(request: Request) -> bool:
    """
    Verifica se a requisição originou-se estritamente de processo local (loopback ou testclient).
    Qualquer requisição com headers de proxy externo (Cloudflare, XFF externo) ou IP não-loopback
    é tratada como externa.
    """
    # 1. Cloudflare Proxy Headers (sempre externo quando presente)
    for cf_header in ("cf-connecting-ip", "cf-ray", "cf-ipcountry", "cf-visitor"):
        if request.headers.get(cf_header):
            return False

    # 2. Headers de proxy / encaminhamento
    for h in ("x-forwarded-for", "x-real-ip", "forwarded", "x-client-ip"):
        val = request.headers.get(h)
        if val:
            for part in val.split(","):
                p = part.strip()
                if p not in ("testclient", "localhost", "127.0.0.1", "::1", "testserver"):
                    try:
                        ip = ipaddress.ip_address(p)
                        if not ip.is_loopback:
                            return False
                    except ValueError:
                        return False

    # 3. Direct client connection host
    client_host = request.client.host if request.client else "127.0.0.1"
    if client_host in ("testclient", "localhost", "127.0.0.1", "::1", "testserver"):
        return True

    try:
        ip = ipaddress.ip_address(client_host)
        return ip.is_loopback
    except ValueError:
        return False

def _is_external_request(request: Request) -> bool:
    """Compatibilidade reversa: retorna True se não for cliente estritamente interno."""
    return not _is_internal_client(request)

@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Adiciona headers de segurança recomendados (OWASP / Defesa em Profundidade / Cloudflare)."""
    # 1. Validação de métodos HTTP permitidos
    if request.method not in ("GET", "POST", "HEAD", "OPTIONS"):
        return JSONResponse(status_code=405, content={"detail": "Method Not Allowed"})

    # 2. Limite de tamanho de payload (máximo 2 MB para prevenir ataques DoS / buffer exhaustion)
    content_length = request.headers.get("content-length")
    if content_length:
        try:
            if int(content_length) > 2 * 1024 * 1024:
                return JSONResponse(status_code=413, content={"detail": "Payload Too Large"})
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid Content-Length"})

    response = await call_next(request)
    
    # Headers OWASP
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(), payment=()"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
    response.headers["Cross-Origin-Resource-Policy"] = "same-origin"
    
    # Content-Security-Policy (CSP) Restritivo:
    # Fontes, Tailwind e Chart.js são 100% locais em /static/. Scripts e estilos externos são bloqueados.
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "font-src 'self' data:; "
        "img-src 'self' data: blob:; "
        "connect-src 'self'; "
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "form-action 'self';"
    )

    # Mascarar assinatura do servidor Uvicorn para proteção de inventário
    response.headers["Server"] = "AstroHistory-Engine"

    return response

@app.middleware("http")
async def block_external_api_middleware(request: Request, call_next):
    """
    Bloqueia todo acesso a endpoints de API, Swagger, OpenAPI e recálculo pesado para tráfego externo.
    Acesso permitido estritamente de forma interna (localhost e testes in-process).
    """
    path = request.url.path
    is_restricted_path = (
        path.startswith("/api/")
        or path == "/api"
        or path.startswith("/docs")
        or path.startswith("/redoc")
        or path == "/openapi.json"
        or path == "/simulator/recalculate"
        or path.startswith("/web")
    )

    if is_restricted_path and not _is_internal_client(request):
        return JSONResponse(
            status_code=404,
            content={"detail": "Not Found"}
        )

    return await call_next(request)

class SimulationInput(BaseModel):
    """Entrada validada do simulador (API e formulário)."""
    title: str = Field(default="Simulação", max_length=200)
    date: str = Field(pattern=r"^-?\d{1,4}-\d{2}-\d{2}$", description="YYYY-MM-DD")
    time: str = Field(default="12:00", max_length=12)
    city: str = Field(default="", max_length=120)
    country: str = Field(default="", max_length=120)
    latitude: float = Field(default=0.0, ge=-90.0, le=90.0)
    longitude: float = Field(default=0.0, ge=-180.0, le=180.0)

def _mark_validated(events: list) -> list:
    validated = get_validated_sample_dates()
    for e in events:
        e["in_validated_sample"] = e.get("date") in validated
    return events

# Configuração de templates e estáticos
TEMPLATES_DIR = os.path.join(BASE_DIR, "src", "web", "templates")
STATIC_DIR = os.path.join(BASE_DIR, "src", "web", "static")
WEB_DIR = os.path.join(BASE_DIR, "web")

from src.web.templating import templates  # v6: instância única com filtros/globais

class CachedStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        if response.status_code == 200:
            response.headers["Cache-Control"] = "public, max-age=86400, stale-while-revalidate=604800"
        return response

if os.path.exists(STATIC_DIR):
    app.mount("/static", CachedStaticFiles(directory=STATIC_DIR), name="static")
if os.path.exists(WEB_DIR):
    app.mount("/web", CachedStaticFiles(directory=WEB_DIR, html=True), name="web")

def build_chart_series(future_data: dict) -> dict:
    """Séries 1800–2100 (escala 0–1000) para o Chart.js do dashboard, simulador e linha do tempo."""
    tl = future_data["timeline"]

    def extract_year_title(t: dict) -> str:
        events = t.get("historical_events", [])
        if not events:
            return ""

        # Priorizar marcos bélicos e históricos monumentais (Segunda Guerra, Hiroshima, Pearl Harbor, etc.)
        def event_priority(e: dict) -> int:
            title = e.get("title", "").lower()
            if "hiroshima" in title or "segunda guerra" in title:
                return 0
            if "pearl harbor" in title or "dia d" in title or "stalingrado" in title or "nuclear" in title:
                return 1
            if "guerra mundial" in title or "auschwitz" in title or "berlim" in title or "crash" in title:
                return 2
            if e.get("category") == "Guerra & Conflito":
                return 3
            if e.get("category") == "Crise Financeira & Econômica":
                return 4
            return 5

        sorted_events = sorted(events, key=event_priority)
        titles = [e["title"] for e in sorted_events]
        if len(titles) <= 3:
            return " • ".join(titles)
        return " • ".join(titles[:3]) + f" (+{len(titles)-3} outros)"

    def extract_top_event(t: dict) -> str:
        events = t.get("historical_events", [])
        if events:
            return extract_year_title(t)
        top_matches = t.get("top_matches", [])
        return top_matches[0]["title"] if top_matches else ""

    return {
        "years": [t["year"] for t in tl],
        "tension_1000": [t["tension_index_1000"] for t in tl],
        "avg_tension_1000": [t["avg_tension_1000"] for t in tl],
        "conflict_risk_1000": [t["conflict_risk_index_1000"] for t in tl],
        "crisis_risk_1000": [t["crisis_risk_index_1000"] for t in tl],
        "tech_innovation_1000": [t["tech_innovation_index_1000"] for t in tl],
        "barbault_1000": [t.get("barbault_concentration_1000", 0.0) for t in tl],
        "is_historical": [t["year"] < 2026 for t in tl],
        "has_historical_events": [len(t.get("historical_events", [])) > 0 for t in tl],
        "hist_events_count": [len(t.get("historical_events", [])) for t in tl],
        "hist_titles": [extract_year_title(t) for t in tl],
        "hist_ids": [t["historical_events"][0]["id"] if t.get("historical_events") else None for t in tl],
        "triggers": [t["cosmic_trigger"] for t in tl],
        "top_events": [extract_top_event(t) for t in tl],
    }

# --- Rotas HTML ---

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def index_view(request: Request):
    stats = get_events_stats()
    # Eventos em destaque paradigmáticos (Segunda Guerra Mundial, Hiroshima, Crash de 1929, Apollo 11, etc.)
    from src.db import get_featured_events
    featured_events = get_featured_events([100, 107, 93, 134, 156, 171])

    # Carregar dados da linha do tempo contínua 1800-2100 na escala 0-1000
    future_data = generate_future_timeline_1800_2100(force_refresh=False)
    chart_series = build_chart_series(future_data)

    try:
        from src.analysis.annual_indices import build as build_annual_indices
        annual_indices = build_annual_indices()
    except Exception:
        annual_indices = None
    forecast = load_forecast()
    forecast_summary = None
    if forecast:
        forecast_summary = [
            {"key": k, "label": v["label"], "bss": v["skill"].get("bss"), "verdict": v["skill"].get("verdict"), "model": v["model"]}
            for k, v in forecast["targets"].items()
        ]
    peaks_catalog = load_energy_peaks_catalog()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "stats": stats,
            "featured_events": featured_events,
            "future_data": future_data,
            "chart_series": chart_series,
            "forecast_summary": forecast_summary,
            "annual_indices": annual_indices,
            "peaks_catalog": peaks_catalog
        }
    )

@app.api_route("/sitemap.xml", methods=["GET", "HEAD"])
async def sitemap_xml_view():
    """Gera o sitemap XML oficial (protocolo sitemaps.org) com todas as páginas, países e marcos."""
    return Response(
        content=build_sitemap_xml(),
        media_type="application/xml; charset=utf-8",
        headers={"Cache-Control": "public, max-age=86400, stale-while-revalidate=604800"}
    )

@app.api_route("/robots.txt", methods=["GET", "HEAD"])
async def robots_txt_view():
    """Retorna diretivas de indexação para robôs de busca e ponteiro para o sitemap."""
    return PlainTextResponse(
        content=get_robots_txt(),
        headers={"Cache-Control": "public, max-age=86400"}
    )

@app.get("/events", response_class=HTMLResponse)
async def events_catalog_view(request: Request, category: str = "Todas", search: str = "", validated: int = 0,
                              macro: str = "", tier: str = "", precision: str = "", polarity: str = "", country: str = "",
                              century: Optional[int] = None, time_known: Optional[int] = None, sort: str = "date",
                              page: int = 1, per_page: int = 50):
    """Catálogo facetado e paginado (v6). Mantém os parâmetros legados category/search/validated."""
    from src.db import get_events_page
    import yaml as _yaml
    per_page = max(10, min(per_page, 200))
    filters = dict(category=category if category != "Todas" else None, search=search or None, macro=macro or None,
                   tier=tier or None, precision=precision or None, polarity=polarity or None, country=country or None,
                   century_from=century if century is not None else None,
                   century_to=(century + 99) if century is not None else None,
                   time_known=(bool(time_known) if time_known is not None else None))
    if validated:
        # Track B: filtra em memória (datas da amostra), mantendo as facetas da consulta base.
        evs = _mark_validated(get_all_events(**filters))
        evs = [e for e in evs if e["in_validated_sample"]]
        total = len(evs)
        pages = max(1, (total + per_page - 1) // per_page)
        page = min(max(1, page), pages)
        pg = get_events_page(page=1, per_page=1, sort=sort, **filters)
        pg.update({"items": evs[(page - 1) * per_page: page * per_page], "total": total, "page": page, "pages": pages, "per_page": per_page})
        validated_count = total
    else:
        pg = get_events_page(page=page, per_page=per_page, sort=sort, **filters)
        _mark_validated(pg["items"])
        validated_count = len([d for d in get_validated_sample_dates()])
    base_args = {k: v for k, v in request.query_params.items() if v not in ("", None) and k != "page"}
    if "category" in base_args and base_args["category"] == "Todas":
        base_args.pop("category")
    try:
        with open(os.path.join(BASE_DIR, "config", "categories.yaml"), "r", encoding="utf-8") as f:
            cats = _yaml.safe_load(f)
        macro_labels = {k: v["label_pt"] for k, v in cats["macro_categories"].items()}
    except Exception:
        macro_labels = {}
    labels = {"category": "Categoria", "macro": "Macro", "tier": "Tier", "precision": "Precisão", "polarity": "Polaridade",
              "country": "País", "century": "Século", "time_known": "Hora", "search": "Busca", "validated": "Amostra validada"}
    active_filters = [(k, f"{labels.get(k, k)}: {macro_labels.get(v, v) if k == 'macro' else v}") for k, v in base_args.items() if k in labels]
    # links de paginação compactos
    cur, last = pg["page"], pg["pages"]
    cand = sorted({1, last, cur, max(1, cur - 1), min(last, cur + 1), max(1, cur - 2), min(last, cur + 2)})
    page_links = []
    for i, p in enumerate(cand):
        if i and p - cand[i - 1] > 1:
            page_links.append(None)
        page_links.append(p)
    return templates.TemplateResponse(
        request=request,
        name="events.html",
        context={
            "page": pg, "page_links": page_links, "base_args": base_args, "active_filters": active_filters,
            "selected_category": category, "search_term": search, "sort": sort, "macro_labels": macro_labels,
            "validated_only": bool(validated), "validated_count": validated_count, "facets_total": pg["total"],
        }
    )

@app.get("/events/{event_id}", response_class=HTMLResponse)
async def event_detail_view(request: Request, event_id: int):
    event = get_event_by_id(event_id)
    if not event:
        return HTMLResponse(content="<h1>Evento não encontrado</h1>", status_code=404)

    chart = event.get("chart", {})
    mandala_svg = generate_mandala_svg(chart)

    # Calcular ênfase astrológica e corroboração teórica moderna
    try:
        emphasis = calculate_event_emphasis(event_id)
    except Exception:
        emphasis = None

    # Navegação cronológica (get_all_events já ordena por data), não por id
    all_evs = get_all_events()
    ids = [e["id"] for e in all_evs]
    pos = ids.index(event_id) if event_id in ids else -1
    prev_id = ids[pos - 1] if pos > 0 else None
    next_id = ids[pos + 1] if 0 <= pos < len(ids) - 1 else None
    event["in_validated_sample"] = event.get("date") in get_validated_sample_dates()

    # Métricas Internacionais (Barbault CI, Oshop Sum of Cosines & Análogos Cósmicos)
    barbault_data, oshop_data, analogues_data = None, None, None
    try:
        import swisseph as swe
        from src.features.barbault_ci import calculate_barbault_comparison
        from src.features.sum_of_cosines import calculate_oshop_indices
        from src.analysis.historical_analogues import find_historical_analogues

        from src.core.dates import catalog_date_to_jd
        tjd = catalog_date_to_jd(event["date"])
        barbault_data = calculate_barbault_comparison(tjd)
        oshop_data = calculate_oshop_indices(tjd)
        ana_res = find_historical_analogues(event["date"], top_k=5, exclude_event_id=event_id, min_year_diff=1)
        analogues_data = ana_res.get("top_analogues", [])
    except Exception:
        pass

    # Dados de Controle Aleatório Nulo pré-calculados no servidor
    control_data = get_random_control_comparison_data(event_id)

    return templates.TemplateResponse(
        request=request,
        name="event_detail.html",
        context={
            "event": event,
            "chart": chart,
            "mandala_svg": mandala_svg,
            "emphasis": emphasis,
            "prev_id": prev_id,
            "next_id": next_id,
            "barbault_data": barbault_data,
            "oshop_data": oshop_data,
            "analogues_data": analogues_data,
            "control_data": control_data
        }
    )

@app.get("/correlations", response_class=HTMLResponse)
async def correlations_view(request: Request):
    from src.web.i18n import resolve_lang, translator
    lang = resolve_lang(request)
    corrs = get_category_correlations()
    return templates.TemplateResponse(
        request=request,
        name="correlations.html",
        context={
            "corrs": corrs,
            "lang": lang,
            "t": translator(lang),
        }
    )

@app.get("/simulator", response_class=HTMLResponse)
async def simulator_get_view(request: Request, title: Optional[str] = None, date: Optional[str] = None, time: str = "12:00",
                             city: str = "", country: str = "", latitude: float = 0.0, longitude: float = 0.0):
    """Simulador com URL compartilhável: /simulator?date=2030-05-15&time=12:00&latitude=..&longitude=.."""
    future_data = generate_future_timeline_1800_2100(force_refresh=False)
    chart_series = build_chart_series(future_data)
    results, sim_event, error = None, None, None
    barbault_data, oshop_data, analogues_data = None, None, None
    if date:
        try:
            sim = SimulationInput(title=title or "Simulação", date=date, time=time, city=city, country=country, latitude=latitude, longitude=longitude)
            sim_event = sim.model_dump()
            chart = calculate_event_chart(sim_event)
            results = {"chart": chart, "similarity": find_similar_events(chart, top_k=5)}

            import swisseph as swe
            from src.features.barbault_ci import calculate_barbault_comparison
            from src.features.sum_of_cosines import calculate_oshop_indices
            from src.analysis.historical_analogues import find_historical_analogues

            from src.core.dates import catalog_date_to_jd
            tjd = catalog_date_to_jd(date)
            barbault_data = calculate_barbault_comparison(tjd)
            oshop_data = calculate_oshop_indices(tjd)
            ana_res = find_historical_analogues(date, top_k=5)
            analogues_data = ana_res.get("top_analogues", [])
        except Exception as e:
            error = f"Parâmetros inválidos: {e}"

    return templates.TemplateResponse(
        request=request,
        name="simulator.html",
        context={
            "future_data": future_data,
            "chart_series": chart_series,
            "results": results,
            "input_data": sim_event,
            "error": error,
            "share_url": str(request.url) if results else None,
            "barbault_data": barbault_data,
            "oshop_data": oshop_data,
            "analogues_data": analogues_data
        }
    )

def _category_skill_badges() -> list:
    """v6: para cada categoria estimável (config/categories.yaml), o melhor BSS astrológico do hindcast dos alvos associados."""
    import yaml as _yaml
    try:
        with open(os.path.join(BASE_DIR, "config", "categories.yaml"), "r", encoding="utf-8") as f:
            cats = _yaml.safe_load(f)
    except Exception:
        return []
    hc = {}
    hc_file = os.path.join(BASE_DIR, "reports", "hindcast_v3.json")
    if os.path.exists(hc_file):
        with open(hc_file, "r", encoding="utf-8") as f:
            hc = json.load(f).get("targets", {})
    astro_models = ("legacy_index", "barbault", "tarnas_outer", "outer_phases", "astro_full")
    out = []
    for key in cats.get("order", []):
        c = cats["categories"][key]
        best = None
        for tname in c.get("hindcast_targets", []):
            t = hc.get(tname)
            if not t:
                continue
            for m, r in t.get("models", {}).items():
                if m in astro_models and (best is None or r["bss"] > best["bss"]):
                    best = {"target": tname, "model": m, "bss": r["bss"], "ci": r.get("bss_ci") or r.get("ci"), "auc": r.get("auc"),
                            "p_pos": r.get("p_bss_pos") or r.get("p_positive")}
        if best is None:
            verdict, badge = "não testado", "slate"
        else:
            ci = best.get("ci") or [None, None]
            positive = best["bss"] > 0 and ci and ci[0] is not None and ci[0] > 0
            verdict, badge = ("skill positivo", "emerald") if positive else ("sem skill demonstrado", "amber")
        out.append({"key": key, "label": c["label_pt"], "short": c["short_pt"], "icon": c["icon"], "color": c["theme_color"],
                    "skeptical": bool(c.get("skeptical_control")), "best": best, "verdict": verdict, "badge": badge,
                    "targets": c.get("hindcast_targets", [])})
    return out


@app.api_route("/projections", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def projections_view(request: Request, decade: str = "Todas", alert: str = "Todos", search: str = ""):
    data = get_projections_2027_2060(force_refresh=False)
    peaks_catalog = load_energy_peaks_catalog()
    
    # Filtragem opcional no servidor (a interface também conta com filtro dinâmico em JS)
    filtered = data["projections"]
    if decade != "Todas":
        filtered = [p for p in filtered if p["decade"] == decade]
    if alert != "Todos":
        filtered = [p for p in filtered if alert.lower() in p["alert_level"].lower() or alert.lower() == p["alert_color"].lower()]
    if search:
        s_lower = search.lower()
        filtered = [
            p for p in filtered
            if s_lower in str(p["year"])
            or s_lower in p["cosmic_trigger"].lower()
            or s_lower in p["scenarios_and_possibilities"].lower()
            or s_lower in p["top_precedent"]["title"].lower()
            or s_lower in p["dominant_category"].lower()
        ]

    category_skill = _category_skill_badges()
    return templates.TemplateResponse(
        request=request,
        name="projections.html",
        context={
            "data": data,
            "projections": filtered,
            "peaks_catalog": peaks_catalog,
            "category_skill": category_skill,
            "selected_decade": decade,
            "selected_alert": alert,
            "search_query": search
        }
    )

@app.post("/simulator/recalculate")
async def simulator_recalculate_view(request: Request):
    # Forçar recálculo completo da linha do tempo contínua 1800-2100
    generate_future_timeline_1800_2100(force_refresh=True)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/simulator", status_code=303)

@app.post("/simulator", response_class=HTMLResponse)
async def simulator_post_view(
    request: Request,
    title: str = Form(...),
    date: str = Form(...),
    time: str = Form("12:00"),
    city: str = Form("São Paulo"),
    country: str = Form("Brasil"),
    latitude: float = Form(-23.5505),
    longitude: float = Form(-46.6333)
):
    # POST -> redireciona para a URL GET equivalente (resultado compartilhável e recarregável)
    from urllib.parse import urlencode
    params = urlencode({"title": title, "date": date, "time": time, "city": city, "country": country,
                        "latitude": latitude, "longitude": longitude})
    return RedirectResponse(url=f"/simulator?{params}#resultado", status_code=303)

# --- Rotas da API REST ---

@app.get("/methodology", response_class=HTMLResponse)
async def methodology_view(request: Request):
    results_file = os.path.join(BASE_DIR, "data", "results.json")
    results_data = {}
    if os.path.exists(results_file):
        try:
            with open(results_file, "r", encoding="utf-8") as f:
                results_data = json.load(f)
        except Exception as e:
            print(f"Error loading results.json: {e}")
    hindcast = {}
    hc_file = os.path.join(BASE_DIR, "reports", "hindcast_v3.json")
    if os.path.exists(hc_file):
        with open(hc_file, "r", encoding="utf-8") as f:
            hindcast = json.load(f)
    return templates.TemplateResponse(
        request=request,
        name="methodology.html",
        context={"results": results_data, "hindcast": hindcast}
    )

@app.get("/forecast", response_class=HTMLResponse)
async def forecast_view(request: Request, target: str = "cow_war_onset"):
    data = load_forecast()
    unified_forecast = build_unified_forecast_data()
    hindcast = {}
    hc_file = os.path.join(BASE_DIR, "reports", "hindcast_v3.json")
    if os.path.exists(hc_file):
        with open(hc_file, "r", encoding="utf-8") as f:
            hindcast = json.load(f)
    if data and target not in data["targets"]:
        target = next(iter(data["targets"]))
    return templates.TemplateResponse(
        request=request,
        name="forecast.html",
        context={
            "forecast": data,
            "unified_forecast": unified_forecast,
            "hindcast": hindcast,
            "selected_target": target
        }
    )

@app.get("/api/forecast")
async def api_forecast(target: str = None):
    data = load_forecast()
    if not data:
        return JSONResponse(content={"error": "forecast_v3.json não gerado. Rode: make forecast"}, status_code=503)
    if target:
        if target not in data["targets"]:
            return JSONResponse(content={"error": "target desconhecido", "available": list(data["targets"].keys())}, status_code=404)
        return JSONResponse(content={"target": target, **data["targets"][target]})
    slim = {k: v for k, v in data.items() if k not in ("calendar", "analogs")}
    return JSONResponse(content=slim)

@app.get("/api/forecast/year/{year}")
async def api_forecast_year(year: int):
    data = load_forecast()
    if not data or str(year) not in data["calendar"]:
        return JSONResponse(content={"error": "ano fora do horizonte 2026–2060"}, status_code=404)
    return JSONResponse(content={
        "year": year,
        "calendar": data["calendar"][str(year)],
        "analogs": data["analogs"].get(str(year)),
        "targets": {k: next((r for r in v["years"] if r["year"] == year), None) for k, v in data["targets"].items()}
    })

def get_random_control_comparison_data(event_id: int) -> dict:
    """Busca datas do grupo de controle que apresentaram tensão equivalente ou superior."""
    conn = get_connection()
    row = conn.execute("SELECT id, title, date, tension_index, chart_json FROM events WHERE id = ?", (event_id,)).fetchone()
    if not row:
        conn.close()
        return {"error": "Event not found", "random_control_matches": [], "explanation": ""}

    target_score = row["tension_index"] * 10.0
    if row["chart_json"]:
        cj = json.loads(row["chart_json"])
        target_score = cj.get("summary", {}).get("tension_index_1000", target_score)

    ctrl_rows = conn.execute("SELECT control_date FROM control_dates ORDER BY RANDOM() LIMIT 200").fetchall()
    conn.close()

    from datetime import date
    from src.core.ephemeris_grid import get_score_for_date
    matched_controls = []
    for cr in ctrl_rows:
        d_parts = [int(p) for p in cr[0].split("-")]
        cd = date(d_parts[0], d_parts[1], d_parts[2])
        score = get_score_for_date(cd)
        if score >= (target_score - 50.0):
            matched_controls.append({
                "date": cr[0],
                "score_1000": score,
                "score_percentile": f"{score / 10.0:.1f}%"
            })
            if len(matched_controls) >= 3:
                break

    return {
        "event_id": event_id,
        "event_title": row["title"],
        "event_date": row["date"],
        "event_score_1000": round(target_score, 1),
        "random_control_matches": matched_controls,
        "explanation": "Datas aleatórias do grupo de controle que apresentaram intensidade geométrica similar ou superior por mera probabilidade temporal."
    }

@app.get("/api/random-control-comparison/{event_id}")
async def api_random_control_comparison(event_id: int):
    data = get_random_control_comparison_data(event_id)
    if "error" in data and data["error"] == "Event not found":
        return JSONResponse(content=data, status_code=404)
    return JSONResponse(content=data)

@app.get("/api/future-timeline")
async def api_future_timeline():
    return JSONResponse(content=generate_future_timeline_1800_2100())

@app.get("/api/projections-2027-2060")
async def api_projections_2027_2060():
    return JSONResponse(content=get_projections_2027_2060(force_refresh=False))

@app.get("/api/energy-peaks-2026-2060")
async def api_energy_peaks_2026_2060(
    scenario: Optional[str] = None,
    scope: Optional[str] = None,
    country: Optional[str] = None,
    decade: Optional[str] = None
):
    """Retorna os picos de energia mundiais e por país para os anos 2026–2060 em ordem cronológica."""
    data = load_energy_peaks_catalog()
    peaks = data.get("peaks", [])
    if scenario and scenario != "Todos":
        peaks = [p for p in peaks if p.get("scenario_key") == scenario]
    if scope and scope != "Todos":
        peaks = [p for p in peaks if p.get("scope_type") == scope]
    if country and country != "Todos":
        peaks = [p for p in peaks if p.get("country_iso") == country.upper()]
    if decade and decade != "Todas":
        peaks = [p for p in peaks if p.get("decade") == decade]
    return JSONResponse(content={
        "total": len(peaks),
        "kpis": data.get("kpis", {}),
        "peaks": peaks
    })

@app.get("/api/stats")
async def api_stats():
    return JSONResponse(content=get_events_stats())

@app.get("/api/events")
async def api_events(category: str = None, search: str = None):
    evs = get_all_events(category=category, search=search)
    return JSONResponse(content=evs)

@app.get("/api/events/{event_id}")
async def api_event_detail(event_id: int):
    ev = get_event_by_id(event_id)
    if not ev:
        return JSONResponse(content={"error": "Not found"}, status_code=404)
    return JSONResponse(content=ev)

@app.post("/api/simulate")
async def api_simulate(data: SimulationInput):
    chart = calculate_event_chart(data.model_dump())
    similarity = find_similar_events(chart, top_k=5)
    return JSONResponse(content={
        "chart": chart,
        "similarity": similarity
    })

# ==================== ENDPOINTS DE PESQUISA INTERNACIONAL & NOVAS METODOLOGIAS ====================

@app.get("/api/historical-analogues")
async def api_historical_analogues(
    date: str,
    category: Optional[str] = None,
    top_k: int = 5,
    exclude_id: Optional[int] = None,
    min_year_diff: Optional[int] = None
):
    """
    Motor Cosmic History Search / Historical Analogues:
    Busca eventos históricos análogos a uma configuração celeste em qualquer data (passada ou futura).
    """
    try:
        from src.analysis.historical_analogues import find_historical_analogues
        res = find_historical_analogues(
            date,
            category_filter=category,
            top_k=min(top_k, 20),
            exclude_event_id=exclude_id,
            min_year_diff=min_year_diff
        )
        return JSONResponse(content=res)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.get("/api/features/oshop")
async def api_features_oshop(date: str):
    """
    Calcula as métricas de clustering Sum of Cosines de Renay Oshop (Project 17) para uma data.
    """
    try:
        import swisseph as swe
        from src.features.sum_of_cosines import calculate_oshop_indices
        from src.core.dates import catalog_date_to_jd
        tjd = catalog_date_to_jd(date)
        res = calculate_oshop_indices(tjd)
        return JSONResponse(content=res)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

@app.get("/api/features/barbault")
async def api_features_barbault(date: str):
    """
    Calcula o comparativo formal André Barbault CI-4 vs CI-5 (Archos 2024) com tendências e derivadas anuais.
    """
    try:
        import swisseph as swe
        from src.features.barbault_ci import calculate_barbault_comparison
        from src.core.dates import catalog_date_to_jd
        tjd = catalog_date_to_jd(date)
        res = calculate_barbault_comparison(tjd)
        return JSONResponse(content=res)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

# Inclusão modular do motor de Astrologia Mundana dos Países (National Horoscopes)
from src.mundane.web_routes import router as mundane_router
app.include_router(mundane_router)

# v6: Módulo Pessoal (mapa natal, trânsitos de vida, progressões secundárias)
from src.natal.web_routes import router as natal_router
app.include_router(natal_router)

# v6: páginas de apoio (glossário, dados & fontes, sobre, busca global)
from src.web.pages import router as pages_router
app.include_router(pages_router)

# Compressão de alta performance: Brotli (qualidade 4) com fallback automático para GZip
from brotli_asgi import BrotliMiddleware
app.add_middleware(BrotliMiddleware, quality=4, minimum_size=512, gzip_fallback=True)


