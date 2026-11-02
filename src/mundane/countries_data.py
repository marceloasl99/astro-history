"""
Módulo de Acesso à Base Canônica de Países para Astrologia Mundana.
Cada país possui um único mapa natal oficial (certidão de fundação/independência).
"""

import json
import os
from typing import List, Dict, Any, Optional

DATA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "countries_database.json"))

_COUNTRIES_CACHE: Optional[List[Dict[str, Any]]] = None
_COUNTRIES_MAP: Optional[Dict[str, Dict[str, Any]]] = None

def load_countries_data() -> List[Dict[str, Any]]:
    """Carrega todos os países da base JSON canônica com cache em memória."""
    global _COUNTRIES_CACHE, _COUNTRIES_MAP
    if _COUNTRIES_CACHE is not None:
        return _COUNTRIES_CACHE

    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        countries = json.load(f)

    _COUNTRIES_CACHE = countries
    _COUNTRIES_MAP = {c["iso_code"].upper(): c for c in countries}
    return _COUNTRIES_CACHE

def get_all_countries() -> List[Dict[str, Any]]:
    """Retorna a lista completa de países ordenados alfabeticamente por nome em português."""
    return load_countries_data()

def get_country_by_iso(iso_code: str) -> Optional[Dict[str, Any]]:
    """Busca um país pelo código ISO 3166-1 alfa-3 (ex: 'BRA', 'USA')."""
    load_countries_data()
    if not _COUNTRIES_MAP or not iso_code:
        return None
    return _COUNTRIES_MAP.get(iso_code.strip().upper())

def get_continents() -> List[str]:
    """Retorna a lista única de continentes presentes na base."""
    countries = load_countries_data()
    continents = sorted(list(set(c.get("continent", "") for c in countries if c.get("continent"))))
    return continents

def search_countries(query: str = "", continent: str = "") -> List[Dict[str, Any]]:
    """Filtra países por texto de busca (nome em PT/EN ou código) e continente."""
    countries = load_countries_data()
    q = query.strip().lower()
    cont = continent.strip().lower()

    filtered = []
    for c in countries:
        if cont and cont != "todos" and c.get("continent", "").lower() != cont:
            continue
        if q:
            name_pt = c.get("name_pt", "").lower()
            name_en = c.get("name_en", "").lower()
            iso = c.get("iso_code", "").lower()
            event = c.get("foundation_event", "").lower()
            if q not in name_pt and q not in name_en and q not in iso and q not in event:
                continue
        filtered.append(c)
    return filtered
