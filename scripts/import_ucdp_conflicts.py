#!/usr/bin/env python3
"""
import_ucdp_conflicts.py
Extrai os conflitos armados únicos do UCDP/PRIO Armed Conflict Dataset v24.1.
Agrupa por conflict_id, seleciona episódios com data precisa (start_prec <= 3),
categoriza entre 'Guerra & Conflito' e 'Revolução & Conflito Interno' e mapeia coordenadas geográficas.
"""

import csv
import json
import os
from collections import defaultdict
from typing import Dict, Any, List

INPUT_CSV = "data/external/UcdpPrioConflict_v24_1.csv"
OUTPUT_JSON = "data/external/ucdp_conflicts.json"
COUNTRIES_DB = "data/countries_database.json"

def load_country_lookup() -> Dict[str, Dict[str, Any]]:
    lookup = {}
    if os.path.exists(COUNTRIES_DB):
        with open(COUNTRIES_DB, "r", encoding="utf-8") as f:
            countries = json.load(f)
            for c in countries:
                if c.get("name_en"):
                    lookup[c["name_en"].lower()] = c
                if c.get("name_pt"):
                    lookup[c["name_pt"].lower()] = c
                if c.get("iso_code"):
                    lookup[c["iso_code"].lower()] = c
    return lookup

# Coordenadas padrão para locais frequentes que possam ter grafia variante
EXTRA_COORDINATES = {
    "vietnam": {"city": "Hanói", "country": "Vietnã", "lat": 21.0285, "lon": 105.8542},
    "korea": {"city": "Seul", "country": "Coreia", "lat": 37.5665, "lon": 126.9780},
    "dr congo (zaire)": {"city": "Kinshasa", "country": "República Democrática do Congo", "lat": -4.4419, "lon": 15.2663},
    "congo": {"city": "Brazzaville", "country": "Congo", "lat": -4.2634, "lon": 15.2828},
    "yemen (north yemen)": {"city": "Sanaa", "country": "Iêmen", "lat": 15.3694, "lon": 44.1910},
    "yemen (south yemen)": {"city": "Áden", "country": "Iêmen", "lat": 12.7797, "lon": 45.0367},
    "russia (soviet union)": {"city": "Moscou", "country": "Rússia", "lat": 55.7558, "lon": 37.6173},
    "myanmar (burma)": {"city": "Yangon", "country": "Mianmar", "lat": 16.8661, "lon": 96.1951},
    "cambodia (kampuchea)": {"city": "Phnom Penh", "country": "Camboja", "lat": 11.5564, "lon": 104.9282},
    "bosnia-herzegovina": {"city": "Sarajevo", "country": "Bósnia e Herzegovina", "lat": 43.8563, "lon": 18.4131},
    "syria": {"city": "Damasco", "country": "Síria", "lat": 33.5138, "lon": 36.2765},
    "lebanon": {"city": "Beirute", "country": "Líbano", "lat": 33.8938, "lon": 35.5018},
    "sudan": {"city": "Cartum", "country": "Sudão", "lat": 15.5007, "lon": 32.5599},
    "south sudan": {"city": "Juba", "country": "Sudão do Sul", "lat": 4.8594, "lon": 31.5713},
    "somalia": {"city": "Mogadíscio", "country": "Somália", "lat": 2.0469, "lon": 45.3182},
    "afghanistan": {"city": "Cabul", "country": "Afeganistão", "lat": 34.5553, "lon": 69.2075},
    "iraq": {"city": "Bagdá", "country": "Iraque", "lat": 33.3152, "lon": 44.3661},
    "iran": {"city": "Teerã", "country": "Irã", "lat": 35.6892, "lon": 51.3890},
    "colombia": {"city": "Bogotá", "country": "Colômbia", "lat": 4.7110, "lon": -74.0721},
    "chad": {"city": "N'Djamena", "country": "Chade", "lat": 12.1348, "lon": 15.0557},
    "angola": {"city": "Luanda", "country": "Angola", "lat": -8.8390, "lon": 13.2894},
    "mozambique": {"city": "Maputo", "country": "Moçambique", "lat": -25.9692, "lon": 32.5732},
    "algeria": {"city": "Argel", "country": "Argélia", "lat": 36.7538, "lon": 3.0588},
    "uganda": {"city": "Kampala", "country": "Uganda", "lat": 0.3476, "lon": 32.5825},
    "ethiopia": {"city": "Adis Abeba", "country": "Etiópia", "lat": 9.0300, "lon": 38.7400},
    "rwanda": {"city": "Kigali", "country": "Ruanda", "lat": -1.9441, "lon": 30.0619},
    "sri lanka": {"city": "Colombo", "country": "Sri Lanka", "lat": 6.9271, "lon": 79.8612},
    "philippines": {"city": "Manila", "country": "Filipinas", "lat": 14.5995, "lon": 120.9842},
    "nicaragua": {"city": "Manágua", "country": "Nicarágua", "lat": 12.1150, "lon": -86.2362},
    "el salvador": {"city": "San Salvador", "country": "El Salvador", "lat": 13.6929, "lon": -89.2182},
    "guatemala": {"city": "Cidade da Guatemala", "country": "Guatemala", "lat": 14.6349, "lon": -90.5069},
}

def resolve_location(loc_str: str, country_lookup: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    first_loc = loc_str.split(",")[0].strip().lower()
    if first_loc in EXTRA_COORDINATES:
        c = EXTRA_COORDINATES[first_loc]
        return {"city": c["city"], "country": c["country"], "lat": c["lat"], "lon": c["lon"]}
    
    if first_loc in country_lookup:
        c = country_lookup[first_loc]
        return {
            "city": c.get("capital") or c.get("city") or first_loc.title(),
            "country": c.get("name_pt") or c.get("name_en") or first_loc.title(),
            "lat": c["latitude"],
            "lon": c["longitude"]
        }
    
    return {"city": loc_str.split(",")[0].strip(), "country": loc_str.split(",")[0].strip(), "lat": 20.0, "lon": 0.0}

def extract_ucdp_conflicts() -> List[Dict[str, Any]]:
    country_lookup = load_country_lookup()
    conflicts_dict = defaultdict(list)
    
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            conflicts_dict[row["conflict_id"]].append(row)

    events = []
    for cid, rows in conflicts_dict.items():
        first = rows[0]
        start_prec = int(first.get("start_prec", 9))
        
        # Filtra apenas conflitos com data de início confiável (precisão 1, 2 ou 3)
        if start_prec > 3:
            continue
            
        start_date = first.get("start_date")
        if not start_date or len(start_date) < 10:
            continue

        loc = first.get("location", "Internacional")
        side_a = first.get("side_a", "Governo")
        side_b = first.get("side_b", "Oposição")
        conflict_type = first.get("type_of_conflict", "3")
        incomp = first.get("incompatibility", "2")
        terr = first.get("territory_name")

        # Categoria do AstroHistory
        if conflict_type == "2":
            category = "Guerra & Conflito"
        else:
            category = "Revolução & Conflito Interno"

        geo = resolve_location(loc, country_lookup)

        motivo = f"pelo controle de {terr}" if (incomp == "1" and terr) else "pelo controle do governo central"
        title_pt = f"Eclosão do Conflito em {geo['country']}: {side_a} vs {side_b}"
        if len(title_pt) > 90:
            title_pt = f"Conflito Armado em {geo['country']} (UCDP #{cid})"

        desc = (
            f"Eclosão de conflito armado documentado pelo Uppsala Conflict Data Program (UCDP #{cid}). "
            f"Beligerantes: {side_a} versus {side_b} ({motivo}). "
            f"Tipo UCDP: {conflict_type} (precisão cronológica: nível {start_prec})."
        )

        events.append({
            "source_id": f"UCDP_{cid}",
            "title": title_pt,
            "category": category,
            "date": start_date[:10],
            "time": "desconhecido",
            "city": geo["city"],
            "country": geo["country"],
            "latitude": round(geo["lat"], 4),
            "longitude": round(geo["lon"], 4),
            "consequence": desc,
            "source": "UCDP/PRIO Armed Conflict Dataset v24.1",
            "start_prec": start_prec
        })

    return events

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    events = extract_ucdp_conflicts()
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print(f"Extraídos {len(events)} conflitos armados do UCDP v24.1 em {OUTPUT_JSON}")
