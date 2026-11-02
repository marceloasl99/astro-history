"""
Aplicação Web FastAPI rodando na porta 81 (0.0.0.0:81).
Oferece o Dashboard completo de Astrologia Moderna com os 1.342 fatos históricos mundiais,
visualização de mapas astrais em mandala SVG e simulador de correlações futuras.
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field
from typing import Optional
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import os
import json

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
from src.mundane.energy_peaks import load_energy_peaks_catalog

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="AstroHistory - Astrologia Moderna & 1.342 Fatos Históricos Mundiais",
    description="Plataforma Internacional de Correlação Astrológica Histórica com Swiss Ephemeris",
    version="4.0.0",
    lifespan=lifespan
)

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

templates = Jinja2Templates(directory=TEMPLATES_DIR)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
if os.path.exists(WEB_DIR):
    app.mount("/web", StaticFiles(directory=WEB_DIR, html=True), name="web")

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
    all_evs = get_all_events()
    featured_ids = [100, 107, 93, 134, 156, 171]
    featured_events = [e for e in all_evs if e["id"] in featured_ids]
    if len(featured_events) < 6:
        featured_events = all_evs[:6]

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

@app.get("/events", response_class=HTMLResponse)
async def events_catalog_view(request: Request, category: str = "Todas", search: str = "", validated: int = 0):
    events = _mark_validated(get_all_events(category=category if category != "Todas" else None, search=search if search else None))
    validated_count = sum(1 for e in events if e["in_validated_sample"])
    if validated:
        events = [e for e in events if e["in_validated_sample"]]
    return templates.TemplateResponse(
        request=request,
        name="events.html",
        context={
            "events": events,
            "selected_category": category,
            "search_term": search,
            "validated_only": bool(validated),
            "validated_count": validated_count
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

        p = [int(x) for x in event["date"].split("-")]
        tjd = swe.julday(p[0], p[1], p[2], 12.0)
        barbault_data = calculate_barbault_comparison(tjd)
        oshop_data = calculate_oshop_indices(tjd)
        ana_res = find_historical_analogues(event["date"], top_k=5, exclude_event_id=event_id, min_year_diff=1)
        analogues_data = ana_res.get("top_analogues", [])
    except Exception:
        pass

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
            "analogues_data": analogues_data
        }
    )

@app.get("/correlations", response_class=HTMLResponse)
async def correlations_view(request: Request):
    corrs = get_category_correlations()
    return templates.TemplateResponse(
        request=request,
        name="correlations.html",
        context={
            "corrs": corrs
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

            p = [int(x) for x in date.split("-")]
            tjd = swe.julday(p[0], p[1], p[2], 12.0)
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

    return templates.TemplateResponse(
        request=request,
        name="projections.html",
        context={
            "data": data,
            "projections": filtered,
            "peaks_catalog": peaks_catalog,
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
        context={"forecast": data, "hindcast": hindcast, "selected_target": target}
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

@app.get("/api/random-control-comparison/{event_id}")
async def api_random_control_comparison(event_id: int):
    conn = get_connection()
    row = conn.execute("SELECT id, title, date, tension_index, chart_json FROM events WHERE id = ?", (event_id,)).fetchone()
    if not row:
        conn.close()
        return JSONResponse(content={"error": "Event not found"}, status_code=404)

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

    return JSONResponse(content={
        "event_id": event_id,
        "event_title": row["title"],
        "event_date": row["date"],
        "event_score_1000": round(target_score, 1),
        "random_control_matches": matched_controls,
        "explanation": "Datas aleatórias do grupo de controle que apresentaram intensidade geométrica similar ou superior por mera probabilidade temporal."
    })

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
        parts = [int(p) for p in date.strip().split("-")]
        tjd = swe.julday(parts[0], parts[1], parts[2], 12.0)
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
        parts = [int(p) for p in date.strip().split("-")]
        tjd = swe.julday(parts[0], parts[1], parts[2], 12.0)
        res = calculate_barbault_comparison(tjd)
        return JSONResponse(content=res)
    except Exception as e:
        return JSONResponse(content={"error": str(e)}, status_code=400)

# Inclusão modular do motor de Astrologia Mundana dos Países (National Horoscopes)
from src.mundane.web_routes import router as mundane_router
app.include_router(mundane_router)


