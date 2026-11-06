"""
Progressões secundárias: carta progredida em uma data, linha do tempo da Lua progredida
(signos, casas natais, fases, aspectos ao natal), ingressos/estações dos planetas progredidos
e séries progredidas diárias para o modo "trânsitos ao mapa progredido".

Convenção: 1 dia após o nascimento = 1 ano trópico de vida (config/natal.yaml).
"""

import math
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import swisseph as swe

from src.astro_engine import degree_to_sign_info
from src.core.ephemeris import ensure_ephe_path
from src.natal.bodies import ANGLES, SWE_IDS, name as point_name, symbol as point_symbol
from src.natal.chart import house_of, _body_entry, calculate_natal_aspects
from src.natal.config import natal_config
from src.natal.ephemeris_cache import CALC_FLAGS, jd_to_iso
from src.natal.models import BirthInput
from src.natal.transits import TROPICAL_YEAR, wrap180, wrap360

PROGRESSED_BODIES = ["sun", "moon", "mercury", "venus", "mars", "jupiter", "saturn", "uranus", "neptune", "pluto", "chiron", "north_node"]
FAST_PROGRESSED = ["sun", "mercury", "venus", "mars"]
PHASE_NAMES_PT = ["Nova", "Crescente", "Quarto Crescente", "Gibosa", "Cheia", "Disseminadora", "Quarto Minguante", "Balsâmica"]
PHASE_NAMES_EN = ["New", "Crescent", "First Quarter", "Gibbous", "Full", "Disseminating", "Last Quarter", "Balsamic"]
SIGN_NAMES = [s["name"] for s in __import__("src.astro_engine", fromlist=["ZODIAC_SIGNS"]).ZODIAC_SIGNS]


def year_length() -> float:
    return float(natal_config()["progression"]["year_length_days"])


def progressed_jd(birth_jd: float, jd_t: float) -> float:
    return birth_jd + (jd_t - birth_jd) / year_length()


def _lon_speed(body: str, jd: float) -> Tuple[float, float, float]:
    res, _ = swe.calc_ut(float(jd), SWE_IDS[body], CALC_FLAGS)
    return float(res[0]), float(res[1]), float(res[3])


def obliquity(jd: float) -> float:
    return float(swe.calc_ut(float(jd), swe.ECL_NUT)[0][0])


def armc_from_mc(mc_lon: float, eps: float) -> float:
    lam = math.radians(mc_lon)
    e = math.radians(eps)
    return wrap360(math.degrees(math.atan2(math.sin(lam) * math.cos(e), math.cos(lam))))


def progressed_angles(natal: Dict[str, Any], inp: BirthInput, jd_t: float, jd_p: float) -> Optional[Dict[str, Any]]:
    """MC progredido por arco solar (padrão) ou Naibod; ASC/cúspides derivados via houses_armc."""
    if not natal.get("angles"):
        return None
    cfg = natal_config()["progression"]
    natal_mc = natal["angles"]["mc"]["longitude"]
    sun_n = natal["points"]["sun"]
    age = (jd_t - natal["tjd_ut"]) / TROPICAL_YEAR
    if cfg.get("mc_method") == "naibod_ra":
        arc = age * float(cfg["naibod_deg_per_year"])
    else:
        sun_p = _lon_speed("sun", jd_p)[0]
        arc = wrap360(sun_p - sun_n)
    mc_p = wrap360(natal_mc + arc)
    eps = obliquity(jd_p)
    armc = armc_from_mc(mc_p, eps)
    hsys = (inp.house_system or "P").encode()
    try:
        cusps, ascmc = swe.houses_armc(armc, inp.lat, eps, hsys)
    except Exception:
        cusps, ascmc = swe.houses_armc(armc, inp.lat, eps, b"O")
    asc_p = float(ascmc[0])
    out = {}
    for k, deg in (("asc", asc_p), ("mc", mc_p), ("dsc", wrap360(asc_p + 180)), ("ic", wrap360(mc_p + 180))):
        info = degree_to_sign_info(deg)
        out[k] = {"id": k, "longitude": round(deg, 4), "degree": round(deg, 4), "formatted": info["formatted"], "sign_name": info["sign_name"],
                  "sign_symbol": info["sign_symbol"], "symbol": {"asc": "AC", "mc": "MC", "dsc": "DC", "ic": "IC"}[k]}
    return {"angles": out, "arc": round(arc, 4), "method": cfg.get("mc_method", "solar_arc"),
            "cusp_degrees": [float(c) for c in cusps[:12]]}


def progressed_chart(natal: Dict[str, Any], inp: BirthInput, jd_t: float) -> Dict[str, Any]:
    """Carta progredida completa na data `jd_t` + aspectos progredido→natal (orbe de config)."""
    ensure_ephe_path()
    lang = inp.lang
    birth_jd = natal["tjd_ut"]
    jd_p = progressed_jd(birth_jd, jd_t)
    bodies = []
    for bid in PROGRESSED_BODIES:
        lon, lat, spd = _lon_speed(bid, jd_p)
        e = _body_entry(bid, lon, lat, spd, lang)
        if natal["houses"].get("cusp_degrees"):
            e["house"] = house_of(lon, natal["houses"]["cusp_degrees"])
        bodies.append(e)
    ang = progressed_angles(natal, inp, jd_t, jd_p)
    prog_points = {b["id"]: (b["longitude"], b["speed"] / year_length()) for b in bodies}
    if ang:
        for k in ANGLES:
            prog_points[k] = (ang["angles"][k]["longitude"], 0.0)
    # aspectos progredido→natal com orbe fixa
    orb = float(natal_config()["progression"]["moon_aspect_orb"])
    aspects = []
    from src.natal.config import aspect_defs
    for pid, (lp, _) in prog_points.items():
        for nid, ln in natal["points"].items():
            for asp in aspect_defs(False):
                diff = abs(abs(wrap180(lp - ln)) - asp["angle"])
                if diff <= orb:
                    aspects.append({"progressed": pid, "natal": nid, "aspect": asp["key"], "aspect_name": asp["name"],
                                    "aspect_symbol": asp["symbol"], "family": asp["family"], "orb": round(diff, 3),
                                    "p_symbol": point_symbol(pid), "n_symbol": point_symbol(nid),
                                    "p_name": point_name(pid, lang), "n_name": point_name(nid, lang)})
    aspects.sort(key=lambda a: a["orb"])
    sun_p = prog_points["sun"][0]
    moon_p = prog_points["moon"][0]
    phase_angle = wrap360(moon_p - sun_p)
    phase_i = int(phase_angle // 45.0) % 8
    return {
        "jd_t": jd_t, "date": jd_to_iso(jd_t), "jd_progressed": jd_p, "progressed_date": jd_to_iso(jd_p),
        "age": round((jd_t - birth_jd) / TROPICAL_YEAR, 2),
        "bodies": bodies, "angles": ang, "aspects_to_natal": aspects,
        "lunation_phase": {"angle": round(phase_angle, 2), "index": phase_i,
                           "name": (PHASE_NAMES_EN if lang == "en" else PHASE_NAMES_PT)[phase_i]},
        "points": {k: v[0] for k, v in prog_points.items()},
        "planets": bodies, "houses": {"houses_available": bool(ang), "ascendant": ang["angles"]["asc"] if ang else None,
                                      "cusps": [], "system": "Progredido"},
    }


# ----------------------------------------------------------------------------- séries progredidas
def progressed_series(natal: Dict[str, Any], inp: BirthInput, axis: np.ndarray, bodies: List[str],
                      sample_days: Optional[int] = None) -> Dict[str, np.ndarray]:
    """Longitudes progredidas por dia do eixo (amostradas a cada `sample_days` e interpoladas)."""
    ensure_ephe_path()
    step = int(sample_days or natal_config()["progression"]["sample_days"])
    birth_jd = natal["tjd_ut"]
    sample = axis[::step]
    if sample[-1] != axis[-1]:
        sample = np.r_[sample, axis[-1]]
    out: Dict[str, np.ndarray] = {}
    raw = {b: np.empty(len(sample)) for b in bodies if b not in ANGLES}
    for i, jt in enumerate(sample):
        jp = progressed_jd(birth_jd, float(jt))
        for b in raw:
            raw[b][i] = _lon_speed(b, jp)[0]
    for b, arr in raw.items():
        unwrapped = np.degrees(np.unwrap(np.radians(arr)))
        out[b] = wrap360(np.interp(axis, sample, unwrapped))
    want_angles = [a for a in bodies if a in ANGLES]
    if want_angles and natal.get("angles"):
        acc = {a: np.empty(len(sample)) for a in want_angles}
        for i, jt in enumerate(sample):
            ang = progressed_angles(natal, inp, float(jt), progressed_jd(birth_jd, float(jt)))
            for a in want_angles:
                acc[a][i] = ang["angles"][a]["longitude"]
        for a, arr in acc.items():
            unwrapped = np.degrees(np.unwrap(np.radians(arr)))
            out[a] = wrap360(np.interp(axis, sample, unwrapped))
    return out


def _bisect(fn, ja: float, jb: float, tol: float = 1.0 / 24.0) -> float:
    fa = fn(ja)
    for _ in range(40):
        mid = 0.5 * (ja + jb)
        fm = fn(mid)
        if (jb - ja) < tol:
            return mid
        if fa * fm <= 0:
            jb = mid
        else:
            ja, fa = mid, fm
    return 0.5 * (ja + jb)


def _crossings(values: np.ndarray, axis: np.ndarray, boundary_fn, refine_fn, label_fn) -> List[Dict[str, Any]]:
    """Detecta mudanças de setor (signo, casa, fase) numa série amostrada e refina a data."""
    sectors = boundary_fn(values)
    out = []
    for i in np.where(sectors[:-1] != sectors[1:])[0]:
        jd_hit = refine_fn(float(axis[i]), float(axis[i + 1]), int(sectors[i]), int(sectors[i + 1]))
        out.append(label_fn(jd_hit, int(sectors[i]), int(sectors[i + 1])))
    return out


def moon_timeline(natal: Dict[str, Any], inp: BirthInput, axis: np.ndarray) -> Dict[str, Any]:
    """Lua progredida: ingressos de signo, casas natais, fases da lunação progredida e aspectos ao natal."""
    lang = inp.lang
    birth_jd = natal["tjd_ut"]
    series = progressed_series(natal, inp, axis, ["sun", "moon"], sample_days=15)
    moon = series["moon"]
    sun = series["sun"]
    cusps = natal["houses"].get("cusp_degrees") or []

    def moon_at(jt: float) -> float:
        return _lon_speed("moon", progressed_jd(birth_jd, jt))[0]

    def sun_at(jt: float) -> float:
        return _lon_speed("sun", progressed_jd(birth_jd, jt))[0]

    def age(jd):
        return round((jd - birth_jd) / TROPICAL_YEAR, 2)

    # Signos
    def refine_sign(ja, jb, s0, s1):
        boundary = (s1 * 30.0) if (s1 == (s0 + 1) % 12) else (s0 * 30.0)
        return _bisect(lambda t: wrap180(moon_at(t) - boundary), ja, jb)
    signs = _crossings(moon, axis, lambda v: (v // 30.0).astype(int), refine_sign,
                       lambda jd, s0, s1: {"date": jd_to_iso(jd), "jd": jd, "age": age(jd), "from": SIGN_NAMES[s0], "to": SIGN_NAMES[s1],
                                           "to_index": s1, "retrograde": s1 != (s0 + 1) % 12})
    # Casas natais
    houses = []
    if len(cusps) == 12:
        c = np.asarray(cusps)
        def house_sectors(v):
            return np.argmin(wrap360(v[:, None] - c[None, :]), axis=1)
        def refine_house(ja, jb, h0, h1):
            boundary = float(c[h1]) if h1 == (h0 + 1) % 12 else float(c[h0])
            return _bisect(lambda t: wrap180(moon_at(t) - boundary), ja, jb)
        houses = _crossings(moon, axis, house_sectors, refine_house,
                            lambda jd, h0, h1: {"date": jd_to_iso(jd), "jd": jd, "age": age(jd), "from": h0 + 1, "to": h1 + 1})
    # Fases (ângulo Lua−Sol progredidos em setores de 45°)
    phase_angle = wrap360(moon - sun)
    names = PHASE_NAMES_EN if lang == "en" else PHASE_NAMES_PT
    def refine_phase(ja, jb, p0, p1):
        boundary = p1 * 45.0
        return _bisect(lambda t: wrap180(wrap360(moon_at(t) - sun_at(t)) - boundary), ja, jb)
    phases = _crossings(phase_angle, axis, lambda v: (v // 45.0).astype(int) % 8, refine_phase,
                        lambda jd, p0, p1: {"date": jd_to_iso(jd), "jd": jd, "age": age(jd), "phase_index": p1, "phase": names[p1]})
    # Aspectos exatos da Lua progredida ao natal
    aspects = progressed_aspects_to_natal(natal, inp, axis, {"moon": moon}, moon_at_fn={"moon": moon_at})
    # Signo/casa atuais no início e sequência de períodos
    periods = []
    prev_jd = float(axis[0])
    prev_sign = int(moon[0] // 30.0)
    for s in signs:
        periods.append({"sign": SIGN_NAMES[prev_sign], "sign_index": prev_sign, "start": jd_to_iso(prev_jd), "end": s["date"]})
        prev_jd, prev_sign = s["jd"], s["to_index"]
    periods.append({"sign": SIGN_NAMES[prev_sign], "sign_index": prev_sign, "start": jd_to_iso(prev_jd), "end": jd_to_iso(float(axis[-1]))})
    return {"sign_ingresses": signs, "house_ingresses": houses, "phases": phases, "aspects": aspects, "sign_periods": periods,
            "series_sample": {"jd": axis[::90].tolist(), "moon": np.round(moon[::90], 2).tolist(), "sun": np.round(sun[::90], 2).tolist()}}


def progressed_aspects_to_natal(natal: Dict[str, Any], inp: BirthInput, axis: np.ndarray, series: Dict[str, np.ndarray],
                                moon_at_fn: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Aspectos exatos (orbe de config) de corpos progredidos aos pontos natais, com datas refinadas."""
    from src.natal.config import aspect_defs
    lang = inp.lang
    birth_jd = natal["tjd_ut"]
    orb = float(natal_config()["progression"]["moon_aspect_orb"])
    out = []
    for pid, arr in series.items():
        def lon_at(t, pid=pid):
            return _lon_speed(pid, progressed_jd(birth_jd, t))[0]
        for nid, ln in natal["points"].items():
            if nid == pid and pid != "moon":
                continue
            for asp in aspect_defs(False):
                for a in ([asp["angle"]] if asp["angle"] in (0, 180) else [asp["angle"], 360 - asp["angle"]]):
                    d = wrap180(arr - ln - a)
                    inorb = np.abs(d) <= orb
                    if not inorb.any():
                        continue
                    cross = np.where(np.sign(d[:-1]) * np.sign(d[1:]) < 0)[0]
                    cross = [i for i in cross if abs(d[i]) < 15.0 and i > 0]  # ignora o contato trivial no nascimento
                    for i in cross:
                        jd_hit = _bisect(lambda t: wrap180(lon_at(t) - ln - a), float(axis[i]), float(axis[i + 1]))
                        # janela em orbe ao redor do hit
                        j = i
                        while j > 0 and inorb[j - 1]:
                            j -= 1
                        k = i + 1
                        while k < len(inorb) - 1 and inorb[k + 1]:
                            k += 1
                        out.append({
                            "progressed": pid, "natal": nid, "aspect": asp["key"], "aspect_name": asp["name"],
                            "aspect_symbol": asp["symbol"], "family": asp["family"],
                            "p_symbol": point_symbol(pid), "n_symbol": point_symbol(nid),
                            "p_name": point_name(pid, lang), "n_name": point_name(nid, lang),
                            "date": jd_to_iso(jd_hit), "jd": jd_hit, "age": round((jd_hit - birth_jd) / TROPICAL_YEAR, 2),
                            "start": jd_to_iso(float(axis[j])), "end": jd_to_iso(float(axis[k])),
                        })
    out.sort(key=lambda x: x["jd"])
    return out


def progressed_ingresses(natal: Dict[str, Any], inp: BirthInput, axis: np.ndarray) -> Dict[str, Any]:
    """Mudanças de signo e estações de Sol/Mercúrio/Vênus/Marte progredidos; signos de ASC/MC progredidos."""
    lang = inp.lang
    birth_jd = natal["tjd_ut"]
    bodies = list(FAST_PROGRESSED) + (["asc", "mc"] if natal.get("angles") else [])
    series = progressed_series(natal, inp, axis, bodies, sample_days=30)
    out = {"sign_ingresses": [], "stations": []}
    for b in bodies:
        arr = series[b]
        if b in ANGLES:
            def at(t, b=b):
                ang = progressed_angles(natal, inp, t, progressed_jd(birth_jd, t))
                return ang["angles"][b]["longitude"]
        else:
            def at(t, b=b):
                return _lon_speed(b, progressed_jd(birth_jd, t))[0]
        def refine_sign(ja, jb, s0, s1, at=at):
            boundary = (s1 * 30.0) if (s1 == (s0 + 1) % 12) else (s0 * 30.0)
            return _bisect(lambda t: wrap180(at(t) - boundary), ja, jb)
        ing = _crossings(arr, axis, lambda v: (v // 30.0).astype(int), refine_sign,
                         lambda jd, s0, s1, b=b: {"body": b, "symbol": point_symbol(b), "name": point_name(b, lang),
                                                  "date": jd_to_iso(jd), "age": round((jd - birth_jd) / TROPICAL_YEAR, 2),
                                                  "from": SIGN_NAMES[s0], "to": SIGN_NAMES[s1], "retrograde": s1 != (s0 + 1) % 12})
        out["sign_ingresses"].extend(ing)
        if b in ("mercury", "venus", "mars"):
            spd = np.r_[wrap180(np.diff(arr)), 0.0]
            sgn = np.sign(spd)
            for i in np.where(sgn[:-1] * sgn[1:] < 0)[0]:
                jd_hit = float(axis[i + 1])
                out["stations"].append({"body": b, "symbol": point_symbol(b), "name": point_name(b, lang), "date": jd_to_iso(jd_hit),
                                        "age": round((jd_hit - birth_jd) / TROPICAL_YEAR, 2),
                                        "to": "retrograde" if sgn[i + 1] < 0 else "direct"})
    out["sign_ingresses"].sort(key=lambda x: x["date"])
    out["stations"].sort(key=lambda x: x["date"])
    return out
