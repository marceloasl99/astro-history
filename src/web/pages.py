"""
Páginas institucionais e de apoio (v6): /glossario, /dados-fontes, /sobre e /search.
Server-rendered, bilíngues via src/web/i18n.
"""

import os
import re
from functools import lru_cache
from typing import Any, Dict, List

import yaml
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from src.db import get_connection
from src.mundane.countries_data import search_countries
from src.web.i18n import resolve_lang, translator

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
from src.web.templating import templates  # v6: instância única
router = APIRouter(tags=["pages"])


@lru_cache(maxsize=1)
def glossary_terms() -> List[Dict[str, Any]]:
    with open(os.path.join(BASE_DIR, "data", "glossary.yaml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)["terms"]


@lru_cache(maxsize=1)
def sources_manifest() -> Dict[str, Any]:
    with open(os.path.join(BASE_DIR, "data", "sources_manifest.yml"), "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _catalog_coverage() -> Dict[str, Any]:
    conn = get_connection()
    try:
        total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        by_cat = [dict(r) for r in conn.execute("SELECT category, COUNT(*) AS n FROM events GROUP BY category ORDER BY n DESC")]
        rows = conn.execute("SELECT date FROM events").fetchall()
        try:
            by_tier = [dict(r) for r in conn.execute("SELECT COALESCE(quality_tier,'—') AS tier, COUNT(*) AS n FROM events GROUP BY tier ORDER BY n DESC")]
            by_prec = [dict(r) for r in conn.execute("SELECT COALESCE(date_precision,'day') AS p, COUNT(*) AS n FROM events GROUP BY p ORDER BY n DESC")]
            by_macro = [dict(r) for r in conn.execute("SELECT COALESCE(macro_category,'—') AS m, COUNT(*) AS n FROM events GROUP BY m ORDER BY n DESC")]
        except Exception:
            by_tier, by_prec, by_macro = [], [], []
    finally:
        conn.close()
    centuries: Dict[int, int] = {}
    for (d,) in rows:
        try:
            y = -int(d[1:5]) if d.startswith("-") else int(d[:4])
        except ValueError:
            continue
        c = (y // 100) * 100
        centuries[c] = centuries.get(c, 0) + 1
    cent = sorted(centuries.items())
    return {"total": total, "by_category": by_cat, "centuries": cent, "by_tier": by_tier, "by_precision": by_prec, "by_macro": by_macro}


def _ctx(request: Request, **kw) -> Dict[str, Any]:
    lang = resolve_lang(request)
    base = {"request": request, "lang": lang, "t": translator(lang)}
    base.update(kw)
    return base


@router.get("/glossario", response_class=HTMLResponse)
async def glossary_view(request: Request, q: str = ""):
    terms = glossary_terms()
    lang = resolve_lang(request)
    if q:
        ql = q.lower()
        terms = [t for t in terms if ql in (t["pt"] + t["en"] + t["def_pt"] + t["def_en"]).lower()]
    cats = {"astro": ("Astrologia", "Astrology"), "tempo": ("Tempo & efemérides", "Time & ephemerides"),
            "metodo": ("Método", "Method"), "stats": ("Estatística", "Statistics"), "dados": ("Dados", "Data")}
    return templates.TemplateResponse(request=request, name="glossary.html",
                                      context=_ctx(request, terms=terms, cats=cats, q=q))


@router.get("/dados-fontes", response_class=HTMLResponse)
async def sources_view(request: Request):
    manifest = sources_manifest()
    coverage = _catalog_coverage()
    from src.core.ephemeris import ephemeris_status
    return templates.TemplateResponse(request=request, name="sources.html",
                                      context=_ctx(request, manifest=manifest, coverage=coverage, ephe=ephemeris_status()))


@router.get("/sobre", response_class=HTMLResponse)
async def about_view(request: Request):
    citation = ""
    try:
        with open(os.path.join(BASE_DIR, "CITATION.cff"), "r", encoding="utf-8") as f:
            citation = f.read()
    except OSError:
        pass
    return templates.TemplateResponse(request=request, name="about.html", context=_ctx(request, citation=citation))


@router.get("/search", response_class=HTMLResponse)
async def search_view(request: Request, q: str = ""):
    q = (q or "").strip()[:120]
    results: Dict[str, Any] = {"events": [], "countries": [], "years": [], "terms": [], "pages": []}
    if q:
        conn = get_connection()
        try:
            term = f"%{q}%"
            results["events"] = [dict(r) for r in conn.execute(
                "SELECT id, title, category, date, country FROM events WHERE title LIKE ? OR consequence LIKE ? OR country LIKE ? OR city LIKE ? ORDER BY date LIMIT 60",
                (term, term, term, term))]
        finally:
            conn.close()
        results["countries"] = search_countries(q)[:12]
        for m in re.findall(r"\b(-?\d{3,4})\b", q):
            y = int(m)
            if 1800 <= y <= 2100:
                results["years"].append({"year": y, "simulator": f"/simulator?date={y:04d}-07-01&time=12:00&latitude=0&longitude=0",
                                         "events": f"/events?search={y:04d}", "forecast": f"/forecast" if y >= 2026 else None})
        ql = q.lower()
        lang = resolve_lang(request)
        results["terms"] = [t for t in glossary_terms() if ql in (t["pt"] + " " + t["en"]).lower()][:10]
        pages = [("/natal", "Mapa Natal & Trânsitos da Vida", "natal mapa pessoal trânsitos progressões"),
                 ("/methodology", "Metodologia", "modelos nulos hindcast estatística"),
                 ("/forecast", "Previsão", "previsão skill bss"), ("/projections", "Cenários", "cenários picos energia"),
                 ("/countries", "Países", "países mapas soberanos"), ("/dados-fontes", "Dados & Fontes", "fontes licenças dados"),
                 ("/glossario", "Glossário", "glossário termos")]
        results["pages"] = [{"href": h, "title": t} for h, t, kw in pages if ql in (t + " " + kw).lower()]
    return templates.TemplateResponse(request=request, name="search.html", context=_ctx(request, q=q, results=results))
