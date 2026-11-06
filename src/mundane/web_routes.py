"""
Rotas Web e API REST para a seção de Astrologia Mundana dos Países.
Integrado de forma modular ao FastAPI sem interferir nas rotas existentes.
"""

from fastapi import APIRouter, Request, Query, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from datetime import date
import os
import json

from src.mundane.countries_data import (
    get_all_countries,
    get_country_by_iso,
    get_continents,
    search_countries
)
from src.mundane.transits_engine import (
    calculate_country_chart,
    calculate_transits_for_date,
    calculate_activation_timeline
)
from src.mundane.mandala_biwheel import generate_biwheel_svg
from src.mundane.historical_analyzer import (
    get_country_analyzed_history
)
from src.mundane.analogy_engine import (
    generate_grounded_future_forecast
)
from src.mundane.history_and_future import (
    get_country_future_outlook
)
from src.mundane.energy_peaks import (
    detect_energy_peaks_and_recurrences
)

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.web.templating import templates  # v6: instância única

router = APIRouter(tags=["mundane_astrology"])

@router.api_route("/countries", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def countries_hub(request: Request, q: str = "", continent: str = ""):
    """Hub principal da seção de Astrologia Mundana: catálogo com busca e filtros."""
    countries = get_all_countries()
    continents = get_continents()
    return templates.TemplateResponse(
        request=request,
        name="countries_index.html",
        context={
            "countries": countries,
            "continents": continents,
            "query": q,
            "selected_continent": continent or "todos"
        }
    )

@router.api_route("/countries/{iso_code}", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def country_detail_view(request: Request, iso_code: str, date_query: str = Query(None, alias="date")):
    """Página detalhada do país: mapa natal, mandala bi-wheel, trânsitos, linha do tempo e projeções."""
    country = get_country_by_iso(iso_code)
    if not country:
        raise HTTPException(status_code=404, detail=f"País com código '{iso_code}' não encontrado.")

    # Data de análise (padrão: hoje)
    today_str = date.today().isoformat()
    selected_date = date_query.strip() if date_query else today_str

    # 1. Mapa Natal canônico
    country_chart = calculate_country_chart(country)

    # 2. Trânsitos na data selecionada
    transits = calculate_transits_for_date(country_chart, selected_date)

    # 3. SVG Bi-Wheel
    biwheel_svg = generate_biwheel_svg(country_chart, transits)

    # 4. Linha do Tempo (1800 a 2060)
    timeline_data = calculate_activation_timeline(country_chart, start_year=1800, end_year=2060)

    # 5. Fatos Históricos reais analisados com suas assinaturas astrológicas
    analyzed_history = get_country_analyzed_history(country_chart)

    # 6. Previsões futuras (2026–2050) fundamentadas em precedentes históricos
    grounded_forecasts = generate_grounded_future_forecast(country_chart)

    # 7. Diagnóstico estruturado pelos 5 pilares do Estado
    future_outlook = get_country_future_outlook(country_chart)

    # 8. Picos de Energia Astrológica & Tendências Cíclicas Recorrentes (2026–2050)
    energy_peaks = detect_energy_peaks_and_recurrences(country_chart)

    return templates.TemplateResponse(
        request=request,
        name="country_detail.html",
        context={
            "chart": country_chart,
            "transits": transits,
            "biwheel_svg": biwheel_svg,
            "selected_date": selected_date,
            "today_date": today_str,
            "timeline_json": json.dumps(timeline_data),
            "analyzed_history": analyzed_history,
            "grounded_forecasts": grounded_forecasts,
            "future_outlook": future_outlook,
            "energy_peaks": energy_peaks
        }
    )

# --- ENDPOINTS API REST ---

@router.get("/api/countries")
async def api_list_countries(q: str = "", continent: str = ""):
    """Lista todos os países cadastrados com busca opcional por texto e continente."""
    results = search_countries(query=q, continent=continent)
    return JSONResponse(content={"total": len(results), "countries": results})

@router.get("/api/countries/{iso_code}")
async def api_get_country(iso_code: str):
    """Metadados e referências históricas de um país."""
    country = get_country_by_iso(iso_code)
    if not country:
        raise HTTPException(status_code=404, detail="País não encontrado")
    return JSONResponse(content=country)

@router.get("/api/countries/{iso_code}/chart")
async def api_get_country_chart(iso_code: str):
    """Retorna a carta natal calculada do país com posições planetárias tropicais."""
    country = get_country_by_iso(iso_code)
    if not country:
        raise HTTPException(status_code=404, detail="País não encontrado")
    chart = calculate_country_chart(country)
    return JSONResponse(content=chart)

@router.get("/api/countries/{iso_code}/transits")
async def api_get_country_transits(iso_code: str, date_query: str = Query(None, alias="date")):
    """Calcula os aspectos de trânsito ativos sobre a carta do país para uma data específica."""
    country = get_country_by_iso(iso_code)
    if not country:
        raise HTTPException(status_code=404, detail="País não encontrado")
    chart = calculate_country_chart(country)
    target_date = date_query.strip() if date_query else date.today().isoformat()
    transits = calculate_transits_for_date(chart, target_date)
    return JSONResponse(content=transits)

@router.get("/api/countries/{iso_code}/timeline")
async def api_get_country_timeline(iso_code: str, start: int = 1800, end: int = 2060):
    """Retorna a série temporal da curva de ativação de trânsitos de 1800 a 2060."""
    country = get_country_by_iso(iso_code)
    if not country:
        raise HTTPException(status_code=404, detail="País não encontrado")
    chart = calculate_country_chart(country)
    timeline = calculate_activation_timeline(chart, start_year=start, end_year=end)
    return JSONResponse(content=timeline)

@router.get("/api/countries/{iso_code}/historical-events")
async def api_get_country_historical_events(iso_code: str):
    """Retorna os fatos históricos do país com suas assinaturas astrológicas retrospectivas."""
    country = get_country_by_iso(iso_code)
    if not country:
        raise HTTPException(status_code=404, detail="País não encontrado")
    chart = calculate_country_chart(country)
    history = get_country_analyzed_history(chart)
    return JSONResponse(content={"total": len(history), "events": history})

@router.get("/api/countries/{iso_code}/analogies")
async def api_get_country_analogies(iso_code: str):
    """Retorna os precedentes históricos emparelhados com as projeções futuras de 2026 a 2050."""
    country = get_country_by_iso(iso_code)
    if not country:
        raise HTTPException(status_code=404, detail="País não encontrado")
    chart = calculate_country_chart(country)
    forecasts = generate_grounded_future_forecast(chart)
    return JSONResponse(content={"total": len(forecasts), "forecasts": forecasts})

@router.get("/api/countries/{iso_code}/outlook")
async def api_get_country_future_outlook(iso_code: str):
    """Retorna o prognóstico futuro (2026–2050) com análise dos 5 pilares do Estado."""
    country = get_country_by_iso(iso_code)
    if not country:
        raise HTTPException(status_code=404, detail="País não encontrado")
    chart = calculate_country_chart(country)
    outlook = get_country_future_outlook(chart)
    return JSONResponse(content=outlook)

@router.get("/api/countries/{iso_code}/energy-peaks")
async def api_get_country_energy_peaks(iso_code: str):
    """Retorna os picos de energia astrológica projetados (2026–2050) e recorrências históricas."""
    country = get_country_by_iso(iso_code)
    if not country:
        raise HTTPException(status_code=404, detail="País não encontrado")
    chart = calculate_country_chart(country)
    peaks = detect_energy_peaks_and_recurrences(chart)
    return JSONResponse(content={"total": len(peaks), "peaks": peaks})
