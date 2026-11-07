"""
Módulo de Banco de Dados SQLite para persistência dos eventos históricos,
seus mapas astrais calculados, posições de planetas/asteroides, aspectos maiores
(orbe 3.0°) e alinhamentos com as 30 principais estrelas fixas (orbe 0.3°).
"""

import sqlite3
import json
import os
from functools import lru_cache
from typing import List, Dict, Any, Optional

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# v6: caminho relativo à raiz do repositório (worktrees/containers) com override por variável de ambiente.
DB_PATH = os.environ.get("ASTRO_DB_PATH") or os.path.join(ROOT_DIR, "db", "history_astrology.db")

# v6: colunas adicionais do catálogo (todas opcionais; nenhuma coluna legada é removida).
SCHEMA_V3_COLUMNS = [
    ("date_precision", "TEXT DEFAULT 'day'"),      # day | month | year | decade
    ("calendar", "TEXT"),                          # gregorian | julian | proleptic
    ("source_id", "TEXT"),                         # chave em data/sources_manifest.yml
    ("source_url", "TEXT"),
    ("quality_tier", "TEXT"),                      # A primário | B dataset acadêmico | C enciclopédico auditado
    ("macro_category", "TEXT"),                    # 7 macro-categorias (config/categories.yaml)
    ("subcategory", "TEXT"),
    ("polarity", "TEXT"),                          # disruptive | constructive | structural | neutral
    ("region", "TEXT"),
    ("magnitude", "REAL"),
    ("is_start", "INTEGER DEFAULT 1"),
    ("external_ids", "TEXT"),                      # JSON
    ("data_version", "TEXT"),
]

EVENT_LIST_COLUMNS = ("id, title, category, date, time, city, country, latitude, longitude, consequence, calculated, "
                      "tension_index, sun_sign, moon_sign, ascendant_sign, date_precision, quality_tier, macro_category, "
                      "subcategory, polarity, region, source_id, source_url, magnitude")


def get_connection():
    """Retorna uma conexão SQLite configurada com dicionários de linhas e PRAGMAs otimizados."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA cache_size = -64000;")
    conn.execute("PRAGMA mmap_size = 268435456;")
    conn.execute("PRAGMA temp_store = MEMORY;")
    return conn

def init_db():
    """Inicializa as tabelas do banco de dados se não existirem."""
    conn = get_connection()
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            time TEXT NOT NULL,
            city TEXT NOT NULL,
            country TEXT NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            consequence TEXT NOT NULL,
            calculated INTEGER DEFAULT 0,
            tjd_ut REAL,
            is_time_known INTEGER DEFAULT 0,
            dominant_element TEXT,
            dominant_modality TEXT,
            tension_index REAL,
            sun_sign TEXT,
            moon_sign TEXT,
            ascendant_sign TEXT,
            chart_json TEXT
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS planet_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            planet_id TEXT NOT NULL,
            planet_name TEXT NOT NULL,
            category TEXT DEFAULT 'planeta',
            sign_name TEXT NOT NULL,
            sign_index INTEGER NOT NULL,
            degree_in_sign REAL NOT NULL,
            abs_degree REAL NOT NULL,
            is_retrograde INTEGER NOT NULL,
            element TEXT NOT NULL,
            modality TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS event_aspects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            planet1_id TEXT NOT NULL,
            planet2_id TEXT NOT NULL,
            aspect_name TEXT NOT NULL,
            aspect_symbol TEXT NOT NULL,
            orb REAL NOT NULL,
            nature TEXT NOT NULL,
            is_outer_cycle INTEGER NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
        );
        """)

        conn.execute("""
        CREATE TABLE IF NOT EXISTS event_star_aspects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id INTEGER NOT NULL,
            body_id TEXT NOT NULL,
            body_name TEXT NOT NULL,
            body_symbol TEXT NOT NULL,
            star_key TEXT NOT NULL,
            star_name TEXT NOT NULL,
            star_bayer TEXT NOT NULL,
            aspect_name TEXT NOT NULL,
            aspect_symbol TEXT NOT NULL,
            exact_angle REAL NOT NULL,
            orb REAL NOT NULL,
            nature TEXT NOT NULL,
            FOREIGN KEY (event_id) REFERENCES events (id) ON DELETE CASCADE
        );
        """)

        # Índices para consultas rápidas
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_category ON events (category);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_date ON events (date);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_category_date ON events (category, date);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_tension ON events (tension_index);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_planets_event ON planet_positions (event_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_planets_planet_sign ON planet_positions (planet_id, sign_name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_aspects_event ON event_aspects (event_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_aspects_pair ON event_aspects (planet1_id, planet2_id, aspect_name);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_star_aspects_event ON event_star_aspects (event_id);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_star_aspects_star ON event_star_aspects (star_key);")

        # Migração de coluna se necessário
        try:
            conn.execute("ALTER TABLE planet_positions ADD COLUMN category TEXT DEFAULT 'planeta';")
        except Exception:
            pass

        # v6: esquema v3 do catálogo (proveniência, precisão, taxonomia em 2 níveis) — migração aditiva
        for col, ddl in SCHEMA_V3_COLUMNS:
            try:
                conn.execute(f"ALTER TABLE events ADD COLUMN {col} {ddl};")
            except Exception:
                pass
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_macro ON events (macro_category);")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_events_country ON events (country);")

    conn.close()

def save_calculated_event(event_dict: Dict[str, Any], chart_data: Dict[str, Any]):
    """Salva ou atualiza um evento com sua carta natal calculada."""
    conn = get_connection()
    with conn:
        bodies = chart_data.get("planets", [])
        sun_sign = next((p["sign_name"] for p in bodies if p["id"] == "sun"), None)
        moon_sign = next((p["sign_name"] for p in bodies if p["id"] == "moon"), None)
        
        asc_sign = None
        if chart_data.get("houses", {}).get("ascendant"):
            asc_sign = chart_data["houses"]["ascendant"]["sign_name"]

        summary = chart_data.get("summary", {})
        dom_elem = summary.get("dominant_element")
        dom_mode = summary.get("dominant_modality")
        tension = summary.get("tension_index")

        conn.execute("""
        INSERT INTO events (
            id, title, category, date, time, city, country,
            latitude, longitude, consequence, calculated,
            tjd_ut, is_time_known, dominant_element, dominant_modality,
            tension_index, sun_sign, moon_sign, ascendant_sign, chart_json
        ) VALUES (
            :id, :title, :category, :date, :time, :city, :country,
            :latitude, :longitude, :consequence, 1,
            :tjd_ut, :is_time_known, :dominant_element, :dominant_modality,
            :tension_index, :sun_sign, :moon_sign, :ascendant_sign, :chart_json
        ) ON CONFLICT(id) DO UPDATE SET
            title=excluded.title,
            category=excluded.category,
            date=excluded.date,
            time=excluded.time,
            city=excluded.city,
            country=excluded.country,
            latitude=excluded.latitude,
            longitude=excluded.longitude,
            consequence=excluded.consequence,
            calculated=1,
            tjd_ut=excluded.tjd_ut,
            is_time_known=excluded.is_time_known,
            dominant_element=excluded.dominant_element,
            dominant_modality=excluded.dominant_modality,
            tension_index=excluded.tension_index,
            sun_sign=excluded.sun_sign,
            moon_sign=excluded.moon_sign,
            ascendant_sign=excluded.ascendant_sign,
            chart_json=excluded.chart_json;
        """, {
            "id": event_dict["id"],
            "title": event_dict["title"],
            "category": event_dict["category"],
            "date": event_dict["date"],
            "time": event_dict["time"],
            "city": event_dict["city"],
            "country": event_dict["country"],
            "latitude": event_dict["latitude"],
            "longitude": event_dict["longitude"],
            "consequence": event_dict["consequence"],
            "tjd_ut": chart_data.get("tjd_ut"),
            "is_time_known": 1 if chart_data.get("is_time_known") else 0,
            "dominant_element": dom_elem,
            "dominant_modality": dom_mode,
            "tension_index": tension,
            "sun_sign": sun_sign,
            "moon_sign": moon_sign,
            "ascendant_sign": asc_sign,
            "chart_json": json.dumps(
                {k: v for k, v in chart_data.items() if k != "fixed_stars"},
                separators=(",", ":"),
                ensure_ascii=False
            )
        })

        # Limpar registros prévios do evento para recálculo integral
        conn.execute("DELETE FROM planet_positions WHERE event_id = ?", (event_dict["id"],))
        conn.execute("DELETE FROM event_aspects WHERE event_id = ?", (event_dict["id"],))
        conn.execute("DELETE FROM event_star_aspects WHERE event_id = ?", (event_dict["id"],))

        # Inserir corpos (planetas e asteroides)
        for b in bodies:
            conn.execute("""
            INSERT INTO planet_positions (
                event_id, planet_id, planet_name, category, sign_name, sign_index,
                degree_in_sign, abs_degree, is_retrograde, element, modality
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_dict["id"], b["id"], b["name"], b.get("category", "planeta"), b["sign_name"], b["sign_index"],
                b["degree_in_sign"], b["longitude"], 1 if b["is_retrograde"] else 0,
                b["element"], b["modality"]
            ))

        # Inserir aspectos estritos (orbe <= 3.0°)
        for a in chart_data.get("aspects", []):
            conn.execute("""
            INSERT INTO event_aspects (
                event_id, planet1_id, planet2_id, aspect_name, aspect_symbol,
                orb, nature, is_outer_cycle
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_dict["id"], a["planet1_id"], a["planet2_id"], a["aspect_name"],
                a["aspect_symbol"], a["orb"], a["nature"], 1 if a["is_outer_cycle"] else 0
            ))

        # Inserir alinhamentos com estrelas fixas (orbe <= 0.3°)
        for sc in chart_data.get("star_contacts", []):
            conn.execute("""
            INSERT INTO event_star_aspects (
                event_id, body_id, body_name, body_symbol, star_key, star_name,
                star_bayer, aspect_name, aspect_symbol, exact_angle, orb, nature
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                event_dict["id"], sc["body_id"], sc["body_name"], sc["body_symbol"],
                sc["star_key"], sc["star_name"], sc["star_bayer"], sc["aspect_name"],
                sc["aspect_symbol"], sc["exact_angle"], sc["orb"], sc["nature"]
            ))

    conn.close()

def get_event_by_id(event_id: int) -> Optional[Dict[str, Any]]:
    """Recupera um evento completo com seu chart_json parsed."""
    conn = get_connection()
    row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    conn.close()
    if not row:
        return None
    d = dict(row)
    if d.get("chart_json"):
        d["chart"] = json.loads(d["chart_json"])
    return d

def _event_filters(category=None, search=None, macro=None, tier=None, precision=None, polarity=None, country=None,
                   century_from=None, century_to=None, time_known=None):
    """Cláusulas WHERE e parâmetros comuns ao catálogo facetado (v6)."""
    clauses, params = [], []
    if category and category != "Todas":
        clauses.append("category = ?"); params.append(category)
    if search:
        clauses.append("(title LIKE ? OR consequence LIKE ? OR city LIKE ? OR country LIKE ?)")
        term = f"%{search}%"; params.extend([term, term, term, term])
    if macro:
        clauses.append("macro_category = ?"); params.append(macro)
    if tier:
        clauses.append("quality_tier = ?"); params.append(tier)
    if precision:
        clauses.append("COALESCE(date_precision,'day') = ?"); params.append(precision)
    if polarity:
        clauses.append("polarity = ?"); params.append(polarity)
    if country:
        clauses.append("country = ?"); params.append(country)
    if time_known is not None:
        clauses.append("is_time_known = ?"); params.append(1 if time_known else 0)
    # Século: datas a.C. começam com '-' e ordenam antes; usa expressão de ano histórico.
    year_expr = "CASE WHEN substr(date,1,1)='-' THEN -CAST(substr(date,2,4) AS INTEGER) ELSE CAST(substr(date,1,4) AS INTEGER) END"
    if century_from is not None:
        clauses.append(f"{year_expr} >= ?"); params.append(int(century_from))
    if century_to is not None:
        clauses.append(f"{year_expr} <= ?"); params.append(int(century_to))
    where = (" WHERE " + " AND ".join(clauses)) if clauses else ""
    return where, params, year_expr


def get_all_events(category: Optional[str] = None, search: Optional[str] = None, **filters) -> List[Dict[str, Any]]:
    """Lista eventos (ordem cronológica) com filtros opcionais; aceita os filtros facetados de v6."""
    conn = get_connection()
    where, params, year_expr = _event_filters(category, search, **filters)
    rows = conn.execute(f"SELECT {EVENT_LIST_COLUMNS} FROM events{where} ORDER BY {year_expr} ASC, date ASC", params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_featured_events(ids: Optional[List[int]] = None) -> List[Dict[str, Any]]:
    """Carrega eventos em destaque por IDs sem escanear a tabela inteira (otimização de alta performance)."""
    featured_ids = ids or [100, 107, 93, 134, 156, 171]
    conn = get_connection()
    placeholders = ",".join("?" * len(featured_ids))
    rows = conn.execute(f"SELECT {EVENT_LIST_COLUMNS} FROM events WHERE id IN ({placeholders})", featured_ids).fetchall()
    conn.close()
    res = [dict(r) for r in rows]
    if len(res) < len(featured_ids):
        all_evs = get_all_events()
        return all_evs[:len(featured_ids)]
    return res


def get_events_page(page: int = 1, per_page: int = 50, sort: str = "date", **filters) -> Dict[str, Any]:
    """Página do catálogo facetado (v6): itens, total e contagens por faceta para os filtros atuais."""
    conn = get_connection()
    where, params, year_expr = _event_filters(**filters)
    order = {"date": f"{year_expr} ASC, date ASC", "date_desc": f"{year_expr} DESC, date DESC",
             "tension": "tension_index DESC", "title": "title COLLATE NOCASE ASC"}.get(sort, f"{year_expr} ASC, date ASC")
    total = conn.execute(f"SELECT COUNT(*) FROM events{where}", params).fetchone()[0]
    page = max(1, page)
    pages = max(1, (total + per_page - 1) // per_page)
    page = min(page, pages)
    rows = conn.execute(f"SELECT {EVENT_LIST_COLUMNS} FROM events{where} ORDER BY {order} LIMIT ? OFFSET ?",
                        params + [per_page, (page - 1) * per_page]).fetchall()

    def facet(expr: str, limit: int = 40):
        q = f"SELECT {expr} AS k, COUNT(*) AS n FROM events{where} GROUP BY k ORDER BY n DESC LIMIT {limit}"
        return [{"key": r[0], "n": r[1]} for r in conn.execute(q, params).fetchall() if r[0] is not None]

    facets = {
        "category": facet("category"),
        "macro": facet("macro_category"),
        "tier": facet("quality_tier"),
        "precision": facet("COALESCE(date_precision,'day')"),
        "polarity": facet("polarity"),
        "country": facet("country", 30),
        "century": [{"key": r[0], "n": r[1]} for r in conn.execute(
            f"SELECT ({year_expr})/100*100 AS c, COUNT(*) AS n FROM events{where} GROUP BY c ORDER BY c", params).fetchall()],
        "time_known": facet("is_time_known"),
    }
    conn.close()
    return {"items": [dict(r) for r in rows], "total": total, "page": page, "pages": pages, "per_page": per_page, "facets": facets}

def get_validated_sample_dates() -> set:
    """Datas (YYYY-MM-DD) dos eventos do catálogo objetivo v2 usados na validação (N=59, 1800–2025)."""
    conn = get_connection()
    try:
        rows = conn.execute("""
            SELECT event_date FROM events_v2
            WHERE date_precision = 'day' AND event_date >= '1800-01-01' AND event_date <= '2025-12-31'
        """).fetchall()
    except Exception:
        rows = []
    conn.close()
    return {r[0] for r in rows}

@lru_cache(maxsize=1)
def _get_events_stats_cached() -> Dict[str, Any]:
    """Retorna estatísticas globais para o dashboard com estrelas fixas e asteroides (em cache de memória)."""
    conn = get_connection()
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    calculated = conn.execute("SELECT COUNT(*) FROM events WHERE calculated = 1").fetchone()[0]
    
    cat_rows = conn.execute("SELECT category, COUNT(*) as cnt FROM events GROUP BY category ORDER BY cnt DESC").fetchall()
    categories = [dict(r) for r in cat_rows]

    sun_signs = conn.execute("SELECT sun_sign, COUNT(*) as cnt FROM events WHERE sun_sign IS NOT NULL GROUP BY sun_sign ORDER BY cnt DESC").fetchall()
    
    avg_tension = conn.execute("SELECT AVG(tension_index) FROM events WHERE calculated = 1").fetchone()[0] or 0.0

    total_star_contacts = conn.execute("SELECT COUNT(*) FROM event_star_aspects").fetchone()[0]

    conn.close()
    return {
        "total_events": total,
        "calculated_events": calculated,
        "progress_percent": round((calculated / total * 100.0) if total > 0 else 0, 1),
        "categories": categories,
        "sun_signs_distribution": [dict(r) for r in sun_signs],
        "average_tension": round(avg_tension, 1),
        "total_star_contacts": total_star_contacts
    }

def get_events_stats(force_refresh: bool = False) -> Dict[str, Any]:
    """Retorna estatísticas globais para o dashboard com suporte a cache em memória."""
    if force_refresh:
        _get_events_stats_cached.cache_clear()
    return _get_events_stats_cached()
