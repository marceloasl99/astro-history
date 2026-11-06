"""
Infraestrutura comum dos importadores (v6):

- `StagedEvent`: registro normalizado no esquema v3.
- `stage(...)`: grava data/staging/<fonte>.json.
- `merge_into_catalog(...)`: deduplica contra o banco (data ±1 dia + país/título similares, ou external_ids),
  atribui ids novos, calcula a carta (Swiss Ephemeris) e insere; registra exclusões em data/exclusion_log.md.
- `update_manifest(...)`: atualiza data/sources_manifest.yml.

Regras: nada toca `events_v2` (Track B). Eventos com date_precision != 'day' entram no catálogo
mas são marcados; o motor de cartas usa meio-dia local sem casas.
"""

import difflib
import json
import os
import sys
import time
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)

from src.astro_engine import calculate_event_chart  # noqa: E402
from src.core.dates import historical_year, parse_catalog_date  # noqa: E402
from src.db import get_connection, init_db, save_calculated_event  # noqa: E402

STAGING_DIR = os.path.join(ROOT, "data", "staging")
EXCLUSION_LOG = os.path.join(ROOT, "data", "exclusion_log.md")
MANIFEST = os.path.join(ROOT, "data", "sources_manifest.yml")
CATEGORIES = os.path.join(ROOT, "config", "categories.yaml")
DATA_VERSION = "6.0.0"


@dataclass
class StagedEvent:
    title: str
    date: str                      # 'YYYY-MM-DD' ou '-YYYY-MM-DD' (a.C.)
    macro_category: str
    subcategory: str
    polarity: str
    country: str
    city: str
    latitude: float
    longitude: float
    consequence: str
    source_id: str
    source_url: str
    quality_tier: str = "B"
    date_precision: str = "day"
    time: str = "desconhecido"
    region: Optional[str] = None
    magnitude: Optional[float] = None
    is_start: int = 1
    external_ids: Dict[str, Any] = field(default_factory=dict)
    calendar: Optional[str] = None

    def legacy_category(self) -> str:
        return macro_to_legacy().get(self.macro_category, "Política, Tratados & Cultura")


def _cats() -> Dict[str, Any]:
    with open(CATEGORIES, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def macro_to_legacy() -> Dict[str, str]:
    return _cats()["macro_to_legacy"]


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join("".join(c if c.isalnum() else " " for c in s).split())


def stage(source_id: str, events: Iterable[StagedEvent]) -> str:
    os.makedirs(STAGING_DIR, exist_ok=True)
    path = os.path.join(STAGING_DIR, f"{source_id}.json")
    data = [asdict(e) for e in events]
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"  staged {len(data)} eventos em {path}")
    return path


def load_staged(source_id: str) -> List[StagedEvent]:
    with open(os.path.join(STAGING_DIR, f"{source_id}.json"), "r", encoding="utf-8") as f:
        return [StagedEvent(**d) for d in json.load(f)]


def _day_number(date: str) -> int:
    """Número de dia aproximado (ano histórico × 366 + mês × 31 + dia) para janela ±1 dia."""
    y, m, d, bce = parse_catalog_date(date)
    yh = historical_year(date)
    return yh * 366 + m * 31 + d


def _existing_index(conn) -> Tuple[Dict[int, List[Dict[str, Any]]], Dict[str, int]]:
    rows = conn.execute("SELECT id, title, date, country, external_ids FROM events").fetchall()
    by_day: Dict[int, List[Dict[str, Any]]] = {}
    ext: Dict[str, int] = {}
    for r in rows:
        try:
            dn = _day_number(r["date"])
        except Exception:
            continue
        by_day.setdefault(dn, []).append({"id": r["id"], "title": norm(r["title"]), "country": norm(r["country"])})
        if r["external_ids"]:
            try:
                for k, v in json.loads(r["external_ids"]).items():
                    ext[f"{k}:{v}"] = r["id"]
            except Exception:
                pass
    return by_day, ext


def _is_duplicate(ev: StagedEvent, by_day, ext) -> Optional[Tuple[int, str]]:
    for k, v in (ev.external_ids or {}).items():
        if f"{k}:{v}" in ext:
            return ext[f"{k}:{v}"], f"external_id {k}:{v}"
    dn = _day_number(ev.date)
    t, c = norm(ev.title), norm(ev.country)
    window = 1 if ev.date_precision == "day" else (31 if ev.date_precision == "month" else 366)
    for d in range(dn - window, dn + window + 1):
        for x in by_day.get(d, []):
            same_country = (c and x["country"] and (c in x["country"] or x["country"] in c))
            ratio = difflib.SequenceMatcher(None, t, x["title"]).ratio()
            if ratio >= 0.85 or (same_country and ratio >= 0.55):
                return x["id"], f"título similar ({ratio:.2f}) a #{x['id']}"
    return None


def _log_exclusions(source_id: str, excluded: List[Tuple[StagedEvent, str]]) -> None:
    if not excluded:
        return
    with open(EXCLUSION_LOG, "a", encoding="utf-8") as f:
        f.write(f"\n## {source_id} — {time.strftime('%Y-%m-%d')} ({len(excluded)} excluídos)\n\n")
        for ev, why in excluded[:500]:
            f.write(f"- `{ev.date}` **{ev.title}** ({ev.country}) — {why}\n")
        if len(excluded) > 500:
            f.write(f"- … e {len(excluded) - 500} outros\n")


def merge_into_catalog(source_id: str, events: List[StagedEvent], calc_charts: bool = True, dry_run: bool = False) -> Dict[str, int]:
    """Insere eventos novos (não duplicados) no catálogo com ids sequenciais e cartas calculadas."""
    init_db()
    conn = get_connection()
    by_day, ext = _existing_index(conn)
    next_id = (conn.execute("SELECT MAX(id) FROM events").fetchone()[0] or 0) + 1
    inserted, excluded = [], []
    seen_titles: Dict[Tuple[int, str], bool] = {}
    for ev in events:
        if not ev.title or not ev.date or len(ev.consequence or "") < 30:
            excluded.append((ev, "registro incompleto"))
            continue
        try:
            parse_catalog_date(ev.date)
        except Exception:
            excluded.append((ev, "data inválida"))
            continue
        dup = _is_duplicate(ev, by_day, ext)
        if dup:
            excluded.append((ev, f"duplicata: {dup[1]}"))
            continue
        key = (_day_number(ev.date), norm(ev.title)[:40])
        if key in seen_titles:
            excluded.append((ev, "duplicata interna da fonte"))
            continue
        seen_titles[key] = True
        row = {
            "id": next_id, "title": ev.title.strip(), "category": ev.legacy_category(), "date": ev.date, "time": ev.time or "desconhecido",
            "city": ev.city or ev.country, "country": ev.country, "latitude": float(ev.latitude), "longitude": float(ev.longitude),
            "consequence": ev.consequence.strip(),
        }
        inserted.append((row, ev))
        by_day.setdefault(key[0], []).append({"id": next_id, "title": norm(ev.title), "country": norm(ev.country)})
        for k, v in (ev.external_ids or {}).items():
            ext[f"{k}:{v}"] = next_id
        next_id += 1
    conn.close()
    print(f"  {source_id}: {len(inserted)} novos, {len(excluded)} excluídos")
    if dry_run:
        return {"inserted": len(inserted), "excluded": len(excluded)}
    t0 = time.time()
    for i, (row, ev) in enumerate(inserted, 1):
        if calc_charts:
            chart = calculate_event_chart(row)
        else:
            chart = {"planets": [], "aspects": [], "star_contacts": [], "summary": {}, "tjd_ut": None, "is_time_known": False}
        save_calculated_event(row, chart)
        if i % 200 == 0:
            print(f"    {i}/{len(inserted)} ({time.time()-t0:.0f}s)")
    conn = get_connection()
    with conn:
        for row, ev in inserted:
            conn.execute("""UPDATE events SET date_precision=?, calendar=?, source_id=?, source_url=?, quality_tier=?, macro_category=?,
                            subcategory=?, polarity=?, region=?, magnitude=?, is_start=?, external_ids=?, data_version=? WHERE id=?""",
                         (ev.date_precision, ev.calendar or ("julian" if (ev.date.startswith("-") or ev.date < "1582-10-15") else "gregorian"),
                          ev.source_id, ev.source_url, ev.quality_tier, ev.macro_category, ev.subcategory, ev.polarity, ev.region,
                          ev.magnitude, ev.is_start, json.dumps(ev.external_ids, ensure_ascii=False) if ev.external_ids else None,
                          DATA_VERSION, row["id"]))
    conn.close()
    _log_exclusions(source_id, excluded)
    return {"inserted": len(inserted), "excluded": len(excluded)}


def update_manifest(entry: Dict[str, Any]) -> None:
    with open(MANIFEST, "r", encoding="utf-8") as f:
        m = yaml.safe_load(f)
    m["sources"] = [s for s in m["sources"] if s.get("id") != entry["id"]] + [entry]
    m["updated_at"] = time.strftime("%Y-%m-%d")
    m["version"] = DATA_VERSION
    with open(MANIFEST, "w", encoding="utf-8") as f:
        yaml.safe_dump(m, f, allow_unicode=True, sort_keys=False, width=120)


def region_for(country: str) -> Optional[str]:
    from scripts.migrate_catalog_v3 import CONTINENT_BY_COUNTRY, load_regions
    if not CONTINENT_BY_COUNTRY:
        load_regions()
    return CONTINENT_BY_COUNTRY.get(country)
