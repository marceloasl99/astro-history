"""
Rotas web do módulo pessoal (/natal/*) e API interna (/api/natal/*).

- Páginas HTML server-rendered (sem chamadas a /api/* do navegador).
- Dados de nascimento viajam apenas na URL (stateless); nada é persistido.
- Rate limit em memória por IP; /natal/places (autocomplete) é same-origin e não fica sob /api/.
"""

import json
import os
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from urllib.parse import urlencode

import swisseph as swe

from src.natal.bodies import ANGLES, BODY_META, NATAL_BODIES_OPTIONAL, TRANSIT_GRID_BODIES
from src.natal.config import natal_config
from src.natal.domains import domain_meta
from src.natal.exports import hits_csv, ics_calendar, to_json, windows_csv
from src.natal.gazetteer import available as gazetteer_available, search_places
from src.natal.interpretations import disclaimer
from src.natal.models import BirthInput
from src.natal.service import build_profile, build_progressions, chart_only
from src.web.i18n import resolve_lang, translator
from src.web.mandala import generate_mandala_svg
from src.mundane.mandala_biwheel import generate_biwheel_svg

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATES_DIR = os.path.join(BASE_DIR, "src", "web", "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

router = APIRouter(tags=["natal"])

QUERY_KEYS = set(BirthInput.model_fields.keys())
VIEW_KEYS = {"today", "view", "decade"}

EXAMPLES = [
    {"label": "Albert Einstein", "date": "1879-03-14", "time": "11:30", "lat": 48.4, "lon": 9.9833, "place": "Ulm, Alemanha", "tz": "Europe/Berlin", "source": "Astrodatabank AA"},
    {"label": "Frida Kahlo", "date": "1907-07-06", "time": "08:30", "lat": 19.3556, "lon": -99.1611, "place": "Coyoacán, México", "tz": "America/Mexico_City", "source": "Astrodatabank AA"},
    {"label": "Carl Gustav Jung", "date": "1875-07-26", "time": "19:32", "lat": 47.5667, "lon": 9.3833, "place": "Kesswil, Suíça", "tz": "Europe/Zurich", "source": "Astrodatabank A"},
    {"label": "Exemplo sem hora", "date": "1990-05-14", "time": "12:00", "time_known": False, "lat": -23.5505, "lon": -46.6333, "place": "São Paulo, Brasil", "tz": "America/Sao_Paulo", "source": "sintético"},
]


# ----------------------------------------------------------------------------- rate limit
class _Buckets:
    def __init__(self):
        self.hits: Dict[str, List[float]] = defaultdict(list)

    def allow(self, key: str, per_minute: int) -> bool:
        now = time.time()
        window = [t for t in self.hits[key] if now - t < 60.0]
        if len(window) >= per_minute:
            self.hits[key] = window
            return False
        window.append(now)
        self.hits[key] = window
        if len(self.hits) > 5000:
            for k in list(self.hits.keys())[:1000]:
                self.hits.pop(k, None)
        return True


_BUCKETS = _Buckets()


def _client_ip(request: Request) -> str:
    for h in ("cf-connecting-ip", "x-forwarded-for"):
        v = request.headers.get(h)
        if v:
            return v.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _rate_limit(request: Request, kind: str = "pages") -> None:
    cfg = natal_config()["privacy"]
    limit = int(cfg["places_rate_limit_per_minute"] if kind == "places" else cfg["rate_limit_per_minute"])
    if len(str(request.url.query)) > int(cfg["max_query_bytes"]):
        raise HTTPException(status_code=414, detail="query too long")
    if not _BUCKETS.allow(f"{kind}:{_client_ip(request)}", limit):
        raise HTTPException(status_code=429, detail="rate limit")


# ----------------------------------------------------------------------------- helpers
def _parse_input(request: Request, lang: str) -> BirthInput:
    q = {k: v for k, v in request.query_params.items() if k in QUERY_KEYS}
    q.setdefault("lang", lang)
    return BirthInput.from_query(q)


def _reference_jd(request: Request) -> Optional[float]:
    today = request.query_params.get("today")
    if today:
        try:
            y, m, d = (int(x) for x in today.split("-"))
            return swe.julday(y, m, d, 12.0, swe.GREG_CAL)
        except Exception:
            return None
    return None


def _ctx(request: Request, lang: str, **kw) -> Dict[str, Any]:
    cfg = natal_config()
    base = {
        "request": request, "lang": lang, "t": translator(lang), "disclaimer": disclaimer(lang),
        "natal_cfg": cfg, "gazetteer": gazetteer_available(), "examples": EXAMPLES,
        "house_systems": cfg["houses"]["allowed"], "optional_bodies": NATAL_BODIES_OPTIONAL,
        "body_meta": BODY_META, "domain_meta": domain_meta(lang),
    }
    base.update(kw)
    return base


def _nav_urls(inp: BirthInput) -> Dict[str, str]:
    q = urlencode(inp.query_params())
    return {"chart": f"/natal/chart?{q}", "transits": f"/natal/transits?{q}", "progressions": f"/natal/progressions?{q}",
            "csv": f"/natal/export.csv?{q}", "ics": f"/natal/export.ics?{q}", "json": f"/natal/export.json?{q}",
            "form": f"/natal?{q}", "query": q}


def _compact_windows(windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out = []
    for w in windows:
        out.append({
            "i": w["id"], "b": w["transit_body"], "p": w["natal_point"], "a": w["aspect"], "f": w["family"],
            "s": w["start"], "e": w["end"], "h": [h["date"] for h in w["hits"]], "r": [1 if h["retrograde"] else 0 for h in w["hits"]],
            "t": w.get("tone"), "d": w.get("primary_domain"), "w": w.get("intensity_peak", 0), "ep": w.get("episode_id"),
            "c": w.get("cycle_label"), "x": 1 if w["exact"] else 0, "bs": w["transit_symbol"], "ps": w["point_symbol"],
            "as": w["aspect_symbol"], "n": f"{w['transit_name']} {w['aspect_name']} {w['point_name']}",
        })
    return out


def _compact_episodes(episodes: List[Dict[str, Any]], windows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cycle_by_ep = {w["episode_id"]: w["cycle_label"] for w in windows if w.get("cycle_label") and w.get("episode_id")}
    return [{"i": e["id"], "b": e["transit_body"], "p": e["natal_point"], "a": e["aspect"], "f": e["family"],
             "s": e["start"], "e": e["end"], "h": [h["date"] for h in e["hits"]], "r": [1 if h["retrograde"] else 0 for h in e["hits"]],
             "n": f"{e['transit_name']} {e['aspect_name']} {e['point_name']}", "bs": e["transit_symbol"], "ps": e["point_symbol"],
             "as": e["aspect_symbol"], "nw": e["n_windows"], "w": e["peak_closeness"], "c": cycle_by_ep.get(e["id"])} for e in episodes]


def _render_error(request: Request, lang: str, err: Exception, status: int = 400) -> HTMLResponse:
    msg = str(err)
    if isinstance(err, ValidationError):
        msg = "; ".join(f"{'.'.join(str(x) for x in e['loc'])}: {e['msg']}" for e in err.errors())
    return templates.TemplateResponse(request=request, name="natal/form.html",
                                      context=_ctx(request, lang, error=msg, prefill=dict(request.query_params)),
                                      status_code=status)


def _mandala(chart: Dict[str, Any]) -> str:
    try:
        return generate_mandala_svg(chart)
    except Exception:
        return ""


def _biwheel(natal: Dict[str, Any], progressed: Dict[str, Any], inp: BirthInput) -> str:
    """Roda dupla natal (interna) × progredida (externa), reaproveitando o renderizador dos países."""
    nature = {"challenging": "tenso", "flowing": "harmônico", "focus": "foco"}
    transits = [{"transit_planet_id": a["progressed"], "natal_planet_id": a["natal"], "aspect_name": a["aspect_name"],
                 "aspect_nature": nature.get(a["family"], "foco"), "is_exact": a["orb"] <= 0.25}
                for a in progressed.get("aspects_to_natal", []) if a["progressed"] not in ANGLES and a["natal"] not in ANGLES]
    natal_like = dict(natal)
    natal_like["flag_emoji"] = "☉"
    natal_like["time"] = inp.time if inp.time_known else ""
    try:
        return generate_biwheel_svg(natal_like, {"transit_bodies": progressed["bodies"], "transits": transits})
    except Exception:
        return ""


# ----------------------------------------------------------------------------- páginas
@router.api_route("/natal", methods=["GET", "HEAD"], response_class=HTMLResponse)
async def natal_form(request: Request):
    lang = resolve_lang(request)
    prefill = {k: v for k, v in request.query_params.items() if k in QUERY_KEYS}
    return templates.TemplateResponse(request=request, name="natal/form.html",
                                      context=_ctx(request, lang, error=None, prefill=prefill))


@router.post("/natal")
async def natal_submit(request: Request):
    _rate_limit(request)
    lang = resolve_lang(request)
    form = await request.form()
    data: Dict[str, Any] = {}
    for k in ("label", "date", "time", "lat", "lon", "tz", "place", "house_system", "orb_preset", "target_mode", "lang", "focus_year"):
        v = form.get(k)
        if v not in (None, ""):
            data[k] = v
    data["time_known"] = form.get("time_known") in ("1", "on", "true")
    data["minors"] = form.get("minors") in ("1", "on", "true")
    bodies: List[str] = []
    if form.get("moon_transits") in ("1", "on", "true"):
        bodies = list(natal_config()["transit_bodies"]["lifetime"]) + ["moon"]
    if bodies:
        data["bodies"] = bodies
    extra = [b for b in form.getlist("extra_natal") if b in NATAL_BODIES_OPTIONAL]
    if extra:
        data["extra_natal"] = extra
    try:
        for k in ("lat", "lon"):
            data[k] = float(str(data.get(k, "")).replace(",", "."))
        if "focus_year" in data:
            data["focus_year"] = int(data["focus_year"])
        data.setdefault("lang", lang)
        inp = BirthInput(**data)
    except (ValidationError, ValueError) as e:
        return _render_error(request, lang, e)
    target = form.get("goto") or "transits"
    if target not in ("chart", "transits", "progressions"):
        target = "transits"
    return RedirectResponse(url=_nav_urls(inp)[target], status_code=303)


@router.get("/natal/places")
async def natal_places(request: Request, q: str = ""):
    _rate_limit(request, "places")
    lang = resolve_lang(request)
    return JSONResponse(content={"results": search_places(q, limit=8, lang=lang)})


@router.get("/natal/chart", response_class=HTMLResponse)
async def natal_chart(request: Request):
    _rate_limit(request)
    lang = resolve_lang(request)
    try:
        inp = _parse_input(request, lang)
    except (ValidationError, ValueError) as e:
        return _render_error(request, lang, e)
    chart = chart_only(inp)
    return templates.TemplateResponse(request=request, name="natal/chart.html",
                                      context=_ctx(request, lang, inp=inp, chart=chart, mandala_svg=_mandala(chart),
                                                   urls=_nav_urls(inp), active_tab="chart"))


@router.get("/natal/transits", response_class=HTMLResponse)
async def natal_transits(request: Request):
    _rate_limit(request)
    lang = resolve_lang(request)
    try:
        inp = _parse_input(request, lang)
    except (ValidationError, ValueError) as e:
        return _render_error(request, lang, e)
    profile = build_profile(inp, reference_jd=_reference_jd(request))
    lt = profile["lifetime"]
    focus_year = profile["meta"]["focus_year"]
    year_windows = [w for w in lt["windows"] if w["start"][:4] <= str(focus_year) <= w["end"][:4]]
    year_windows.sort(key=lambda w: (-w.get("intensity_peak", 0), w["start"]))
    detail_windows = sorted(profile["detail"]["windows"], key=lambda w: w["start"])
    compact = {
        "episodes": _compact_episodes(lt["episodes"], lt["windows"]),
        "years": profile["domains"]["scored"]["years"], "annual_total": profile["domains"]["scored"]["annual_total_1000"],
        "annual": profile["domains"]["scored"]["annual_1000"], "months": profile["domains"]["scored"]["months"],
        "monthly_total": profile["domains"]["scored"]["monthly_total_1000"],
        "domains": [{"k": k, "l": v["label"], "i": v["icon"], "c": v["color"]} for k, v in profile["domains"]["meta"].items()],
        "bodies": lt["bodies"], "axis": profile["axis"], "focus_year": focus_year, "today": profile["now"]["date"],
        "lang": lang, "query": profile["query"],
    }
    return templates.TemplateResponse(request=request, name="natal/transits.html",
                                      context=_ctx(request, lang, inp=inp, profile=profile, chart=profile["chart"],
                                                   urls=_nav_urls(inp), active_tab="transits", focus_year=focus_year,
                                                   year_windows=year_windows, detail_windows=detail_windows,
                                                   compact_json=json.dumps(compact, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")))


@router.get("/natal/progressions", response_class=HTMLResponse)
async def natal_progressions(request: Request):
    _rate_limit(request)
    lang = resolve_lang(request)
    try:
        inp = _parse_input(request, lang)
    except (ValidationError, ValueError) as e:
        return _render_error(request, lang, e)
    prog = build_progressions(inp, reference_jd=_reference_jd(request))
    natal_svg = _mandala(prog["chart"])
    prog_svg = _biwheel(prog["chart"], prog["current"], inp)
    return templates.TemplateResponse(request=request, name="natal/progressions.html",
                                      context=_ctx(request, lang, inp=inp, prog=prog, chart=prog["chart"],
                                                   natal_svg=natal_svg, prog_svg=prog_svg, urls=_nav_urls(inp),
                                                   active_tab="progressions"))


@router.get("/natal/export.{fmt}")
async def natal_export(request: Request, fmt: str):
    _rate_limit(request)
    lang = resolve_lang(request)
    try:
        inp = _parse_input(request, lang)
    except (ValidationError, ValueError) as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    profile = build_profile(inp, reference_jd=_reference_jd(request))
    windows = profile["lifetime"]["windows"] + profile["detail"]["windows"]
    stem = "astrohistory-transitos" if lang == "pt" else "astrohistory-transits"
    if fmt == "csv":
        body = windows_csv(windows) + "\n" + hits_csv(windows)
        return PlainTextResponse(body, media_type="text/csv; charset=utf-8",
                                 headers={"Content-Disposition": f'attachment; filename="{stem}.csv"'})
    if fmt == "ics":
        include_windows = request.query_params.get("windows") == "1"
        body = ics_calendar(profile["lifetime"]["windows"], inp.label, include_windows=include_windows, lang=lang)
        return Response(content=body, media_type="text/calendar; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{stem}.ics"'})
    if fmt == "json":
        slim = {k: v for k, v in profile.items() if k != "chart"}
        slim["chart"] = {k: v for k, v in profile["chart"].items() if k not in ("planets", "point_speeds")}
        return Response(content=to_json(slim), media_type="application/json; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{stem}.json"'})
    raise HTTPException(status_code=404)


# ----------------------------------------------------------------------------- API interna
@router.get("/api/natal/chart")
async def api_natal_chart(request: Request):
    try:
        inp = _parse_input(request, resolve_lang(request))
    except (ValidationError, ValueError) as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    chart = chart_only(inp)
    return Response(content=to_json({k: v for k, v in chart.items() if k != "planets"}), media_type="application/json")


@router.get("/api/natal/transits")
async def api_natal_transits(request: Request):
    try:
        inp = _parse_input(request, resolve_lang(request))
    except (ValidationError, ValueError) as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    profile = build_profile(inp, reference_jd=_reference_jd(request))
    slim = {k: v for k, v in profile.items() if k != "chart"}
    return Response(content=to_json(slim), media_type="application/json")


@router.get("/api/natal/progressions")
async def api_natal_progressions(request: Request):
    try:
        inp = _parse_input(request, resolve_lang(request))
    except (ValidationError, ValueError) as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
    prog = build_progressions(inp, reference_jd=_reference_jd(request))
    slim = {k: v for k, v in prog.items() if k != "chart"}
    return Response(content=to_json(slim), media_type="application/json")
