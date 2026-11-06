#!/usr/bin/env python3
"""
Datasets curados do AstroHistory v6 (data/curated/*.json) — marcos documentados em fontes públicas
(cronologias acadêmicas, documentos oficiais, OMS/ONU/NASA, historiografia nacional). Tier C por padrão
(enciclopédico auditado); `q: "A"` quando a data vem de documento primário citado.

Formato compacto por registro:
  t título · d data ('YYYY-MM-DD' ou '-YYYY-MM-DD') · m macro · s subcategoria · p polaridade · co país · ci cidade
  la/lo coordenadas · c consequência · pr precisão (day|month|year|decade, padrão day) · tm hora local (opcional)
  q tier (padrão C) · u URL da fonte (opcional)

Uso: python scripts/importers/import_curated.py [--merge] [--only arquivo]
"""
import glob
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.importers.common import StagedEvent, merge_into_catalog, stage, update_manifest  # noqa: E402

CURATED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "curated")
SOURCE_ID = "astrohistory_curated_v6"


def load_all(only: str = None) -> list:
    out = []
    for path in sorted(glob.glob(os.path.join(CURATED_DIR, "*.json"))):
        if only and only not in os.path.basename(path):
            continue
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        for r in data:
            out.append(StagedEvent(
                title=r["t"], date=r["d"], macro_category=r["m"], subcategory=r["s"], polarity=r.get("p", "neutral"),
                country=r["co"], city=r.get("ci", r["co"]), latitude=float(r["la"]), longitude=float(r["lo"]),
                consequence=r["c"], source_id=SOURCE_ID, source_url=r.get("u", "https://github.com/marceloasl99/astro-history/tree/main/data/curated"),
                quality_tier=r.get("q", "C"), date_precision=r.get("pr", "day"), time=r.get("tm", "desconhecido"),
                external_ids={"curated": f"{os.path.basename(path)[:-5]}:{r['d']}:{r['t'][:30]}"},
            ))
    return out


def main():
    only = sys.argv[sys.argv.index("--only") + 1] if "--only" in sys.argv else None
    events = load_all(only)
    print(f"curados: {len(events)} eventos em {len(glob.glob(os.path.join(CURATED_DIR, '*.json')))} arquivos")
    stage(SOURCE_ID, events)
    if "--merge" in sys.argv:
        res = merge_into_catalog(SOURCE_ID, events)
        update_manifest({
            "id": SOURCE_ID, "name": "AstroHistory — marcos curados v6 (Antiguidade/Medievo, ciência, saúde, diplomacia, sociedade, economia, Brasil/América Latina)",
            "institution": "AstroHistory Research Team (consolidação de cronologias acadêmicas e documentos oficiais)",
            "url": "https://github.com/marceloasl99/astro-history/tree/main/data/curated", "license": "AGPL-3.0",
            "file_path": "data/curated/", "time_span": "1750 BCE / 2024 CE", "records_count": res["inserted"],
            "category": "múltiplas", "date_precision": "day|month|year|decade (declarada por registro)",
            "features": ["title_pt", "consequence_pt", "coordinates", "tier"], "quality_tier": "C (A quando documento primário)",
        })


if __name__ == "__main__":
    main()
