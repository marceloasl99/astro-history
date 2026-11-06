"""
Instância única de Jinja2Templates (v6) compartilhada por app.py e pelos routers,
com filtros e globais comuns: total do catálogo, formatação numérica PT, versão.
"""

import os
from functools import lru_cache

from fastapi.templating import Jinja2Templates

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TEMPLATES_DIR = os.path.join(BASE_DIR, "src", "web", "templates")
APP_VERSION = "7.0.0"

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def fmt_int(n) -> str:
    """1342 → '1.342' (separador de milhar PT)."""
    try:
        return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)


@lru_cache(maxsize=1)
def _catalog_total_cached() -> int:
    try:
        from src.db import get_connection
        conn = get_connection()
        n = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        conn.close()
        return int(n)
    except Exception:
        return 0


def catalog_total() -> int:
    return _catalog_total_cached()


def refresh_catalog_total() -> None:
    _catalog_total_cached.cache_clear()


def hist_date(d) -> str:
    """Exibe '-0490-09-12' como '12/09/490 a.C.' e datas d.C. como estão."""
    try:
        from src.core.dates import format_historical
        return format_historical(str(d)) if str(d).startswith("-") else str(d)
    except Exception:
        return str(d)


templates.env.filters["fmt_int"] = fmt_int
templates.env.filters["hist_date"] = hist_date
templates.env.globals["catalog_total"] = catalog_total
templates.env.globals["app_version"] = APP_VERSION
