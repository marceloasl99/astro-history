"""
Registro de corpos e pontos usados pelo módulo pessoal.

- `BODY_META`: metadados (nomes PT/EN, símbolo, id do Swiss Ephemeris, classe).
- `TRANSIT_GRID_BODIES`: corpos presentes na grade diária 1850–2150 (data/ephemeris/natal_grid_1850_2150.npz).
- Ângulos (ASC, MC, DSC, IC) não são corpos: existem só como alvos natais.
"""

from typing import Dict, Any, List

import swisseph as swe

BODY_META: Dict[str, Dict[str, Any]] = {
    "sun":        {"name_pt": "Sol",         "name_en": "Sun",        "symbol": "☉", "swe": swe.SUN,       "class": "luminary"},
    "moon":       {"name_pt": "Lua",         "name_en": "Moon",       "symbol": "☽", "swe": swe.MOON,      "class": "luminary"},
    "mercury":    {"name_pt": "Mercúrio",    "name_en": "Mercury",    "symbol": "☿", "swe": swe.MERCURY,   "class": "personal"},
    "venus":      {"name_pt": "Vênus",       "name_en": "Venus",      "symbol": "♀", "swe": swe.VENUS,     "class": "personal"},
    "mars":       {"name_pt": "Marte",       "name_en": "Mars",       "symbol": "♂", "swe": swe.MARS,      "class": "personal"},
    "jupiter":    {"name_pt": "Júpiter",     "name_en": "Jupiter",    "symbol": "♃", "swe": swe.JUPITER,   "class": "social"},
    "saturn":     {"name_pt": "Saturno",     "name_en": "Saturn",     "symbol": "♄", "swe": swe.SATURN,    "class": "social"},
    "uranus":     {"name_pt": "Urano",       "name_en": "Uranus",     "symbol": "♅", "swe": swe.URANUS,    "class": "outer"},
    "neptune":    {"name_pt": "Netuno",      "name_en": "Neptune",    "symbol": "♆", "swe": swe.NEPTUNE,   "class": "outer"},
    "pluto":      {"name_pt": "Plutão",      "name_en": "Pluto",      "symbol": "♇", "swe": swe.PLUTO,     "class": "outer"},
    "chiron":     {"name_pt": "Quíron",      "name_en": "Chiron",     "symbol": "⚷", "swe": swe.CHIRON,    "class": "centaur"},
    "north_node": {"name_pt": "Nodo Norte",  "name_en": "North Node", "symbol": "☊", "swe": swe.TRUE_NODE, "class": "node"},
    "mean_node":  {"name_pt": "Nodo Norte (médio)", "name_en": "North Node (mean)", "symbol": "☊", "swe": swe.MEAN_NODE, "class": "node"},
    "lilith":     {"name_pt": "Lilith (Lua Negra)", "name_en": "Lilith (Black Moon)", "symbol": "⚸", "swe": swe.MEAN_APOG, "class": "point"},
    "ceres":      {"name_pt": "Ceres",       "name_en": "Ceres",      "symbol": "⚳", "swe": swe.CERES,     "class": "asteroid"},
    "pallas":     {"name_pt": "Pallas",      "name_en": "Pallas",     "symbol": "⚴", "swe": swe.PALLAS,    "class": "asteroid"},
    "juno":       {"name_pt": "Juno",        "name_en": "Juno",       "symbol": "⚵", "swe": swe.JUNO,      "class": "asteroid"},
    "vesta":      {"name_pt": "Vesta",       "name_en": "Vesta",      "symbol": "⚶", "swe": swe.VESTA,     "class": "asteroid"},
}

ANGLE_META: Dict[str, Dict[str, Any]] = {
    "asc": {"name_pt": "Ascendente",     "name_en": "Ascendant",   "symbol": "AC"},
    "mc":  {"name_pt": "Meio do Céu",    "name_en": "Midheaven",   "symbol": "MC"},
    "dsc": {"name_pt": "Descendente",    "name_en": "Descendant",  "symbol": "DC"},
    "ic":  {"name_pt": "Fundo do Céu",   "name_en": "Imum Coeli",  "symbol": "IC"},
}

POINT_META: Dict[str, Dict[str, Any]] = {**BODY_META, **ANGLE_META}

SWE_IDS: Dict[str, int] = {k: v["swe"] for k, v in BODY_META.items()}

# Corpos da grade diária (ordem fixa — a grade é indexada por esta lista).
TRANSIT_GRID_BODIES: List[str] = [
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "chiron", "mean_node", "lilith",
]

NATAL_BODIES_DEFAULT: List[str] = [
    "sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn",
    "uranus", "neptune", "pluto", "chiron", "north_node", "lilith",
]
NATAL_BODIES_OPTIONAL: List[str] = ["ceres", "pallas", "juno", "vesta"]

ANGLES: List[str] = ["asc", "mc", "dsc", "ic"]

# Correspondência corpo em trânsito → ponto natal "mesmo corpo" (para retornos/ciclos).
SAME_BODY: Dict[str, str] = {b: b for b in BODY_META}
SAME_BODY["mean_node"] = "north_node"


def name(point_id: str, lang: str = "pt") -> str:
    meta = POINT_META.get(point_id)
    if not meta:
        return point_id
    return meta["name_en"] if lang == "en" else meta["name_pt"]


def symbol(point_id: str) -> str:
    meta = POINT_META.get(point_id)
    return meta["symbol"] if meta else point_id
