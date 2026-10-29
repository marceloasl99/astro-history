"""
Aplicação Web FastAPI rodando na porta 81 (0.0.0.0:81).
Oferece o Dashboard completo de Astrologia Moderna com os 300 fatos históricos,
visualização de mapas astrais em mandala SVG e simulador de correlações futuras.
"""

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
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
    get_connection
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="AstroHistory - Astrologia Moderna & 300 Fatos Históricos",
    description="Plataforma de Correlação Astrológica Histórica com Swiss Ephemeris",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração de templates e estáticos
TEMPLATES_DIR = "/home/astro/src/web/templates"
STATIC_DIR = "/home/astro/src/web/static"

templates = Jinja2Templates(directory=TEMPLATES_DIR)
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# --- Rotas HTML ---

@app.api_route("/", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def index_view(request: Request):
    stats = get_events_stats()
    # Eventos em destaque paradigmáticos (ex: Crash de 1929, Hiroshima, Muro de Berlim, 11/Setembro, etc.)
    all_evs = get_all_events()
    featured_ids = [93, 107, 134, 156, 171, 188]
    featured_events = [e for e in all_evs if e["id"] in featured_ids]
    if len(featured_events) < 6:
        featured_events = all_evs[:6]

    # Carregar dados da linha do tempo contínua 1800-2100 na escala 0-1000
    future_data = generate_future_timeline_1800_2100(force_refresh=False)
    chart_series = {
        "years": [t["year"] for t in future_data["timeline"]],
        "tension_1000": [t["tension_index_1000"] for t in future_data["timeline"]],
        "avg_tension_1000": [t["avg_tension_1000"] for t in future_data["timeline"]],
        "conflict_risk_1000": [t["conflict_risk_index_1000"] for t in future_data["timeline"]],
        "crisis_risk_1000": [t["crisis_risk_index_1000"] for t in future_data["timeline"]],
        "tech_innovation_1000": [t["tech_innovation_index_1000"] for t in future_data["timeline"]],
        "is_historical": [t["is_historical"] for t in future_data["timeline"]],
        "hist_titles": [
            t["historical_events"][0]["title"] if t.get("historical_events") else ""
            for t in future_data["timeline"]
        ],
        "hist_ids": [
            t["historical_events"][0]["id"] if t.get("historical_events") else None
            for t in future_data["timeline"]
        ],
        "triggers": [t["cosmic_trigger"] for t in future_data["timeline"]],
        "top_events": [
            t["historical_events"][0]["title"] if t.get("historical_events")
            else (t["top_matches"][0]["title"] if t.get("top_matches") else "")
            for t in future_data["timeline"]
        ]
    }

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "stats": stats,
            "featured_events": featured_events,
            "future_data": future_data,
            "chart_series": chart_series
        }
    )

@app.get("/events", response_class=HTMLResponse)
async def events_catalog_view(request: Request, category: str = "Todas", search: str = ""):
    events = get_all_events(category=category if category != "Todas" else None, search=search if search else None)
    return templates.TemplateResponse(
        request=request,
        name="events.html",
        context={
            "events": events,
            "selected_category": category,
            "search_term": search
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

    all_evs = get_all_events()
    total_evs = len(all_evs) if all_evs else 300
    prev_id = event_id - 1 if event_id > 1 else None
    next_id = event_id + 1 if event_id < total_evs else None

    return templates.TemplateResponse(
        request=request,
        name="event_detail.html",
        context={
            "event": event,
            "chart": chart,
            "mandala_svg": mandala_svg,
            "emphasis": emphasis,
            "prev_id": prev_id,
            "next_id": next_id
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
async def simulator_get_view(request: Request):
    future_data = generate_future_timeline_1800_2100(force_refresh=False)
    
    # Preparar séries temporais de alta resolução (0-1000) para Chart.js
    chart_series = {
        "years": [t["year"] for t in future_data["timeline"]],
        "tension_1000": [t["tension_index_1000"] for t in future_data["timeline"]],
        "avg_tension_1000": [t["avg_tension_1000"] for t in future_data["timeline"]],
        "conflict_risk_1000": [t["conflict_risk_index_1000"] for t in future_data["timeline"]],
        "crisis_risk_1000": [t["crisis_risk_index_1000"] for t in future_data["timeline"]],
        "tech_innovation_1000": [t["tech_innovation_index_1000"] for t in future_data["timeline"]],
        "is_historical": [t["is_historical"] for t in future_data["timeline"]],
        "hist_titles": [
            t["historical_events"][0]["title"] if t.get("historical_events") else ""
            for t in future_data["timeline"]
        ],
        "hist_ids": [
            t["historical_events"][0]["id"] if t.get("historical_events") else None
            for t in future_data["timeline"]
        ],
        "triggers": [t["cosmic_trigger"] for t in future_data["timeline"]],
        "top_events": [
            t["historical_events"][0]["title"] if t.get("historical_events")
            else (t["top_matches"][0]["title"] if t.get("top_matches") else "")
            for t in future_data["timeline"]
        ]
    }

    return templates.TemplateResponse(
        request=request,
        name="simulator.html",
        context={
            "future_data": future_data,
            "chart_series": chart_series,
            "results": None,
            "input_data": None
        }
    )

@app.api_route("/projections", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def projections_view(request: Request, decade: str = "Todas", alert: str = "Todos", search: str = ""):
    data = get_projections_2027_2060(force_refresh=False)
    
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
    future_data = generate_future_timeline_1800_2100(force_refresh=False)
    chart_series = {
        "years": [t["year"] for t in future_data["timeline"]],
        "tension_1000": [t["tension_index_1000"] for t in future_data["timeline"]],
        "avg_tension_1000": [t["avg_tension_1000"] for t in future_data["timeline"]],
        "conflict_risk_1000": [t["conflict_risk_index_1000"] for t in future_data["timeline"]],
        "crisis_risk_1000": [t["crisis_risk_index_1000"] for t in future_data["timeline"]],
        "tech_innovation_1000": [t["tech_innovation_index_1000"] for t in future_data["timeline"]],
        "is_historical": [t["is_historical"] for t in future_data["timeline"]],
        "hist_titles": [
            t["historical_events"][0]["title"] if t.get("historical_events") else ""
            for t in future_data["timeline"]
        ],
        "hist_ids": [
            t["historical_events"][0]["id"] if t.get("historical_events") else None
            for t in future_data["timeline"]
        ],
        "triggers": [t["cosmic_trigger"] for t in future_data["timeline"]],
        "top_events": [
            t["historical_events"][0]["title"] if t.get("historical_events")
            else (t["top_matches"][0]["title"] if t.get("top_matches") else "")
            for t in future_data["timeline"]
        ]
    }

    sim_event = {
        "title": title,
        "date": date,
        "time": time,
        "city": city,
        "country": country,
        "latitude": latitude,
        "longitude": longitude
    }

    chart = calculate_event_chart(sim_event)
    similarity = find_similar_events(chart, top_k=5)

    results = {
        "chart": chart,
        "similarity": similarity
    }

    return templates.TemplateResponse(
        request=request,
        name="simulator.html",
        context={
            "future_data": future_data,
            "chart_series": chart_series,
            "results": results,
            "input_data": sim_event
        }
    )

# --- Rotas da API REST ---

@app.get("/methodology", response_class=HTMLResponse)
async def methodology_view(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="methodology.html",
        context={}
    )

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
async def api_simulate(data: dict):
    chart = calculate_event_chart(data)
    similarity = find_similar_events(chart, top_k=5)
    return JSONResponse(content={
        "chart": chart,
        "similarity": similarity
    })
