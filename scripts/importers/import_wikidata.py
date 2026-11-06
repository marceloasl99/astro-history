#!/usr/bin/env python3
"""
Wikidata (CC0) via SPARQL: batalhas, tratados de paz, declarações de independência, revoluções e
golpes com data (P585/P580) de precisão ≥ dia e coordenadas. Notabilidade: nº de sitelinks ≥ limiar.
Rótulos em pt (fallback en). Tier C (enciclopédico auditado); precisão declarada pelo qualificador do Wikidata.

Uso: python scripts/importers/import_wikidata.py [--merge] [--min-links 25]
"""
import json
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.importers.common import StagedEvent, merge_into_catalog, stage, update_manifest  # noqa: E402

ENDPOINT = "https://query.wikidata.org/sparql"
UA = "AstroHistoryResearchBot/6.0 (https://github.com/marceloasl99/astro-history; research, AGPL)"
SOURCE_ID = "wikidata_events"
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "external", "wikidata")

# (chave, classe Wikidata, propriedade de data, macro, sub, polaridade, descrição PT)
QUERIES = [
    ("battle", "Q178561", "P585", "politics_geopolitics", "battle", "disruptive", "Batalha"),
    ("siege", "Q188055", "P580", "politics_geopolitics", "battle", "disruptive", "Cerco"),
    ("peace_treaty", "Q625298", "P585", "diplomacy_peace", "peace_treaty", "constructive", "Tratado de paz"),
    ("treaty", "Q131569", "P585", "diplomacy_peace", "treaty", "constructive", "Tratado"),
    ("independence", "Q1464916", "P585", "politics_geopolitics", "independence", "constructive", "Declaração de independência"),
    ("revolution", "Q10931", "P580", "politics_geopolitics", "revolution", "disruptive", "Revolução"),
    ("coup", "Q45382", "P585", "politics_geopolitics", "coup", "disruptive", "Golpe de Estado"),
    ("massacre", "Q3199915", "P585", "politics_geopolitics", "massacre", "disruptive", "Massacre"),
    ("earthquake", "Q7944", "P585", "natural_disasters", "earthquake", "disruptive", "Terremoto"),
    ("pandemic", "Q12184", "P580", "health_epidemics", "pandemic", "disruptive", "Pandemia"),
    ("epidemic", "Q3241045", "P580", "health_epidemics", "epidemic", "disruptive", "Epidemia"),
    ("financial_crisis", "Q290178", "P580", "economics_finance", "financial_crisis", "disruptive", "Crise financeira"),
    ("stock_crash", "Q1324393", "P585", "economics_finance", "stock_crash", "disruptive", "Crash de bolsa"),
    ("space_mission", "Q2133344", "P619", "science_technology", "space_exploration", "constructive", "Missão espacial (lançamento)"),
    ("discovery", "Q12772819", "P585", "science_technology", "discovery", "constructive", "Descoberta científica"),
    ("assassination", "Q3882219", "P585", "politics_geopolitics", "political_assassination", "disruptive", "Assassinato"),
    ("uprising", "Q124734", "P580", "politics_geopolitics", "uprising", "disruptive", "Levante"),
    ("famine", "Q168247", "P580", "natural_disasters", "drought_famine", "disruptive", "Fome"),
    ("flood", "Q8068", "P585", "natural_disasters", "flood", "disruptive", "Inundação"),
    ("eruption", "Q7692360", "P585", "natural_disasters", "volcanic_eruption", "disruptive", "Erupção vulcânica"),
]

SPARQL = """
SELECT ?item ?itemLabel ?itemDescription ?date ?prec ?coord ?links ?countryLabel WHERE {{
  ?item wdt:P31/wdt:P279* wd:{cls} .
  ?item p:{prop} ?st . ?st psv:{prop} ?v . ?v wikibase:timeValue ?date ; wikibase:timePrecision ?prec .
  FILTER(?prec >= 9)
  ?item wikibase:sitelinks ?links . FILTER(?links >= {min_links})
  OPTIONAL {{ ?item wdt:P625 ?coord . }}
  OPTIONAL {{ ?item wdt:P17 ?country . }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "pt,pt-br,en" . }}
}}
LIMIT 4000
"""


def run_query(q: str) -> list:
    data = urllib.parse.urlencode({"query": q, "format": "json"}).encode()
    req = urllib.request.Request(ENDPOINT, data=data, headers={"User-Agent": UA, "Accept": "application/sparql-results+json"})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                return json.load(r)["results"]["bindings"]
        except Exception as e:
            print(f"    tentativa {attempt+1} falhou: {e}")
            time.sleep(5 * (attempt + 1))
    return []


def fetch_all(min_links: int) -> dict:
    os.makedirs(RAW_DIR, exist_ok=True)
    out = {}
    for key, cls, prop, *_ in QUERIES:
        raw = os.path.join(RAW_DIR, f"{key}_{min_links}.json")
        if os.path.exists(raw):
            with open(raw, encoding="utf-8") as f:
                out[key] = json.load(f)
            continue
        rows = run_query(SPARQL.format(cls=cls, prop=prop, min_links=min_links))
        print(f"  {key}: {len(rows)} linhas")
        with open(raw, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False)
        out[key] = rows
        time.sleep(1.5)
    return out


def parse_wd_date(v: str, prec: int):
    """'1942-08-19T00:00:00Z' ou '-0333-05-01T00:00:00Z' → (iso catálogo, precisão).
    Verificado empiricamente (Grânico 334 a.C. → '-0333', Zama 202 a.C. → '-0201'): o Wikidata grava anos a.C. em
    numeração ASTRONÔMICA (ano 0 = 1 a.C.); o catálogo usa ano histórico, logo a.C. histórico = |ano| + 1."""
    m = re.match(r"^(-?)(\d{1,6})-(\d{2})-(\d{2})T", v)
    if not m:
        return None, None
    neg, y, mo, d = m.group(1) == "-", int(m.group(2)), int(m.group(3)), int(m.group(4))
    if y > 3000:
        return None, None
    precision = "day" if prec >= 11 else ("month" if prec == 10 else "year")
    mo = mo if prec >= 10 and 1 <= mo <= 12 else 7
    d = d if prec >= 11 and 1 <= d <= 31 else 1
    if neg:
        return f"-{y + 1:04d}-{mo:02d}-{d:02d}", precision
    return f"{y:04d}-{mo:02d}-{d:02d}", precision


def to_events(data: dict) -> list:
    out = []
    seen = set()
    for key, cls, prop, macro, sub, pol, label_pt in QUERIES:
        for r in data.get(key, []):
            qid = r["item"]["value"].rsplit("/", 1)[-1]
            if qid in seen:
                continue
            title = r.get("itemLabel", {}).get("value", "")
            if not title or title == qid:
                continue
            date, precision = parse_wd_date(r["date"]["value"], int(r["prec"]["value"]))
            if not date:
                continue
            if "coord" not in r:
                continue
            m = re.match(r"Point\(([-\d.eE]+) ([-\d.eE]+)\)", r["coord"]["value"])
            if not m:
                continue
            lon, lat = float(m.group(1)), float(m.group(2))
            country = r.get("countryLabel", {}).get("value", "") or "—"
            desc = r.get("itemDescription", {}).get("value", "")
            links = int(r["links"]["value"])
            cons = (f"{label_pt}: {title}. {desc[0].upper() + desc[1:] + '.' if desc else ''} Registro do Wikidata ({qid}) com "
                    f"{links} artigos na Wikipédia, data com precisão '{precision}' e coordenadas; incluído no catálogo exploratório "
                    f"(Track A) para busca de análogos — não integra a amostra estatística pré-registrada.")
            seen.add(qid)
            out.append(StagedEvent(
                title=title[:160], date=date, macro_category=macro, subcategory=sub, polarity=pol, country=country[:80],
                city=title[:80], latitude=lat, longitude=lon, consequence=cons, source_id=SOURCE_ID,
                source_url=f"https://www.wikidata.org/wiki/{qid}", quality_tier="C", date_precision=precision,
                external_ids={"wikidata": qid}, magnitude=float(links),
            ))
    return out


def main():
    min_links = int(sys.argv[sys.argv.index("--min-links") + 1]) if "--min-links" in sys.argv else 25
    data = fetch_all(min_links)
    events = to_events(data)
    print(f"Wikidata: {sum(len(v) for v in data.values())} linhas → {len(events)} eventos únicos")
    stage(SOURCE_ID, events)
    if "--merge" in sys.argv:
        res = merge_into_catalog(SOURCE_ID, events)
        update_manifest({
            "id": SOURCE_ID, "name": f"Wikidata — eventos históricos datados com coordenadas (≥ {min_links} sitelinks)",
            "institution": "Wikimedia Foundation / comunidade Wikidata", "url": "https://query.wikidata.org/",
            "license": "CC0 1.0 (domínio público)", "file_path": "data/external/wikidata/", "time_span": "1000 BCE / 2025 CE",
            "records_count": res["inserted"], "category": "múltiplas", "date_precision": "day|month|year (qualificador P585/P580)",
            "features": ["sitelinks", "coordinates", "country", "date_precision"], "quality_tier": "C",
        })


if __name__ == "__main__":
    main()
