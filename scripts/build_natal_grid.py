#!/usr/bin/env python3
"""
Constrói a grade diária de efemérides para o módulo pessoal (trânsitos de vida):
longitudes e velocidades dos corpos em trânsito, 0h UT, de 1850-01-01 a 2150-12-31.

Saída: data/ephemeris/natal_grid_1850_2150.npz (float32, ~12 MB).
Uso:   python scripts/build_natal_grid.py [start_year end_year]
"""
import os
import sys
import time
from datetime import date, timedelta

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import swisseph as swe  # noqa: E402
from src.core.ephemeris import ensure_ephe_path  # noqa: E402
from src.natal.bodies import TRANSIT_GRID_BODIES, SWE_IDS  # noqa: E402

OUT = os.path.join(ROOT, "data", "ephemeris", "natal_grid_1850_2150.npz")


def build(start_year: int = 1850, end_year: int = 2150, out: str = OUT):
    ensure_ephe_path()
    d0, d1 = date(start_year, 1, 1), date(end_year, 12, 31)
    n = (d1 - d0).days + 1
    bodies = TRANSIT_GRID_BODIES
    jd = np.empty(n, dtype=np.float64)
    lon = np.empty((n, len(bodies)), dtype=np.float32)
    spd = np.empty((n, len(bodies)), dtype=np.float32)
    flags = swe.FLG_SWIEPH | swe.FLG_SPEED
    t0 = time.time()
    cur = d0
    for i in range(n):
        j = swe.julday(cur.year, cur.month, cur.day, 0.0, swe.GREG_CAL)
        jd[i] = j
        for b, bid in enumerate(bodies):
            res, _ = swe.calc_ut(j, SWE_IDS[bid], flags)
            lon[i, b] = res[0]
            spd[i, b] = res[3]
        cur += timedelta(days=1)
        if i % 20000 == 0 and i:
            print(f"  {i}/{n} dias ({time.time()-t0:.0f}s)")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    np.savez_compressed(out, jd=jd, lon=lon, speed=spd, bodies=np.array(bodies),
                        start_year=np.int32(start_year), end_year=np.int32(end_year))
    print(f"grade salva em {out}: {n} dias × {len(bodies)} corpos em {time.time()-t0:.1f}s "
          f"({os.path.getsize(out)/1e6:.1f} MB)")


if __name__ == "__main__":
    a = [int(x) for x in sys.argv[1:3]]
    build(*a) if a else build()
