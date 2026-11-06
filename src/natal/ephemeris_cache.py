"""
Grade diária de efemérides para os trânsitos de vida (1850–2150, 0h UT) com cache em memória
e fallback de cálculo direto (Swiss Ephemeris) fora do intervalo da grade.
"""

import logging
import os
import time
from datetime import date, timedelta
from typing import Dict, List, Optional, Tuple

import numpy as np
import swisseph as swe

from src.core.ephemeris import ensure_ephe_path
from src.natal.bodies import SWE_IDS, TRANSIT_GRID_BODIES
from src.natal.config import grid_path, natal_config

logger = logging.getLogger(__name__)

CALC_FLAGS = swe.FLG_SWIEPH | swe.FLG_SPEED


def jd_at_0h(y: int, m: int, d: int) -> float:
    return swe.julday(y, m, d, 0.0, swe.GREG_CAL)


def jd_to_date(jd: float) -> Tuple[int, int, int, float]:
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    return int(y), int(m), int(d), float(h)


def jd_to_iso(jd: float) -> str:
    y, m, d, _ = jd_to_date(jd + 1e-9)
    return f"{y:04d}-{m:02d}-{d:02d}"


def jd_to_iso_time(jd: float) -> str:
    y, m, d, h = jd_to_date(jd + 1e-9)
    hh = int(h)
    mm = int(round((h - hh) * 60))
    if mm == 60:
        hh, mm = hh + 1, 0
    return f"{y:04d}-{m:02d}-{d:02d} {hh:02d}:{mm:02d} UT"


def floor_day(jd: float) -> float:
    """JD do 0h UT do dia civil que contém `jd`."""
    return np.floor(jd - 0.5) + 0.5


def build_grid(start_year: int = 1850, end_year: int = 2150, out: Optional[str] = None,
               bodies: Optional[List[str]] = None, verbose: bool = True) -> str:
    """Constrói a grade (usada por scripts/build_natal_grid.py e pelo carregamento automático)."""
    ensure_ephe_path()
    out = out or grid_path()
    bodies = bodies or TRANSIT_GRID_BODIES
    d0, d1 = date(start_year, 1, 1), date(end_year, 12, 31)
    n = (d1 - d0).days + 1
    jd = np.empty(n, dtype=np.float64)
    lon = np.empty((n, len(bodies)), dtype=np.float32)
    spd = np.empty((n, len(bodies)), dtype=np.float32)
    t0 = time.time()
    cur = d0
    for i in range(n):
        j = jd_at_0h(cur.year, cur.month, cur.day)
        jd[i] = j
        for b, bid in enumerate(bodies):
            res, _ = swe.calc_ut(j, SWE_IDS[bid], CALC_FLAGS)
            lon[i, b] = res[0]
            spd[i, b] = res[3]
        cur += timedelta(days=1)
        if verbose and i and i % 20000 == 0:
            logger.info("grade natal: %d/%d dias (%.0fs)", i, n, time.time() - t0)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, jd=jd, lon=lon, speed=spd, bodies=np.array(bodies),
                        start_year=np.int32(start_year), end_year=np.int32(end_year))
    if verbose:
        logger.info("grade natal salva em %s (%d dias × %d corpos, %.1fs)", out, n, len(bodies), time.time() - t0)
    return out


class NatalGrid:
    def __init__(self, path: str):
        data = np.load(path, allow_pickle=False)
        self.jd: np.ndarray = data["jd"].astype(np.float64)
        self.lon: np.ndarray = data["lon"]
        self.speed: np.ndarray = data["speed"]
        self.bodies: List[str] = [str(b) for b in data["bodies"]]
        self.index: Dict[str, int] = {b: i for i, b in enumerate(self.bodies)}
        self.jd0: float = float(self.jd[0])
        self.jd1: float = float(self.jd[-1])
        self.n: int = len(self.jd)

    def day_index(self, jd: float) -> int:
        return int(round(jd - self.jd0))

    def contains(self, jd: float) -> bool:
        return self.jd0 <= jd <= self.jd1


_GRID: Optional[NatalGrid] = None


def get_grid() -> NatalGrid:
    global _GRID
    if _GRID is None:
        path = grid_path()
        if not os.path.exists(path):
            logger.warning("grade natal ausente em %s — construindo (pode levar ~1 min)", path)
            build_grid(out=path)
        _GRID = NatalGrid(path)
    return _GRID


def _calc_days(body: str, jd_days: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Fallback lento: calcula lon/velocidade diretamente para um eixo de dias."""
    ensure_ephe_path()
    sid = SWE_IDS[body]
    lon = np.empty(len(jd_days), dtype=np.float64)
    spd = np.empty(len(jd_days), dtype=np.float64)
    for i, j in enumerate(jd_days):
        res, _ = swe.calc_ut(float(j), sid, CALC_FLAGS)
        lon[i], spd[i] = res[0], res[3]
    return lon, spd


def day_axis(jd_start: float, jd_end: float) -> np.ndarray:
    a = floor_day(jd_start)
    b = floor_day(jd_end)
    n = int(round(b - a)) + 1
    return a + np.arange(n, dtype=np.float64)


def series(body: str, jd_days: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
    """Longitudes e velocidades do corpo nos dias (0h UT) de `jd_days`, via grade quando possível."""
    grid = get_grid()
    lon = np.empty(len(jd_days), dtype=np.float64)
    spd = np.empty(len(jd_days), dtype=np.float64)
    inside = (jd_days >= grid.jd0) & (jd_days <= grid.jd1)
    if body in grid.index and inside.any():
        idx = np.round(jd_days[inside] - grid.jd0).astype(int)
        col = grid.index[body]
        lon[inside] = grid.lon[idx, col]
        spd[inside] = grid.speed[idx, col]
    outside = ~inside if body in grid.index else np.ones(len(jd_days), dtype=bool)
    if outside.any():
        lo, sp = _calc_days(body, jd_days[outside])
        lon[outside], spd[outside] = lo, sp
    return lon, spd


def hourly_series(body: str, jd_start: float, jd_end: float, step_hours: float = 1.0) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Eixo horário (para a Lua em trânsito, restrita a intervalos curtos)."""
    n = int(np.ceil((jd_end - jd_start) * 24.0 / step_hours)) + 1
    jds = jd_start + np.arange(n) * (step_hours / 24.0)
    lon, spd = _calc_days(body, jds)
    return jds, lon, spd


def body_longitude(body: str, jd: float) -> float:
    ensure_ephe_path()
    res, _ = swe.calc_ut(float(jd), SWE_IDS[body], CALC_FLAGS)
    return float(res[0])


def grid_info() -> Dict[str, object]:
    g = get_grid()
    cfg = natal_config()["grid"]
    return {"start_year": int(cfg["start_year"]), "end_year": int(cfg["end_year"]), "days": g.n, "bodies": g.bodies}
