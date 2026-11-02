"""
Módulo de Análise e Assinatura Astrológica Retrospectiva dos Fatos Históricos.
Calcula a assinatura celeste exata de guerras, crises econômicas, revoluções e tratados
com base nos parâmetros rigorosos da Astrologia Moderna.
"""

import json
import os
from typing import Dict, List, Any, Optional

from src.mundane.transits_engine import calculate_transits_for_date

EVENTS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "country_historical_events.json"))

_EVENTS_CACHE: Optional[List[Dict[str, Any]]] = None
_ANALYZED_HISTORY_CACHE: Dict[str, List[Dict[str, Any]]] = {}

def load_raw_historical_events() -> List[Dict[str, Any]]:
    """Carrega todos os eventos históricos da base JSON canônica."""
    global _EVENTS_CACHE
    if _EVENTS_CACHE is not None:
        return _EVENTS_CACHE

    if not os.path.exists(EVENTS_FILE):
        return []

    with open(EVENTS_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)

    _EVENTS_CACHE = events
    return _EVENTS_CACHE

def compute_event_astrological_signature(country_chart: Dict[str, Any], event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula a assinatura astrológica de um fato histórico sobre a carta natal do país.
    Extrai aspectos exatos (< 1.0°), pares arquetípicos ativados e o índice de ativação (0–1000).
    """
    event_date = event["date"]
    transits_res = calculate_transits_for_date(country_chart, event_date)
    transits = transits_res.get("transits", [])

    # Filtrar trânsitos protagonistas de planetas lentos e sociais
    major_transits = [t for t in transits if t["transit_planet_id"] in ["pluto", "neptune", "uranus", "saturn", "jupiter", "mars"]]

    # Identificar o par arquetípico mais intenso
    archetype_key = "NEUTRAL"
    protagonist_headline = "Sem trânsito protagonista isolado"
    if major_transits:
        top = major_transits[0]
        archetype_key = f"{top['transit_planet_id'].upper()}_{top['natal_planet_id'].upper()}"
        protagonist_headline = f"{top['transit_symbol']} {top['transit_planet']} {top['aspect_symbol']} {top['natal_planet']} Natal ({top['formatted_orb']})"

    return {
        "event_id": event.get("event_id"),
        "iso_code": country_chart["country_iso"],
        "title": event["title"],
        "category": event["category"],
        "date": event["date"],
        "description": event["description"],
        "historical_source": event.get("historical_source", ""),
        "severity_notes": event.get("severity_notes", ""),
        "activation_index_1000": transits_res["activation_index_1000"],
        "archetype_key": archetype_key,
        "protagonist_headline": protagonist_headline,
        "exact_aspects_count": sum(1 for t in major_transits if t["is_exact"]),
        "top_transits": major_transits[:4]
    }

def get_country_analyzed_history(country_chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Retorna a lista completa de eventos históricos de um país após sua fundação,
    com as respectivas assinaturas cósmicas calculadas.
    """
    iso = country_chart["country_iso"].upper()
    if iso in _ANALYZED_HISTORY_CACHE:
        return _ANALYZED_HISTORY_CACHE[iso]

    all_events = load_raw_historical_events()
    foundation_date = country_chart.get("date", "1800-01-01")

    # Para países com refundação constitucional pós-guerra (como Japão 1952 e Alemanha 1949),
    # permitir os grandes marcos do século XX (como Segunda Guerra e Hiroshima) que definiram a ordem contemporânea
    effective_start = "1930-01-01" if iso in ("JPN", "DEU", "ITA", "AUT", "FRA") else foundation_date

    country_events = [
        e for e in all_events
        if e.get("iso_code", "").upper() == iso and e.get("date", "") >= effective_start
    ]

    analyzed = []
    for ev in country_events:
        try:
            sig = compute_event_astrological_signature(country_chart, ev)
            analyzed.append(sig)
        except Exception:
            continue

    analyzed.sort(key=lambda x: x["date"])
    _ANALYZED_HISTORY_CACHE[iso] = analyzed
    return analyzed
