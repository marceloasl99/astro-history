"""
Carta natal do módulo pessoal: reaproveita o motor astronômico (Swiss Ephemeris) do projeto,
acrescentando sistema de casas selecionável, ângulos (ASC/MC/DSC/IC), posição em casa,
aspectos natais com orbes modernas por classe e tratamento explícito de hora desconhecida.
"""

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import swisseph as swe

from src.astro_engine import (
    degree_to_sign_info,
    calculate_fixed_stars,
    calculate_fixed_star_aspects,
)
from src.core.ephemeris import ensure_ephe_path
from src.core.timezones import local_to_ut, resolve_zone
from src.natal.bodies import (
    BODY_META, ANGLE_META, ANGLES, NATAL_BODIES_DEFAULT, SWE_IDS, name as point_name, symbol as point_symbol,
)
from src.natal.config import natal_config, aspect_defs
from src.natal.ephemeris_cache import CALC_FLAGS, jd_to_iso_time
from src.natal.models import BirthInput

# Classe → categoria usada pelo renderizador de mandala do projeto (cores dos glifos).
MANDALA_CATEGORY = {"luminary": "luminar", "personal": "pessoal", "social": "social", "outer": "transpessoal",
                    "centaur": "centauro", "node": "nodo", "point": "ponto", "asteroid": "asteroide"}

HOUSE_SYSTEM_NAMES = {"P": "Placidus", "K": "Koch", "W": "Signos Inteiros", "E": "Igual (ASC)", "O": "Porphyry"}

# Pesos para elementos/modalidades dominantes (convenção moderna).
DOMINANCE_WEIGHTS = {
    "sun": 3.0, "moon": 3.0, "asc": 3.0, "mc": 2.0, "mercury": 2.0, "venus": 2.0, "mars": 2.0,
    "jupiter": 1.5, "saturn": 1.5, "uranus": 1.0, "neptune": 1.0, "pluto": 1.0,
}


def wrap180(x):
    return (x + 180.0) % 360.0 - 180.0


def wrap360(x):
    return x % 360.0


# ----------------------------------------------------------------------------- instante
def birth_instant(inp: BirthInput) -> Dict[str, Any]:
    """Converte data/hora civil local em JD UT. Hora desconhecida → 12:00 local, sem casas."""
    y, m, d = (int(x) for x in inp.date.split("-"))
    if inp.time_known:
        hh, mm = (int(x) for x in inp.time.split(":"))
    else:
        hh, mm = 12, 0
    local_hour = hh + mm / 60.0
    zone = inp.tz or resolve_zone(inp.lat, inp.lon)
    conv = local_to_ut(y, m, d, local_hour, inp.lat, inp.lon, zone=zone)
    tjd = swe.julday(conv["year"], conv["month"], conv["day"], conv["ut_hour"], swe.GREG_CAL)
    return {
        "tjd_ut": tjd,
        "ut_iso": jd_to_iso_time(tjd),
        "local_date": inp.date,
        "local_time": inp.time if inp.time_known else None,
        "is_time_known": inp.time_known,
        "zone": zone,
        "tz_source": conv["tz_source"],
        "utc_offset_hours": conv["utc_offset_hours"],
    }


# ----------------------------------------------------------------------------- corpos
def _body_entry(bid: str, lon: float, lat: float, speed: float, lang: str) -> Dict[str, Any]:
    info = degree_to_sign_info(lon)
    meta = BODY_META[bid]
    return {
        "id": bid,
        "name": meta["name_en"] if lang == "en" else meta["name_pt"],
        "symbol": meta["symbol"],
        "class": meta["class"],
        "category": MANDALA_CATEGORY.get(meta["class"], "planeta"),
        "longitude": round(float(lon), 4),
        "latitude": round(float(lat), 4),
        "speed": round(float(speed), 5),
        "is_retrograde": bool(speed < 0.0),
        "sign_name": info["sign_name"],
        "sign_symbol": info["sign_symbol"],
        "sign_index": info["sign_index"],
        "degree_in_sign": info["degree_in_sign"],
        "formatted": info["formatted"],
        "short_formatted": info["short_formatted"],
        "element": info["element"],
        "modality": info["modality"],
        "ruler": info["ruler"],
        "house": None,
    }


def calculate_bodies(tjd_ut: float, bodies: List[str], lang: str = "pt") -> List[Dict[str, Any]]:
    ensure_ephe_path()
    out = []
    for bid in bodies:
        try:
            res, _ = swe.calc_ut(tjd_ut, SWE_IDS[bid], CALC_FLAGS)
        except Exception:
            continue
        out.append(_body_entry(bid, res[0], res[1], res[3], lang))
    return out


# ----------------------------------------------------------------------------- casas
def calculate_houses_system(tjd_ut: float, lat: float, lon: float, hsys: str = "P") -> Dict[str, Any]:
    """Casas no sistema pedido, com fallback polar (Porphyry → Signos Inteiros) como no motor de eventos."""
    ensure_ephe_path()
    system_used = HOUSE_SYSTEM_NAMES.get(hsys, hsys)
    code = hsys.encode()
    try:
        cusps, ascmc = swe.houses_ex2(tjd_ut, lat, lon, code)[:2]
        if any(c != c for c in cusps) or len(set(round(c, 3) for c in cusps)) < 12:
            raise ValueError("cúspides degeneradas")
    except Exception:
        try:
            cusps, ascmc = swe.houses(tjd_ut, lat, lon, b"O")
            system_used = "Porphyry (fallback polar)"
        except Exception:
            cusps, ascmc = swe.houses(tjd_ut, lat, lon, b"W")
            system_used = "Signos Inteiros (fallback polar)"
    asc, mc, armc = float(ascmc[0]), float(ascmc[1]), float(ascmc[2])
    cusp_list = [float(c) for c in cusps[:12]]
    angles = {
        "asc": asc, "mc": mc, "dsc": wrap360(asc + 180.0), "ic": wrap360(mc + 180.0),
    }
    angle_entries = {}
    for k, deg in angles.items():
        info = degree_to_sign_info(deg)
        angle_entries[k] = {
            "id": k, "symbol": ANGLE_META[k]["symbol"], "longitude": round(deg, 4), "degree": round(deg, 4),
            "sign_name": info["sign_name"], "sign_symbol": info["sign_symbol"], "sign_index": info["sign_index"],
            "degree_in_sign": info["degree_in_sign"], "formatted": info["formatted"], "element": info["element"],
            "modality": info["modality"],
        }
    cusps_out = []
    for i, c in enumerate(cusp_list):
        info = degree_to_sign_info(c)
        cusps_out.append({"house": i + 1, "degree": round(c, 4), "sign_name": info["sign_name"],
                          "sign_symbol": info["sign_symbol"], "formatted": info["formatted"]})
    return {
        "houses_available": True, "system": system_used, "system_code": hsys, "armc": round(armc, 4),
        "cusps": cusps_out, "cusp_degrees": cusp_list, "angles": angle_entries,
        "ascendant": angle_entries["asc"], "midheaven": angle_entries["mc"],
    }


def house_of(lon: float, cusps: List[float]) -> int:
    """Casa (1–12) que contém a longitude, para cúspides em graus."""
    offsets = [wrap360(lon - c) for c in cusps]
    return int(np.argmin(offsets)) + 1


# ----------------------------------------------------------------------------- aspectos natais
def _class_orb(pid: str) -> float:
    orbs = natal_config()["natal_aspect_orbs"]
    cls = BODY_META.get(pid, {}).get("class")
    if cls == "luminary":
        return float(orbs["luminaries"])
    if cls in ("personal", "social", "outer"):
        return float(orbs["planets"])
    return float(orbs["points"])


def calculate_natal_aspects(points: Dict[str, Tuple[float, float]], include_minor: bool = False,
                            lang: str = "pt") -> List[Dict[str, Any]]:
    """points: id → (longitude, speed). Ângulos entram com velocidade 0 e orbe de 'pontos'."""
    ids = list(points.keys())
    out = []
    aspects = aspect_defs(include_minor)
    for i in range(len(ids)):
        for j in range(i + 1, len(ids)):
            a, b = ids[i], ids[j]
            if a in ANGLES and b in ANGLES:
                continue
            la, va = points[a]
            lb, vb = points[b]
            orb_max = (_class_orb(a) + _class_orb(b)) / 2.0
            sep = abs(wrap180(la - lb))
            for asp in aspects:
                o = orb_max * (0.5 if asp.get("minor") else 1.0)
                diff = abs(sep - asp["angle"])
                if diff <= o:
                    d = wrap180(la - lb - asp["angle"]) if abs(wrap180(la - lb - asp["angle"])) <= o else wrap180(la - lb + asp["angle"])
                    applying = bool(d * (va - vb) < 0)
                    out.append({
                        "p1": a, "p2": b, "planet1_id": a, "planet2_id": b,
                        "nature": {"challenging": "tenso", "flowing": "harmonico", "focus": "intenso"}[asp["family"]],
                        "p1_name": point_name(a, lang), "p2_name": point_name(b, lang),
                        "p1_symbol": point_symbol(a), "p2_symbol": point_symbol(b),
                        "aspect": asp["key"], "aspect_name": asp["name"], "aspect_symbol": asp["symbol"],
                        "angle": asp["angle"], "family": asp["family"], "orb": round(diff, 3), "orb_max": round(o, 2),
                        "applying": applying, "minor": bool(asp.get("minor", False)),
                    })
                    break
    out.sort(key=lambda x: x["orb"])
    return out


# ----------------------------------------------------------------------------- resumo
def summarize(bodies: List[Dict[str, Any]], angles: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    elements = {"Fogo": 0.0, "Terra": 0.0, "Ar": 0.0, "Água": 0.0}
    modalities = {"Cardinal": 0.0, "Fixo": 0.0, "Mutável": 0.0}
    for b in bodies:
        w = DOMINANCE_WEIGHTS.get(b["id"])
        if w:
            elements[b["element"]] += w
            modalities[b["modality"]] += w
    if angles:
        for k in ("asc", "mc"):
            w = DOMINANCE_WEIGHTS[k]
            elements[angles[k]["element"]] += w
            modalities[angles[k]["modality"]] += w
    retro = [b["id"] for b in bodies if b["is_retrograde"] and b["class"] in ("personal", "social", "outer", "centaur")]
    hemispheres = None
    if angles:
        asc = angles["asc"]["longitude"]
        mc = angles["mc"]["longitude"]
        east = sum(1 for b in bodies if b["class"] in ("luminary", "personal", "social", "outer")
                   and wrap360(b["longitude"] - asc) > 180.0)
        south = sum(1 for b in bodies if b["class"] in ("luminary", "personal", "social", "outer")
                    and wrap360(b["longitude"] - mc) > 180.0)
        total = sum(1 for b in bodies if b["class"] in ("luminary", "personal", "social", "outer"))
        hemispheres = {"east": east, "west": total - east, "south": south, "north": total - south}
    return {
        "elements": {k: round(v, 1) for k, v in elements.items()},
        "modalities": {k: round(v, 1) for k, v in modalities.items()},
        "dominant_element": max(elements, key=elements.get),
        "dominant_modality": max(modalities, key=modalities.get),
        "retrograde": retro,
        "hemispheres": hemispheres,
    }


# ----------------------------------------------------------------------------- carta completa
def moon_uncertainty(inp: BirthInput, zone: Optional[str]) -> Dict[str, float]:
    """Faixa da Lua natal no dia civil (hora desconhecida): posição às 00:00 e 23:59 locais."""
    y, m, d = (int(x) for x in inp.date.split("-"))
    lons = []
    for h in (0.0, 23.983):
        conv = local_to_ut(y, m, d, h, inp.lat, inp.lon, zone=zone)
        tjd = swe.julday(conv["year"], conv["month"], conv["day"], conv["ut_hour"], swe.GREG_CAL)
        lons.append(swe.calc_ut(tjd, swe.MOON, CALC_FLAGS)[0][0])
    amp = wrap360(lons[1] - lons[0])
    return {"min": round(lons[0], 3), "max": round(lons[1], 3), "amplitude": round(amp, 3), "center": round(wrap360(lons[0] + amp / 2.0), 3)}


def calculate_natal_chart(inp: BirthInput) -> Dict[str, Any]:
    ensure_ephe_path()
    lang = inp.lang
    inst = birth_instant(inp)
    tjd = inst["tjd_ut"]
    body_ids = list(NATAL_BODIES_DEFAULT) + [b for b in inp.extra_natal if b not in NATAL_BODIES_DEFAULT]
    bodies = calculate_bodies(tjd, body_ids, lang)

    houses: Dict[str, Any]
    angles = None
    if inp.time_known:
        houses = calculate_houses_system(tjd, inp.lat, inp.lon, inp.house_system)
        angles = houses["angles"]
        for b in bodies:
            b["house"] = house_of(b["longitude"], houses["cusp_degrees"])
    else:
        houses = {"houses_available": False, "system": "Sem casas (hora desconhecida)", "system_code": None,
                  "cusps": [], "cusp_degrees": [], "angles": None, "ascendant": None, "midheaven": None}

    points: Dict[str, Tuple[float, float]] = {b["id"]: (b["longitude"], b["speed"]) for b in bodies}
    if angles:
        for k in ANGLES:
            points[k] = (angles[k]["longitude"], 0.0)
    aspects = calculate_natal_aspects(points, include_minor=inp.minors, lang=lang)

    star_bodies = [b for b in bodies if b["class"] in ("luminary", "personal", "social", "outer")]
    try:
        stars = calculate_fixed_stars(tjd)
        star_contacts = calculate_fixed_star_aspects(star_bodies, stars)
    except Exception:
        star_contacts = []

    moon_range = None if inp.time_known else moon_uncertainty(inp, inst["zone"])

    chart = {
        "input": inp.model_dump(),
        "instant": inst,
        "bodies": bodies,
        "houses": houses,
        "angles": angles,
        "aspects": aspects,
        "star_contacts": star_contacts,
        "moon_range": moon_range,
        "summary": summarize(bodies, angles),
        "precision": "exact_time" if inp.time_known else "unknown_time",
        "points": {k: v[0] for k, v in points.items()},
        "point_speeds": {k: v[1] for k, v in points.items()},
        # Compatibilidade com o renderizador de mandala do projeto:
        "planets": bodies,
        "tjd_ut": tjd,
        "is_time_known": inp.time_known,
    }
    return chart
