"""
Orquestrador do módulo pessoal: a partir de um BirthInput produz o perfil completo
(carta natal, trânsitos de vida, ciclos, domínios, "agora", progressões) com cache em memória.

Nada é persistido em disco: o cache é um dicionário LRU com TTL (config privacy).
"""

import time
from collections import OrderedDict
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import swisseph as swe

from src.core.ephemeris import ephemeris_status
from src.natal.chart import calculate_natal_chart
from src.natal.config import natal_config
from src.natal.cycles import label_cycles
from src.natal.domains import (
    active_now, annual_totals, classify_windows, domain_meta, key_years, monthly_domain_series, scored_series,
)
from src.natal.ephemeris_cache import jd_to_iso
from src.natal.interpretations import describe_window, describe_cycle
from src.natal.models import BirthInput
from src.natal.progressions import moon_timeline, progressed_chart, progressed_ingresses, progressed_series
from src.natal.transits import (
    TROPICAL_YEAR, Targets, lifetime_axis, scan_house_ingresses, scan_transits, strip_internal,
)

_CACHE: "OrderedDict[str, Tuple[float, Dict[str, Any]]]" = OrderedDict()


def _cache_get(key: str) -> Optional[Dict[str, Any]]:
    cfg = natal_config()["privacy"]
    item = _CACHE.get(key)
    if not item:
        return None
    ts, value = item
    if time.time() - ts > float(cfg["cache_ttl_seconds"]):
        _CACHE.pop(key, None)
        return None
    _CACHE.move_to_end(key)
    return value


def _cache_put(key: str, value: Dict[str, Any]) -> None:
    cfg = natal_config()["privacy"]
    _CACHE[key] = (time.time(), value)
    while len(_CACHE) > int(cfg["cache_max_entries"]):
        _CACHE.popitem(last=False)


def clear_cache() -> None:
    _CACHE.clear()


def now_jd() -> float:
    import datetime as _dt
    n = _dt.datetime.now(_dt.timezone.utc)
    return swe.julday(n.year, n.month, n.day, n.hour + n.minute / 60.0, swe.GREG_CAL)


def _target_ids(inp: BirthInput, chart: Dict[str, Any]) -> List[str]:
    cfg = natal_config()
    ids = inp.targets or cfg["targets"]["natal_default"]
    return [t for t in ids if t in chart["points"]]


def _targets(inp: BirthInput, chart: Dict[str, Any], axis: np.ndarray, ids: List[str]) -> Targets:
    extra = {}
    if not inp.time_known and chart.get("moon_range"):
        extra["moon"] = float(natal_config()["unknown_time"]["moon_orb_extra_factor"]) * chart["moon_range"]["amplitude"]
    if inp.target_mode == "progressed":
        series = progressed_series(chart, inp, axis, ids)
        values = {k: series[k] for k in ids if k in series}
    else:
        values = {k: chart["points"][k] for k in ids}
    return Targets(axis, values, extra_orb=extra)


def _year_axis(birth_jd: float, year: int, axis: np.ndarray) -> np.ndarray:
    y0 = swe.julday(year, 1, 1, 0.0, swe.GREG_CAL)
    y1 = swe.julday(year, 12, 31, 0.0, swe.GREG_CAL)
    lo, hi = max(y0, float(axis[0])), min(y1, float(axis[-1]))
    if hi < lo:
        lo, hi = float(axis[0]), min(float(axis[0]) + 365.0, float(axis[-1]))
    return axis[(axis >= lo) & (axis <= hi)]


def build_profile(inp: BirthInput, reference_jd: Optional[float] = None, include_detail: bool = True) -> Dict[str, Any]:
    """Perfil completo de trânsitos (vida inteira + ano em foco). Cacheado por hash dos parâmetros."""
    ref_jd = reference_jd if reference_jd is not None else now_jd()
    ref_day = jd_to_iso(ref_jd)
    key = f"profile:{inp.cache_key()}:{ref_day}:{int(include_detail)}"
    cached = _cache_get(key)
    if cached:
        cached["meta"]["cached"] = True
        return cached

    t0 = time.time()
    cfg = natal_config()
    lang = inp.lang
    chart = calculate_natal_chart(inp)
    birth_jd = chart["tjd_ut"]
    years = float(cfg["lifetime_years"])
    axis = lifetime_axis(birth_jd, years, inp.range_from, inp.range_to)
    ids = _target_ids(inp, chart)
    targets = _targets(inp, chart, axis, ids)

    lifetime_bodies = inp.bodies or cfg["transit_bodies"]["lifetime"]
    lifetime_bodies = [b for b in lifetime_bodies if b != "moon"]
    res = scan_transits(targets, birth_jd=birth_jd, bodies=lifetime_bodies, preset=inp.orb_preset,
                        custom_orbs=inp.orbs, include_minor=inp.minors, mode=inp.target_mode, lang=lang)
    windows = res["windows"]
    natal_houses = {b["id"]: b.get("house") for b in chart["bodies"]}
    classify_windows(windows, natal_houses, lang)
    cycles = label_cycles(windows, lang)
    cycles = [c for c in cycles if c["age"] >= 1.0 or c["body"] in ("sun", "mars")]
    for w in windows:
        w["text"] = describe_window(w, lang)
    for c in cycles:
        c["text"] = describe_cycle(c, lang)

    monthly = monthly_domain_series(windows, axis)
    annual = annual_totals(monthly)
    scored = scored_series(monthly, annual)
    kyears = key_years(annual, scored, windows)

    house_tr = []
    if chart["houses"].get("cusp_degrees") and inp.target_mode == "natal":
        house_tr = scan_house_ingresses(chart["houses"]["cusp_degrees"], axis, cfg["house_transits"]["bodies"], birth_jd, lang)

    # Ano em foco (corpos rápidos)
    detail: Dict[str, Any] = {"year": None, "windows": [], "bodies": []}
    focus_year = inp.focus_year
    life_y0, life_y1 = int(jd_to_iso(axis[0])[:4]), int(jd_to_iso(axis[-1])[:4])
    if focus_year is None:
        ref_year = int(ref_day[:4])
        focus_year = ref_year if life_y0 <= ref_year <= life_y1 else life_y0
    focus_year = max(life_y0, min(life_y1, focus_year))
    if include_detail:
        yaxis = _year_axis(birth_jd, focus_year, axis)
        detail_bodies = list(cfg["transit_bodies"]["detail"])
        if inp.bodies and "moon" in inp.bodies:
            detail_bodies.append("moon")
        if len(yaxis) > 1:
            ytargets = _targets(inp, chart, yaxis, ids)
            dres = scan_transits(ytargets, birth_jd=birth_jd, bodies=detail_bodies, preset=inp.orb_preset,
                                 custom_orbs=inp.orbs, include_minor=inp.minors, mode=inp.target_mode, lang=lang)
            dwin = dres["windows"]
            classify_windows(dwin, natal_houses, lang)
            for w in dwin:
                w["text"] = describe_window(w, lang)
            detail = {"year": focus_year, "windows": strip_internal(dwin), "bodies": detail_bodies, "notes": dres["notes"],
                      "lifetime_in_year": [w["id"] for w in windows if w["start"][:4] <= str(focus_year) <= w["end"][:4]]}

    now = active_now(windows + [w for w in detail["windows"]], ref_jd)
    now_out = {"date": ref_day, "active": strip_internal(now["active"]), "upcoming": now["upcoming"][:40]}

    eph = ephemeris_status()
    profile = {
        "input": inp.model_dump(),
        "query": inp.query_params(),
        "chart": chart,
        "axis": {"start": jd_to_iso(axis[0]), "end": jd_to_iso(axis[-1]), "days": int(len(axis)),
                 "years": round((axis[-1] - axis[0]) / TROPICAL_YEAR, 1), "year_start": life_y0, "year_end": life_y1},
        "lifetime": {"windows": strip_internal(windows), "episodes": res["episodes"], "cycles": cycles,
                     "house_transits": house_tr, "notes": res["notes"], "bodies": lifetime_bodies, "targets": ids},
        "detail": detail,
        "domains": {"meta": domain_meta(lang), "scored": scored, "key_years": kyears,
                    "annual_raw": [round(float(x), 4) for x in annual["total"]]},
        "now": now_out,
        "meta": {"computed_ms": int((time.time() - t0) * 1000), "cached": False, "engine": f"swisseph {swe.version}",
                 "full_ephemeris": eph["full_planets"], "config_version": cfg["version"], "mode": inp.target_mode,
                 "calibrated": scored["calibrated"], "lang": lang, "focus_year": focus_year},
    }
    _cache_put(key, profile)
    return profile


def build_progressions(inp: BirthInput, reference_jd: Optional[float] = None) -> Dict[str, Any]:
    ref_jd = reference_jd if reference_jd is not None else now_jd()
    ref_day = jd_to_iso(ref_jd)
    key = f"prog:{inp.cache_key()}:{ref_day}"
    cached = _cache_get(key)
    if cached:
        cached["meta"]["cached"] = True
        return cached
    t0 = time.time()
    cfg = natal_config()
    chart = calculate_natal_chart(inp)
    birth_jd = chart["tjd_ut"]
    axis = lifetime_axis(birth_jd, float(cfg["lifetime_years"]), inp.range_from, inp.range_to)
    at_jd = ref_jd if axis[0] <= ref_jd <= axis[-1] else float(axis[0])
    current = progressed_chart(chart, inp, at_jd)
    moon = moon_timeline(chart, inp, axis)
    ingresses = progressed_ingresses(chart, inp, axis)
    from src.natal.interpretations import describe_progressed_moon_sign, describe_progressed_moon_house, describe_phase
    for p in moon["sign_periods"]:
        p["text"] = describe_progressed_moon_sign(p["sign_index"], inp.lang)
    for h in moon["house_ingresses"]:
        h["text"] = describe_progressed_moon_house(h["to"], inp.lang)
    for ph in moon["phases"]:
        ph["text"] = describe_phase(ph["phase_index"], inp.lang)
    current["lunation_phase"]["text"] = describe_phase(current["lunation_phase"]["index"], inp.lang)
    out = {
        "input": inp.model_dump(), "query": inp.query_params(), "chart": chart,
        "axis": {"start": jd_to_iso(axis[0]), "end": jd_to_iso(axis[-1])},
        "current": current, "moon": moon, "ingresses": ingresses,
        "meta": {"computed_ms": int((time.time() - t0) * 1000), "cached": False, "reference_date": ref_day,
                 "method": cfg["progression"], "lang": inp.lang},
    }
    _cache_put(key, out)
    return out


def chart_only(inp: BirthInput) -> Dict[str, Any]:
    key = f"chart:{inp.cache_key()}"
    cached = _cache_get(key)
    if cached:
        return cached
    chart = calculate_natal_chart(inp)
    _cache_put(key, chart)
    return chart
