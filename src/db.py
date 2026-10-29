"""
Módulo de Banco de Dados SQLite para persistência dos eventos históricos,
seus mapas astrais calculados, posições de planetas/asteroides, aspectos maiores
(orbe 3.0°) e alinhamentos com as 30 principais estrelas fixas (orbe 0.3°).
"""

import sqlite3
import json
import os
from typing import List, Dict, Any, Optional

DB_PATH = "/home/astro/db/history_astrology.db"

def get_connection():
    """Retorna uma conexão SQLite configurada com dicionários de linhas."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
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
            "chart_json": json.dumps(chart_data, ensure_ascii=False)
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

def get_all_events(category: Optional[str] = None, search: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lista eventos com filtros opcionais de categoria e busca textual."""
    conn = get_connection()
    query = "SELECT id, title, category, date, time, city, country, latitude, longitude, consequence, calculated, tension_index, sun_sign, moon_sign, ascendant_sign FROM events WHERE 1=1"
    params = []

    if category and category != "Todas":
        query += " AND category = ?"
        params.append(category)

    if search:
        query += " AND (title LIKE ? OR consequence LIKE ? OR city LIKE ? OR country LIKE ?)"
        term = f"%{search}%"
        params.extend([term, term, term, term])

    query += " ORDER BY date ASC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_events_stats() -> Dict[str, Any]:
    """Retorna estatísticas globais para o dashboard com estrelas fixas e asteroides."""
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
