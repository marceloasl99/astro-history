"""
Eventos astronômicos exatos (datas com precisão de minutos) via busca de raiz
sobre o Swiss Ephemeris: aspectos exatos (com nº de passagens), ingressos, estações e eclipses.
São os "marcadores" temporais do forecast e os drivers exibidos na interface.
"""

import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import swisseph as swe
from scipy.optimize import brentq

for _p in ["/usr/share/libswe/ephe", "/usr/share/swisseph", "/usr/local/share/swisseph"]:
    if os.path.exists(_p):
        swe.set_ephe_path(_p)
        break

SWE_ID = {
    "sun": swe.SUN, "mercury": swe.MERCURY, "venus": swe.VENUS, "mars": swe.MARS,
    "jupiter": swe.JUPITER, "saturn": swe.SATURN, "uranus": swe.URANUS,
    "neptune": swe.NEPTUNE, "pluto": swe.PLUTO,
}
PT_NAMES = {
    "sun": "Sol", "mercury": "Mercúrio", "venus": "Vênus", "mars": "Marte", "jupiter": "Júpiter",
    "saturn": "Saturno", "uranus": "Urano", "neptune": "Netuno", "pluto": "Plutão",
}
ASPECT_PT = {0: "Conjunção", 60: "Sextil", 90: "Quadratura", 120: "Trígono", 180: "Oposição"}
ASPECT_SYMBOL = {0: "☌", 60: "⚹", 90: "□", 120: "△", 180: "☍"}
SIGNS_PT = ["Áries", "Touro", "Gêmeos", "Câncer", "Leão", "Virgem", "Libra",
            "Escorpião", "Sagitário", "Capricórnio", "Aquário", "Peixes"]


def jd_to_date(jd: float) -> date:
    y, m, d, _ = swe.revjul(jd)
    return date(y, m, d)


def jd_to_iso(jd: float) -> str:
    y, m, d, h = swe.revjul(jd)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    if mm == 60:
        hh, mm = hh + 1, 0
    return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d} UT"


def _lon(body: str, jd: float, helio: bool = False) -> float:
    flag = swe.FLG_SWIEPH | (swe.FLG_HELCTR if helio else 0)
    return swe.calc_ut(jd, SWE_ID[body], flag)[0][0]


def _speed(body: str, jd: float) -> float:
    return swe.calc_ut(jd, SWE_ID[body], swe.FLG_SWIEPH | swe.FLG_SPEED)[0][3]


def _wrap180(x: float) -> float:
    return (x + 180.0) % 360.0 - 180.0


def exact_aspects(body_a: str, body_b: str, angle: float, start: date, end: date, step_days: float = 1.0) -> List[Dict[str, Any]]:
    """
    Instantes em que (lon_a - lon_b) == ±angle entre `start` e `end`.
    Retorna lista com data/hora UT, passagem (1ª, 2ª, 3ª...) e se o aspecto é aplicativo ou separativo.
    """
    jd0 = swe.julday(start.year, start.month, start.day, 0.0)
    jd1 = swe.julday(end.year, end.month, end.day, 24.0)
    targets = [angle] if angle in (0.0, 180.0) else [angle, -angle]
    hits: List[Tuple[float, float]] = []
    for tgt in targets:
        def f(jd: float, tgt=tgt) -> float:
            return _wrap180(_lon(body_a, jd) - _lon(body_b, jd) - tgt)
        grid = np.arange(jd0, jd1 + step_days, step_days)
        vals = np.array([f(j) for j in grid])
        for k in range(len(grid) - 1):
            if vals[k] == 0.0:
                hits.append((grid[k], tgt))
            elif np.sign(vals[k]) != np.sign(vals[k + 1]) and abs(vals[k] - vals[k + 1]) < 90.0:
                try:
                    root = brentq(f, grid[k], grid[k + 1], xtol=1e-5)
                    hits.append((root, tgt))
                except ValueError:
                    continue
    hits.sort()
    # Agrupa as passagens de um mesmo "episódio" (laço retrógrado): intervalos < 420 dias
    episodes: List[List[Tuple[float, float]]] = []
    for h in hits:
        if episodes and h[0] - episodes[-1][-1][0] < 420.0:
            episodes[-1].append(h)
        else:
            episodes.append([h])
    numbered = [(jd, tgt, n, len(ep)) for ep in episodes for n, (jd, tgt) in enumerate(ep, 1)]
    out = []
    for jd, tgt, n, total in numbered:
        # aplicativo se a separação absoluta está diminuindo em direção ao ângulo antes do exato
        before = abs(_wrap180(_lon(body_a, jd - 1.0) - _lon(body_b, jd - 1.0)))
        after = abs(_wrap180(_lon(body_a, jd + 1.0) - _lon(body_b, jd + 1.0)))
        out.append({
            "body_a": body_a, "body_b": body_b, "angle": angle,
            "label": f"{PT_NAMES[body_a]} {ASPECT_SYMBOL[int(angle)]} {PT_NAMES[body_b]}",
            "aspect": ASPECT_PT[int(angle)],
            "jd": round(jd, 5), "date": jd_to_date(jd).isoformat(), "datetime_ut": jd_to_iso(jd),
            "pass_number": n, "total_passes": total,
            "direction": "aplicativo→separativo" if before > after or before == after else "retrógrado",
        })
    return out


def ingresses(body: str, start: date, end: date, step_days: float = 1.0) -> List[Dict[str, Any]]:
    """Mudanças de signo (incluindo regressos por retrogradação)."""
    jd0 = swe.julday(start.year, start.month, start.day, 0.0)
    jd1 = swe.julday(end.year, end.month, end.day, 24.0)
    grid = np.arange(jd0, jd1 + step_days, step_days)
    lons = np.array([_lon(body, j) for j in grid])
    signs = np.floor(lons / 30.0).astype(int) % 12
    out = []
    for k in range(len(grid) - 1):
        if signs[k] != signs[k + 1]:
            boundary = 30.0 * (signs[k + 1] if lons[k + 1] > lons[k] or abs(lons[k + 1] - lons[k]) > 180 else signs[k])
            if abs(lons[k + 1] - lons[k]) > 180:  # cruzou 0° Áries
                boundary = 0.0
            def f(jd: float, b=boundary) -> float:
                return _wrap180(_lon(body, jd) - b)
            try:
                root = brentq(f, grid[k], grid[k + 1], xtol=1e-5)
            except ValueError:
                root = grid[k + 1]
            out.append({
                "body": body, "label": f"{PT_NAMES[body]} ingressa em {SIGNS_PT[signs[k + 1]]}",
                "from_sign": SIGNS_PT[signs[k]], "to_sign": SIGNS_PT[signs[k + 1]],
                "retrograde": bool(_speed(body, root) < 0),
                "jd": round(root, 5), "date": jd_to_date(root).isoformat(), "datetime_ut": jd_to_iso(root),
            })
    return out


def stations(body: str, start: date, end: date, step_days: float = 1.0) -> List[Dict[str, Any]]:
    """Estações (velocidade zero): retrógrada (R) ou direta (D)."""
    jd0 = swe.julday(start.year, start.month, start.day, 0.0)
    jd1 = swe.julday(end.year, end.month, end.day, 24.0)
    grid = np.arange(jd0, jd1 + step_days, step_days)
    sp = np.array([_speed(body, j) for j in grid])
    out = []
    for k in range(len(grid) - 1):
        if np.sign(sp[k]) != np.sign(sp[k + 1]) and sp[k] != 0:
            root = brentq(lambda j: _speed(body, j), grid[k], grid[k + 1], xtol=1e-5)
            kind = "retrógrada" if sp[k] > 0 else "direta"
            out.append({
                "body": body, "label": f"{PT_NAMES[body]} estaciona {kind}", "kind": kind,
                "longitude": round(_lon(body, root), 3),
                "jd": round(root, 5), "date": jd_to_date(root).isoformat(), "datetime_ut": jd_to_iso(root),
            })
    return out


def eclipses(start: date, end: date) -> List[Dict[str, Any]]:
    """Eclipses solares e lunares com tipo e, para solares, ponto de máximo geográfico."""
    jd0 = swe.julday(start.year, start.month, start.day, 0.0)
    jd1 = swe.julday(end.year, end.month, end.day, 24.0)
    out = []
    for solar in (True, False):
        j = jd0
        while True:
            if solar:
                rflag, tret = swe.sol_eclipse_when_glob(j, swe.FLG_SWIEPH, 0)
            else:
                rflag, tret = swe.lun_eclipse_when(j, swe.FLG_SWIEPH, 0)
            t = tret[0]
            if t > jd1 or t <= j:
                break
            if solar:
                kind = "total" if rflag & swe.ECL_TOTAL else "anular" if rflag & swe.ECL_ANNULAR else "parcial"
                try:
                    geo = swe.sol_eclipse_where(t, swe.FLG_SWIEPH)[1]
                    where = {"lon": round(geo[0], 2), "lat": round(geo[1], 2)}
                except Exception:
                    where = None
            else:
                kind = "total" if rflag & swe.ECL_TOTAL else "parcial" if rflag & swe.ECL_PARTIAL else "penumbral"
                where = None
            sun_lon = _lon("sun", t)
            out.append({
                "type": "solar" if solar else "lunar", "kind": kind,
                "label": f"Eclipse {'solar' if solar else 'lunar'} {kind} a {sun_lon % 30:.1f}° de {SIGNS_PT[int(sun_lon // 30) % 12]}",
                "sun_longitude": round(sun_lon, 3), "max_point": where,
                "jd": round(t, 5), "date": jd_to_date(t).isoformat(), "datetime_ut": jd_to_iso(t),
            })
            j = t + 1.0
    out.sort(key=lambda e: e["jd"])
    return out


OUTER_PAIRS = [("jupiter", "saturn"), ("jupiter", "uranus"), ("jupiter", "neptune"), ("jupiter", "pluto"),
               ("saturn", "uranus"), ("saturn", "neptune"), ("saturn", "pluto"),
               ("uranus", "neptune"), ("uranus", "pluto"), ("neptune", "pluto")]


def outer_cycle_calendar(start: date, end: date, angles=(0.0, 90.0, 180.0)) -> List[Dict[str, Any]]:
    """Calendário de aspectos exatos entre planetas lentos (Júpiter a Plutão) no período."""
    out = []
    for a, b in OUTER_PAIRS:
        for ang in angles:
            out.extend(exact_aspects(a, b, ang, start, end, step_days=5.0))
    out.sort(key=lambda e: e["jd"])
    return out
