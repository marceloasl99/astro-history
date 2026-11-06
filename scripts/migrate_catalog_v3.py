#!/usr/bin/env python3
"""
Migração do catálogo para o esquema v3 (AstroHistory v6).

1. Corrige eventos a.C. gravados como d.C. (ex.: Maratona "0490-09-12" → "-0490-09-12").
2. Remove duplicatas conhecidas (mantém o id menor): 301→1, 303→4, 305→6.
3. Preenche macro_category / subcategory / polarity / date_precision / quality_tier / region / data_version.
4. Recalcula TODAS as cartas (Placidus corrigido, fusos históricos por zona, convenção a.C. astronômica).
5. Sincroniza data/historical_events.json com o banco.

Uso: python scripts/migrate_catalog_v3.py [--no-recalc]
"""
import json
import os
import sys
import time

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

from src.astro_engine import calculate_event_chart  # noqa: E402
from src.db import get_connection, init_db, save_calculated_event  # noqa: E402

DATA_VERSION = "6.0.0"
JSON_FILE = os.path.join(ROOT, "data", "historical_events.json")

# id → data correta (a.C.). Fontes: cronologia clássica padrão (calendário juliano proléptico).
BCE_FIXES = {
    1: "-0490-09-12",    # Batalha de Maratona (490 a.C.)
    2: "-0323-06-10",    # Morte de Alexandre (323 a.C.)
    3: "-0146-04-15",    # Destruição de Cartago (146 a.C.)
    4: "-0044-03-15",    # Idos de Março (44 a.C.)
    201: "-0480-08-11",  # Termópilas (480 a.C.)
    202: "-0331-10-01",  # Gaugamela (331 a.C.)
    203: "-0216-08-02",  # Canas (216 a.C.)
}
DUPLICATES = {301: 1, 303: 4, 305: 6}

SUBCATEGORY_RULES = [
    # (palavras-chave no título, subcategoria, polaridade)
    (["golpe", "coup"], "coup", "disruptive"),
    (["revolução", "revolta", "levante", "insurreição", "rebelião", "motim"], "revolution", "disruptive"),
    (["guerra civil"], "civil_war", "disruptive"),
    (["guerra", "invasão", "batalha", "ofensiva", "ataque", "cerco", "bombardeio"], "interstate_war", "disruptive"),
    (["independência", "proclamação"], "independence", "constructive"),
    (["assassinato", "atentado"], "political_assassination", "disruptive"),
    (["queda", "colapso", "fim do", "dissolução", "abdicação"], "regime_collapse", "structural"),
    (["terremoto", "sismo"], "earthquake", "disruptive"),
    (["erupção", "vulcão"], "volcanic_eruption", "disruptive"),
    (["tsunami"], "tsunami", "disruptive"),
    (["furacão", "ciclone", "tufão"], "hurricane", "disruptive"),
    (["pandemia", "epidemia", "peste", "gripe", "cólera", "covid", "ebola", "varíola", "aids"], "pandemic", "disruptive"),
    (["vacina", "penicilina", "erradicação", "cura"], "medicine", "constructive"),
    (["crash", "quebra", "pânico", "crise bancária", "bolsa"], "stock_crash", "disruptive"),
    (["recessão", "depressão"], "recession_start", "disruptive"),
    (["hiperinflação", "inflação"], "hyperinflation", "disruptive"),
    (["moratória", "default", "calote", "dívida"], "sovereign_default", "disruptive"),
    (["plano real", "reforma monetária", "moeda"], "monetary_reform", "structural"),
    (["lançamento", "sputnik", "apollo", "lua", "órbita", "satélite", "espaço", "marte", "voyager", "estação espacial"], "space_exploration", "constructive"),
    (["computador", "internet", "web", "transistor", "chip", "inteligência artificial", "ia ", "software"], "computing_ai", "constructive"),
    (["descoberta", "teoria", "publicação", "relatividade", "dna", "genoma", "prêmio nobel", "física", "química"], "discovery", "constructive"),
    (["invenção", "primeiro voo", "telefone", "rádio", "televisão", "imprensa", "motor", "locomotiva"], "invention", "constructive"),
    (["tratado", "acordo", "armistício", "paz", "pacto"], "peace_treaty", "constructive"),
    (["onu", "liga das nações", "união europeia", "otan", "organização"], "international_organization", "constructive"),
    (["abolição", "lei áurea", "escravidão"], "abolition", "constructive"),
    (["sufrágio", "voto feminino", "direito ao voto"], "suffrage", "constructive"),
    (["direitos civis", "apartheid", "marcha", "declaração universal"], "civil_rights", "constructive"),
    (["constituição", "carta magna", "reforma"], "constitution", "structural"),
    (["eleição", "posse", "eleito"], "landmark_election", "structural"),
]

LEGACY_MACRO = {
    "Guerra & Conflito": "politics_geopolitics",
    "Revolução & Conflito Interno": "politics_geopolitics",
    "Crise Financeira & Econômica": "economics_finance",
    "Desastre & Saúde Pública": "natural_disasters",
    "Ciência & Tecnologia": "science_technology",
    "Política, Tratados & Cultura": "diplomacy_peace",
}
HEALTH_SUBS = {"pandemic", "medicine"}
SOCIETY_SUBS = {"abolition", "suffrage", "civil_rights", "constitution", "landmark_election"}
DEFAULT_SUB = {
    "politics_geopolitics": ("political_event", "disruptive"),
    "economics_finance": ("economic_crisis", "disruptive"),
    "natural_disasters": ("natural_disaster", "disruptive"),
    "health_epidemics": ("epidemic", "disruptive"),
    "science_technology": ("discovery", "constructive"),
    "diplomacy_peace": ("diplomacy", "constructive"),
    "society_culture": ("cultural_milestone", "constructive"),
}

CONTINENT_BY_COUNTRY = {}


def load_regions():
    try:
        with open(os.path.join(ROOT, "data", "countries_database.json"), encoding="utf-8") as f:
            for c in json.load(f):
                CONTINENT_BY_COUNTRY[c["name_pt"]] = c["continent"]
    except Exception:
        pass
    extra = {"Estados Unidos": "América do Norte", "Argentina": "América do Sul", "Bolívia": "América do Sul", "Peru": "América do Sul",
             "Sudão": "África", "Iraque": "Ásia", "México": "América do Norte", "Chile": "América do Sul", "Grécia": "Europa",
             "Itália": "Europa", "Reino Unido": "Europa", "França": "Europa", "Alemanha": "Europa", "Rússia": "Europa",
             "China": "Ásia", "Índia": "Ásia", "Japão": "Ásia", "Brasil": "América do Sul", "Israel": "Ásia", "Irã": "Ásia",
             "Turquia": "Ásia", "Egito": "África", "Tunísia": "África", "Babilônia": "Ásia", "Império Romano": "Europa"}
    for k, v in extra.items():
        CONTINENT_BY_COUNTRY.setdefault(k, v)


def classify(title: str, legacy: str):
    t = (title or "").lower()
    macro = LEGACY_MACRO.get(legacy, "politics_geopolitics")
    sub, pol = None, None
    for keys, s, p in SUBCATEGORY_RULES:
        if any(k in t for k in keys):
            sub, pol = s, p
            break
    if sub in HEALTH_SUBS:
        macro = "health_epidemics"
    elif sub in SOCIETY_SUBS:
        macro = "society_culture"
    elif sub in ("peace_treaty", "international_organization"):
        macro = "diplomacy_peace"
    elif sub in ("earthquake", "volcanic_eruption", "tsunami", "hurricane"):
        macro = "natural_disasters"
    elif sub in ("space_exploration", "computing_ai", "discovery", "invention"):
        macro = "science_technology"
    elif sub in ("stock_crash", "recession_start", "hyperinflation", "sovereign_default", "monetary_reform"):
        macro = "economics_finance"
    elif sub in ("coup", "revolution", "civil_war", "interstate_war", "independence", "political_assassination", "regime_collapse"):
        macro = "politics_geopolitics"
    if sub is None:
        sub, pol = DEFAULT_SUB[macro]
    return macro, sub, pol


def main():
    recalc = "--no-recalc" not in sys.argv
    init_db()
    load_regions()
    conn = get_connection()
    cur = conn.cursor()
    # 1. datas a.C.
    for eid, date in BCE_FIXES.items():
        cur.execute("UPDATE events SET date = ?, calendar = 'julian' WHERE id = ? AND date NOT LIKE '-%'", (date, eid))
        print(f"  a.C. corrigido: #{eid} → {date}" if cur.rowcount else f"  #{eid} já corrigido")
    # 2. duplicatas
    for dup, keep in DUPLICATES.items():
        for tbl in ("planet_positions", "event_aspects", "event_star_aspects"):
            cur.execute(f"DELETE FROM {tbl} WHERE event_id = ?", (dup,))
        cur.execute("DELETE FROM events WHERE id = ?", (dup,))
        if cur.rowcount:
            print(f"  duplicata removida: #{dup} (mantido #{keep})")
    # 3. taxonomia e proveniência
    rows = cur.execute("SELECT id, title, category, country, date, time FROM events").fetchall()
    for r in rows:
        macro, sub, pol = classify(r["title"], r["category"])
        tier = "C" if r["id"] <= 300 else "B"   # ≤300: curadoria original (enciclopédica auditada); >300: datasets COW/UCDP/P&T/USGS/NBER
        cal = "julian" if (r["date"].startswith("-") or r["date"] < "1582-10-15") else "gregorian"
        cur.execute("""UPDATE events SET macro_category=?, subcategory=?, polarity=?, quality_tier=COALESCE(quality_tier, ?),
                       date_precision=COALESCE(date_precision,'day'), calendar=?, region=COALESCE(region, ?), data_version=?,
                       is_start=COALESCE(is_start,1) WHERE id=?""",
                    (macro, sub, pol, tier, cal, CONTINENT_BY_COUNTRY.get(r["country"]), DATA_VERSION, r["id"]))
    conn.commit()
    print(f"  taxonomia aplicada a {len(rows)} eventos")
    # 4. recálculo
    if recalc:
        evs = [dict(r) for r in cur.execute("SELECT * FROM events ORDER BY id").fetchall()]
        conn.close()
        t0 = time.time()
        for i, ev in enumerate(evs, 1):
            chart = calculate_event_chart(ev)
            save_calculated_event(ev, chart)
            if i % 200 == 0:
                print(f"  recalculados {i}/{len(evs)} ({time.time()-t0:.0f}s)")
        print(f"  {len(evs)} cartas recalculadas em {time.time()-t0:.0f}s")
        conn = get_connection()
    # 5. JSON
    rows = conn.execute("SELECT id, title, category, date, time, city, country, latitude, longitude, consequence, macro_category, "
                        "subcategory, polarity, date_precision, quality_tier, calendar, region, source_id, source_url FROM events ORDER BY id").fetchall()
    out = []
    for r in rows:
        d = dict(r)
        out.append({k: v for k, v in d.items() if v is not None})
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    total = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    conn.close()
    print(f"  historical_events.json sincronizado ({total} eventos)")


if __name__ == "__main__":
    main()
