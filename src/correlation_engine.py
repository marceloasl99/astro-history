"""
Motor de Correlações Astrológicas e Simulador Preditivo Histórico.
Versão Refinada com Asteroides e 30 Estrelas Fixas:
Analisa padrões de planetas, asteroides e estrelas fixas por categoria de evento
e compara novas cartas astrológicas com a base dos 200 fatos históricos.
"""

import json
from typing import List, Dict, Any, Optional
from collections import defaultdict
import math

from src.db import get_connection, get_all_events, get_event_by_id
from src.astro_engine import calculate_event_chart, ZODIAC_SIGNS

def get_category_correlations() -> Dict[str, Any]:
    """
    Calcula correlações estatísticas entre corpos celestes (planetas, asteroides e estrelas fixas)
    e categorias históricas, identificando as assinaturas dominantes de cada tipo de evento.
    """
    conn = get_connection()
    
    categories_res = conn.execute("SELECT DISTINCT category FROM events ORDER BY category").fetchall()
    categories = [r[0] for r in categories_res]

    results_by_category = {}

    for cat in categories:
        # Frequência de planetas e asteroides em signos nesta categoria
        rows = conn.execute("""
            SELECT p.planet_id, p.planet_name, p.category, p.sign_name, p.element, p.modality, COUNT(*) as frequency
            FROM planet_positions p
            JOIN events e ON p.event_id = e.id
            WHERE e.category = ?
            GROUP BY p.planet_id, p.sign_name
            ORDER BY p.planet_id, frequency DESC
        """, (cat,)).fetchall()

        # Aspectos estritos mais frequentes nesta categoria (orbe <= 3.0°)
        aspect_rows = conn.execute("""
            SELECT a.planet1_id, a.planet2_id, a.aspect_name, a.aspect_symbol, a.nature, COUNT(*) as frequency
            FROM event_aspects a
            JOIN events e ON a.event_id = e.id
            WHERE e.category = ?
            GROUP BY a.planet1_id, a.planet2_id, a.aspect_name
            ORDER BY frequency DESC
            LIMIT 8
        """, (cat,)).fetchall()

        # Estrelas fixas mais ativadas nesta categoria (orbe <= 0.3°)
        star_rows = conn.execute("""
            SELECT s.star_name, s.aspect_name, COUNT(*) as frequency
            FROM event_star_aspects s
            JOIN events e ON s.event_id = e.id
            WHERE e.category = ?
            GROUP BY s.star_name
            ORDER BY frequency DESC
            LIMIT 5
        """, (cat,)).fetchall()

        avg_tension = conn.execute("""
            SELECT AVG(tension_index) FROM events WHERE category = ?
        """, (cat,)).fetchone()[0] or 50.0

        total_evs = conn.execute("SELECT COUNT(*) FROM events WHERE category = ?", (cat,)).fetchone()[0]

        planets_dist = defaultdict(list)
        for r in rows:
            planets_dist[r["planet_name"]].append({
                "sign": r["sign_name"],
                "frequency": r["frequency"],
                "element": r["element"],
                "modality": r["modality"],
                "percentage": round((r["frequency"] / total_evs) * 100.0, 1)
            })

        # Destaques dos principais corpos na categoria
        key_bodies = ["Plutão", "Netuno", "Urano", "Saturno", "Marte", "Ceres", "Quíron"]
        highlights = {}
        for kb in key_bodies:
            if kb in planets_dist and len(planets_dist[kb]) > 0:
                top_pos = planets_dist[kb][0]
                highlights[kb] = f"{top_pos['sign']} ({top_pos['percentage']}% dos casos - {top_pos['element']}/{top_pos['modality']})"

        results_by_category[cat] = {
            "total_events": total_evs,
            "average_tension": round(avg_tension, 1),
            "key_highlights": highlights,
            "top_aspects": [dict(a) for a in aspect_rows],
            "top_stars": [dict(s) for s in star_rows]
        }

    # Análise de Grandes Ciclos Planetários (Saturno-Plutão, Urano-Plutão, Saturno-Urano)
    cycles_rows = conn.execute("""
        SELECT a.planet1_id, a.planet2_id, a.aspect_name, e.title, e.date, e.category, e.consequence
        FROM event_aspects a
        JOIN events e ON a.event_id = e.id
        WHERE (a.planet1_id = 'saturn' AND a.planet2_id = 'pluto')
           OR (a.planet1_id = 'uranus' AND a.planet2_id = 'pluto')
           OR (a.planet1_id = 'saturn' AND a.planet2_id = 'uranus')
        ORDER BY a.planet1_id, a.planet2_id, e.date ASC
    """).fetchall()

    major_cycles = defaultdict(list)
    for cr in cycles_rows:
        pair_key = f"{cr['planet1_id'].capitalize()}-{cr['planet2_id'].capitalize()}"
        major_cycles[pair_key].append(dict(cr))

    conn.close()

    return {
        "by_category": results_by_category,
        "major_cycles": dict(major_cycles)
    }

def find_similar_events(target_chart: Dict[str, Any], top_k: int = 5) -> Dict[str, Any]:
    """
    Compara uma carta natal (passada, presente ou futura) com os 200 eventos históricos,
    considerando planetas transpessoais, sociais, asteroides, aspectos estritos (3.0°)
    e alinhamentos idênticos com as 30 estrelas fixas (0.3°).
    """
    conn = get_connection()
    events_rows = conn.execute("""
        SELECT id, title, category, date, time, city, country, consequence,
               dominant_element, dominant_modality, tension_index, chart_json
        FROM events
        WHERE calculated = 1
    """).fetchall()
    conn.close()

    target_bodies = {b["id"]: b for b in target_chart.get("planets", [])}
    target_summary = target_chart.get("summary", {})
    target_tension = target_summary.get("tension_index", 50.0)
    target_aspect_pairs = {(a["planet1_id"], a["planet2_id"]): a["aspect_name"] for a in target_chart.get("aspects", [])}
    target_stars = {sc["star_key"]: sc for sc in target_chart.get("star_contacts", [])}

    weights = {
        "pluto": 22.0,
        "neptune": 18.0,
        "uranus": 18.0,
        "saturn": 14.0,
        "jupiter": 10.0,
        "mars": 8.0,
        "sun": 8.0,
        "moon": 5.0,
        "ceres": 4.0,
        "pallas": 3.0,
        "vesta": 3.0,
        "juno": 3.0,
        "chiron": 4.0,
        "lilith": 3.0
    }
    max_score = sum(weights.values())

    scored_events = []

    for er in events_rows:
        ev_chart = json.loads(er["chart_json"])
        ev_bodies = {b["id"]: b for b in ev_chart.get("planets", [])}
        ev_aspect_pairs = {(a["planet1_id"], a["planet2_id"]): a["aspect_name"] for a in ev_chart.get("aspects", [])}
        ev_stars = {sc["star_key"]: sc for sc in ev_chart.get("star_contacts", [])}

        current_score = 0.0
        matching_traits = []

        # 1. Proximidade de planetas e asteroides
        for b_id, w in weights.items():
            if b_id in target_bodies and b_id in ev_bodies:
                tb = target_bodies[b_id]
                eb = ev_bodies[b_id]

                ang_dist = abs(tb["longitude"] - eb["longitude"])
                if ang_dist > 180.0:
                    ang_dist = 360.0 - ang_dist

                if tb["sign_name"] == eb["sign_name"]:
                    proximity = 1.0 - (ang_dist / 60.0) if ang_dist < 60.0 else 0.5
                    proximity = max(0.6, proximity)
                    current_score += w * proximity
                    if w >= 14.0:
                        matching_traits.append(f"{tb['name']} em {tb['sign_name']} (mesmo signo)")
                elif tb["element"] == eb["element"]:
                    current_score += w * 0.45
                elif tb["modality"] == eb["modality"]:
                    current_score += w * 0.25

        # 2. Aspectos estritos compartilhados (orbe <= 3.0°)
        shared_aspects = 0
        for pair, asp_name in target_aspect_pairs.items():
            if pair in ev_aspect_pairs and ev_aspect_pairs[pair] == asp_name:
                shared_aspects += 1
                b1_name = target_bodies.get(pair[0], {}).get("name", pair[0])
                b2_name = target_bodies.get(pair[1], {}).get("name", pair[1])
                matching_traits.append(f"Aspecto comum: {b1_name} em {asp_name} com {b2_name}")

        aspect_bonus = min(20.0, shared_aspects * 5.0)
        current_score += aspect_bonus

        # 3. Estrelas fixas em comum (orbe <= 0.3°)
        for s_key in target_stars:
            if s_key in ev_stars:
                current_score += 8.0
                ts = target_stars[s_key]
                matching_traits.append(f"★ Estrela Fixa {s_key} ativada simultaneamente ({ts['body_name']})")

        # 4. Proximidade de tensão cósmica
        tension_diff = abs(target_tension - er["tension_index"])
        tension_sim = max(0.0, 10.0 - (tension_diff / 5.0))
        current_score += tension_sim

        # Normalização percentual
        total_possible = max_score + 20.0 + 10.0 + 15.0
        match_percent = round(min(98.5, max(15.0, (current_score / total_possible) * 100.0)), 1)

        scored_events.append({
            "id": er["id"],
            "title": er["title"],
            "category": er["category"],
            "date": er["date"],
            "city": er["city"],
            "country": er["country"],
            "consequence": er["consequence"],
            "tension_index": round(er["tension_index"], 1),
            "match_percent": match_percent,
            "matching_traits": matching_traits[:4]
        })

    scored_events.sort(key=lambda x: x["match_percent"], reverse=True)
    top_matches = scored_events[:top_k]

    categories_count = defaultdict(int)
    for m in top_matches:
        categories_count[m["category"]] += 1
    most_common_cat = max(categories_count, key=categories_count.get)

    avg_match_percent = round(sum(m["match_percent"] for m in top_matches) / len(top_matches), 1)

    synthesis = (
        f"Com base na assinatura astrológica calculada (incluindo asteroides e estrelas fixas), "
        f"a configuração possui alta concordância histórica ({avg_match_percent}%) com marcos da categoria '{most_common_cat}'. "
        f"Na história, conjunções com essa distribuição dos planetas transpessoais e grau de tensão "
        f"desencadearam transformações de grande impacto: "
        f"{top_matches[0]['consequence'][:220]}... "
        f"Os paralelos históricos indicam momentos de ruptura de paradigmas e transformações institucionais irreversíveis."
    )

    return {
        "top_matches": top_matches,
        "dominant_matching_category": most_common_cat,
        "avg_match_percent": avg_match_percent,
        "historical_synthesis": synthesis
    }
