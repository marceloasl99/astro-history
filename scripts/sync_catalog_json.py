#!/usr/bin/env python3
"""Sincroniza data/historical_events.json com a tabela `events` (fonte de verdade: SQLite)."""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from src.db import get_connection  # noqa: E402

OUT = os.path.join(ROOT, "data", "historical_events.json")
COLS = ("id, title, category, date, time, city, country, latitude, longitude, consequence, macro_category, subcategory, "
        "polarity, date_precision, quality_tier, calendar, region, source_id, source_url, magnitude, external_ids")


def main():
    conn = get_connection()
    rows = conn.execute(f"SELECT {COLS} FROM events ORDER BY id").fetchall()
    conn.close()
    out = []
    for r in rows:
        d = {k: v for k, v in dict(r).items() if v is not None}
        if "external_ids" in d:
            try:
                d["external_ids"] = json.loads(d["external_ids"])
            except Exception:
                pass
        out.append(d)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"{len(out)} eventos → {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
