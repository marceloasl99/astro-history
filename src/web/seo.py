"""
Módulo de SEO (Search Engine Optimization), Sitemap XML e Robots.txt.
Gera sitemap estático e dinâmico cobrindo rotas principais, dossiês de países e marcos históricos.
"""

from functools import lru_cache
from typing import List, Dict, Any
from datetime import datetime, timezone
import os

from src.mundane.countries_data import load_countries_data
from src.db import get_connection

BASE_URL = os.environ.get("ASTRO_SITE_URL", "https://history.skyastrum.com").rstrip("/")

MAIN_ROUTES: List[Dict[str, Any]] = [
    {"path": "/", "changefreq": "daily", "priority": "1.0"},
    {"path": "/events", "changefreq": "weekly", "priority": "0.9"},
    {"path": "/simulator", "changefreq": "weekly", "priority": "0.9"},
    {"path": "/projections", "changefreq": "weekly", "priority": "0.9"},
    {"path": "/forecast", "changefreq": "weekly", "priority": "0.9"},
    {"path": "/correlations", "changefreq": "weekly", "priority": "0.8"},
    {"path": "/countries", "changefreq": "weekly", "priority": "0.8"},
    {"path": "/natal", "changefreq": "weekly", "priority": "0.8"},
    {"path": "/methodology", "changefreq": "monthly", "priority": "0.7"},
    {"path": "/dados-fontes", "changefreq": "monthly", "priority": "0.7"},
    {"path": "/glossario", "changefreq": "monthly", "priority": "0.7"},
    {"path": "/sobre", "changefreq": "monthly", "priority": "0.7"},
]

@lru_cache(maxsize=1)
def build_sitemap_xml() -> str:
    """Gera o XML do sitemap segundo o padrão sitemaps.org/schemas/sitemap/0.9."""
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    xml_parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]

    # 1. Rotas Principais
    for item in MAIN_ROUTES:
        loc = f"{BASE_URL}{item['path']}"
        xml_parts.append(
            f"  <url>\n"
            f"    <loc>{loc}</loc>\n"
            f"    <lastmod>{today}</lastmod>\n"
            f"    <changefreq>{item['changefreq']}</changefreq>\n"
            f"    <priority>{item['priority']}</priority>\n"
            f"  </url>"
        )

    # 2. 107 Países Soberanos
    try:
        countries = load_countries_data()
        for c in countries:
            loc = f"{BASE_URL}/countries/{c['iso_code']}"
            xml_parts.append(
                f"  <url>\n"
                f"    <loc>{loc}</loc>\n"
                f"    <lastmod>{today}</lastmod>\n"
                f"    <changefreq>monthly</changefreq>\n"
                f"    <priority>0.7</priority>\n"
                f"  </url>"
            )
    except Exception:
        pass

    # 3. 3.406 Marcos Históricos Catalogados
    try:
        conn = get_connection()
        event_ids = [r[0] for r in conn.execute("SELECT id FROM events ORDER BY id ASC").fetchall()]
        conn.close()
        for eid in event_ids:
            loc = f"{BASE_URL}/events/{eid}"
            xml_parts.append(
                f"  <url>\n"
                f"    <loc>{loc}</loc>\n"
                f"    <lastmod>{today}</lastmod>\n"
                f"    <changefreq>monthly</changefreq>\n"
                f"    <priority>0.6</priority>\n"
                f"  </url>"
            )
    except Exception:
        pass

    xml_parts.append("</urlset>")
    return "\n".join(xml_parts)


def get_robots_txt() -> str:
    """Retorna a diretiva robots.txt com declaração de sitemap e bloqueio de rotas internas/API."""
    return f"""User-agent: *
Allow: /
Disallow: /api/
Disallow: /simulator/recalculate
Disallow: /web/
Disallow: /search

Sitemap: {BASE_URL}/sitemap.xml
"""
