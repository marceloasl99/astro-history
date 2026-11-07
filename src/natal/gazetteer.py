"""
Gazetteer offline (GeoNames cities15000, CC BY 4.0) para autocompletar o local de nascimento
sem chamadas externas. Banco: data/gazetteer/cities.sqlite (ver scripts/build_gazetteer.py).
"""

import os
import re
import sqlite3
import unicodedata
from typing import Any, Dict, List, Optional

from src.core.timezones import resolve_zone

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DB_FILE = os.path.join(ROOT_DIR, "data", "gazetteer", "cities.sqlite")

_TOKEN_RE = re.compile(r"[^\w\s]", re.UNICODE)


def available() -> bool:
    return os.path.exists(DB_FILE)


def _strip(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _conn() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA trusted_schema = OFF;")
    return conn


def _row_to_place(r: sqlite3.Row, lang: str = "pt") -> Dict[str, Any]:
    country = r["country_pt"] if lang == "pt" else r["country_en"]
    admin = r["admin1"] or ""
    label = r["name"]
    if admin and admin != r["name"]:
        label += f", {admin}"
    label += f", {country}"
    return {
        "id": int(r["id"]), "name": r["name"], "admin1": admin, "country": country,
        "country_code": r["country_code"], "lat": round(float(r["lat"]), 4), "lon": round(float(r["lon"]), 4),
        "tz": r["tz"], "population": int(r["population"] or 0), "label": label,
    }


def search_places(query: str, limit: int = 8, lang: str = "pt") -> List[Dict[str, Any]]:
    """Busca por prefixo (sem acentos) ordenada por relevância e população."""
    if not available():
        return []
    q = _TOKEN_RE.sub(" ", _strip(query or "")).strip()
    if len(q) < 2:
        return []
    tokens = [t for t in q.split() if t]
    if not tokens:
        return []
    match = " ".join(f'"{t}"*' for t in tokens[:5])
    sql = """
        SELECT c.*, bm25(cities_fts, 10.0, 8.0, 3.0, 2.0, 1.0) AS rank
        FROM cities_fts JOIN cities c ON c.id = cities_fts.rowid
        WHERE cities_fts MATCH ?
        ORDER BY rank LIMIT 60
    """
    conn = _conn()
    try:
        rows = conn.execute(sql, (match,)).fetchall()
    except sqlite3.OperationalError:
        rows = []
    finally:
        conn.close()
    # Reordena: nome exato primeiro, depois população.
    qn = _strip(query).lower().strip()
    def key(r):
        exact = 0 if _strip(r["name"]).lower() == qn or _strip(r["ascii_name"]).lower() == qn else 1
        return (exact, -int(r["population"] or 0))
    rows = sorted(rows, key=key)
    return [_row_to_place(r, lang) for r in rows[:limit]]


def place_by_id(place_id: int, lang: str = "pt") -> Optional[Dict[str, Any]]:
    if not available():
        return None
    conn = _conn()
    try:
        r = conn.execute("SELECT * FROM cities WHERE id = ?", (int(place_id),)).fetchone()
    finally:
        conn.close()
    return _row_to_place(r, lang) if r else None


def resolve_timezone(lat: float, lon: float) -> Optional[str]:
    """Fuso IANA por coordenadas (timezonefinder); None em alto-mar."""
    return resolve_zone(lat, lon)


def stats() -> Dict[str, Any]:
    if not available():
        return {"available": False, "cities": 0}
    conn = _conn()
    try:
        n = conn.execute("SELECT COUNT(*) FROM cities").fetchone()[0]
    finally:
        conn.close()
    return {"available": True, "cities": int(n), "file": DB_FILE}
