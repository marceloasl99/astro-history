#!/usr/bin/env python3
"""
Calibração 0–1000 dos domínios de vida por população sintética de nascimentos.

Gera data/calibration/natal_domains_reference.json com os quantis (0..1000) de:
  month_<domínio>, month_total, year_<domínio>, year_total
Uso: python scripts/calibrate_natal_domains.py [N] [seed]
"""
import json
import os
import sqlite3
import sys
import time

import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from src.natal.chart import calculate_natal_chart  # noqa: E402
from src.natal.config import natal_config, domains_config  # noqa: E402
from src.natal.domains import annual_totals, classify_windows, domain_keys, monthly_domain_series  # noqa: E402
from src.natal.gazetteer import DB_FILE  # noqa: E402
from src.natal.models import BirthInput  # noqa: E402
from src.natal.transits import Targets, lifetime_axis, scan_transits  # noqa: E402

OUT = os.path.join(ROOT, "data", "calibration", "natal_domains_reference.json")


def sample_places(rng, n):
    conn = sqlite3.connect(DB_FILE)
    rows = conn.execute("SELECT lat, lon, tz FROM cities WHERE population > 200000 ORDER BY population DESC LIMIT 1500").fetchall()
    conn.close()
    idx = rng.integers(0, len(rows), size=n)
    return [rows[i] for i in idx]


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else int(domains_config()["calibration"]["synthetic_births"])
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else int(domains_config()["calibration"]["seed"])
    rng = np.random.default_rng(seed)
    cfg = natal_config()
    keys = domain_keys()
    places = sample_places(rng, n)
    month_vals = {k: [] for k in keys}
    month_tot = []
    year_vals = {k: [] for k in keys}
    year_tot = []
    t0 = time.time()
    for i in range(n):
        y = int(rng.integers(1940, 2011))
        m = int(rng.integers(1, 13))
        d = int(rng.integers(1, 29))
        hh, mm = int(rng.integers(0, 24)), int(rng.integers(0, 60))
        lat, lon, tz = places[i]
        inp = BirthInput(date=f"{y:04d}-{m:02d}-{d:02d}", time=f"{hh:02d}:{mm:02d}", lat=float(lat), lon=float(lon), tz=tz)
        chart = calculate_natal_chart(inp)
        axis = lifetime_axis(chart["tjd_ut"], float(cfg["lifetime_years"]))
        ids = [t for t in cfg["targets"]["natal_default"] if t in chart["points"]]
        tg = Targets(axis, {k: chart["points"][k] for k in ids})
        res = scan_transits(tg, birth_jd=chart["tjd_ut"], bodies=cfg["transit_bodies"]["lifetime"], precise=False)
        W = res["windows"]
        classify_windows(W, {b["id"]: b.get("house") for b in chart["bodies"]})
        mo = monthly_domain_series(W, axis)
        an = annual_totals(mo)
        for k in keys:
            month_vals[k].append(mo["by_domain"][k])
            year_vals[k].append(an["by_domain"][k])
        month_tot.append(mo["total"])
        year_tot.append(an["total"])
        if (i + 1) % 25 == 0:
            print(f"  {i+1}/{n} ({time.time()-t0:.0f}s)")
    q = np.linspace(0, 1, 1001)
    ref = {"n": n, "seed": seed, "generated_at": time.strftime("%Y-%m-%d"), "quantiles": {}, "fallback_scale": {}}
    for k in keys:
        ref["quantiles"][f"month_{k}"] = np.quantile(np.concatenate(month_vals[k]), q).round(6).tolist()
        ref["quantiles"][f"year_{k}"] = np.quantile(np.concatenate(year_vals[k]), q).round(6).tolist()
        ref["fallback_scale"][f"month_{k}"] = float(np.mean(np.concatenate(month_vals[k])) or 0.1)
    ref["quantiles"]["month_total"] = np.quantile(np.concatenate(month_tot), q).round(6).tolist()
    ref["quantiles"]["year_total"] = np.quantile(np.concatenate(year_tot), q).round(6).tolist()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(ref, f, separators=(",", ":"))
    print(f"referência salva em {OUT} ({os.path.getsize(OUT)/1e3:.0f} KB, {n} nascimentos, {time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
