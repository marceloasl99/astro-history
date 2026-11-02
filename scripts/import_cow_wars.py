#!/usr/bin/env python3
"""
import_cow_wars.py
Extrai as 95 guerras interestatais do Correlates of War (COW) Inter-State War Dataset v4.0.
Gera eventos normalizados com participantes, data de eclosão, coordenadas geográficas e estimativa de baixas.
"""

import csv
import json
import os
from collections import defaultdict
from typing import Dict, Any, List

INPUT_CSV = "data/external/Inter-StateWarData_v4.0.csv"
OUTPUT_JSON = "data/external/cow_wars.json"

# Coordenadas aproximadas dos principais teatros/capitais para guerras históricas do COW
REGION_COORDINATES: Dict[str, Dict[str, Any]] = {
    "1": {"name": "América do Norte / América Central", "lat": 19.4326, "lon": -99.1332, "city": "Cidade do México", "country": "México"},
    "2": {"name": "América do Sul", "lat": -34.6037, "lon": -58.3816, "city": "Buenos Aires", "country": "Argentina"},
    "4": {"name": "Europa Ocidental / Central", "lat": 48.8566, "lon": 2.3522, "city": "Paris", "country": "França"},
    "6": {"name": "Oriente Médio & Norte da África", "lat": 31.7683, "lon": 35.2137, "city": "Jerusalém", "country": "Israel"},
    "7": {"name": "Ásia Meridional / Central", "lat": 28.6139, "lon": 77.2090, "city": "Nova Délhi", "country": "Índia"},
    "9": {"name": "Sudeste Asiático / Extremo Oriente", "lat": 37.5665, "lon": 126.9780, "city": "Seul", "country": "Coreia do Sul"},
    "11": {"name": "Leste Europeu / Balcãs", "lat": 44.7866, "lon": 20.4489, "city": "Belgrado", "country": "Sérvia"},
    "default": {"name": "Global / Múltiplos Teatros", "lat": 50.8503, "lon": 4.3517, "city": "Bruxelas", "country": "Bélgica"}
}

# Coordenadas por país histórico
COUNTRY_COORDS = {
    "Russia": {"city": "Moscou", "country": "Rússia", "lat": 55.7558, "lon": 37.6173},
    "Ottoman Empire": {"city": "Constantinopla", "country": "Império Otomano", "lat": 41.0082, "lon": 28.9784},
    "France": {"city": "Paris", "country": "França", "lat": 48.8566, "lon": 2.3522},
    "United Kingdom": {"city": "Londres", "country": "Reino Unido", "lat": 51.5074, "lon": -0.1278},
    "Spain": {"city": "Madri", "country": "Espanha", "lat": 40.4168, "lon": -3.7038},
    "United States of America": {"city": "Washington, D.C.", "country": "Estados Unidos", "lat": 38.9072, "lon": -77.0369},
    "Mexico": {"city": "Cidade do México", "country": "México", "lat": 19.4326, "lon": -99.1332},
    "Prussia": {"city": "Berlim", "country": "Alemanha", "lat": 52.5200, "lon": 13.4050},
    "Germany": {"city": "Berlim", "country": "Alemanha", "lat": 52.5200, "lon": 13.4050},
    "Austria": {"city": "Viena", "country": "Áustria", "lat": 48.2082, "lon": 16.3738},
    "Austria-Hungary": {"city": "Viena", "country": "Áustria", "lat": 48.2082, "lon": 16.3738},
    "Italy": {"city": "Roma", "country": "Itália", "lat": 41.9028, "lon": 12.4964},
    "China": {"city": "Pequim", "country": "China", "lat": 39.9042, "lon": 116.4074},
    "Japan": {"city": "Tóquio", "country": "Japão", "lat": 35.6762, "lon": 139.6503},
    "Paraguay": {"city": "Assunção", "country": "Paraguai", "lat": -25.2637, "lon": -57.5759},
    "Bolivia": {"city": "La Paz", "country": "Bolívia", "lat": -16.5000, "lon": -68.1500},
    "Ecuador": {"city": "Quito", "country": "Equador", "lat": -0.1807, "lon": -78.4678},
    "Peru": {"city": "Lima", "country": "Peru", "lat": -12.0464, "lon": -77.0428},
    "Chile": {"city": "Santiago", "country": "Chile", "lat": -33.4489, "lon": -70.6693},
    "Iran": {"city": "Teerã", "country": "Irã", "lat": 35.6892, "lon": 51.3890},
    "Iraq": {"city": "Bagdá", "country": "Iraque", "lat": 33.3152, "lon": 44.3661},
    "Israel": {"city": "Tel Aviv", "country": "Israel", "lat": 32.0853, "lon": 34.7818},
    "Egypt": {"city": "Cairo", "country": "Egito", "lat": 30.0444, "lon": 31.2357},
    "India": {"city": "Nova Délhi", "country": "Índia", "lat": 28.6139, "lon": 77.2090},
    "Pakistan": {"city": "Islamabad", "country": "Paquistão", "lat": 33.6844, "lon": 73.0479},
}

def parse_cow_date(year_str: str, month_str: str, day_str: str) -> tuple[str, str]:
    """Retorna data ISO (YYYY-MM-DD) e precisão ('day', 'month', 'year')."""
    try:
        y = int(year_str)
        m = int(month_str) if month_str and int(month_str) > 0 else 1
        d = int(day_str) if day_str and int(day_str) > 0 else 1
        
        prec = "day"
        if not day_str or int(day_str) <= 0:
            prec = "month" if (month_str and int(month_str) > 0) else "year"
            d = 1
        if not month_str or int(month_str) <= 0:
            m = 1
            prec = "year"
            
        return f"{y:04d}-{m:02d}-{d:02d}", prec
    except Exception:
        return "1800-01-01", "year"

def extract_cow_wars() -> List[Dict[str, Any]]:
    wars_dict = defaultdict(list)
    with open(INPUT_CSV, "r", encoding="latin-1") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wars_dict[row["WarNum"]].append(row)

    events = []
    for wnum, rows in sorted(wars_dict.items(), key=lambda x: int(x[0])):
        first = rows[0]
        war_name = first["WarName"]

        # Determinar data de início mais antiga entre os participantes
        earliest_tuple = None
        for r in rows:
            try:
                y = int(r["StartYear1"])
                m = int(r["StartMonth1"]) if int(r["StartMonth1"]) > 0 else 1
                d = int(r["StartDay1"]) if int(r["StartDay1"]) > 0 else 1
                t = (y, m, d)
                if earliest_tuple is None or t < earliest_tuple:
                    earliest_tuple = t
            except (ValueError, TypeError):
                continue

        if not earliest_tuple:
            continue

        date_iso = f"{earliest_tuple[0]:04d}-{earliest_tuple[1]:02d}-{earliest_tuple[2]:02d}"

        # Coletar participantes e baixas
        side1 = [r["StateName"] for r in rows if r["Side"] == "1"]
        side2 = [r["StateName"] for r in rows if r["Side"] == "2"]
        
        total_deaths = 0
        for r in rows:
            try:
                bd = int(r.get("BatDeath", -8))
                if bd > 0:
                    total_deaths += bd
            except ValueError:
                pass

        # Determinar localização geográfica
        where = first.get("WhereFought", "")
        lead_state = side1[0] if side1 else (side2[0] if side2 else "")
        coords = COUNTRY_COORDS.get(lead_state) or REGION_COORDINATES.get(where) or REGION_COORDINATES["default"]

        title_pt = f"Eclosão da Guerra {war_name}"
        combatants_str = f"{', '.join(side1[:3])} vs {', '.join(side2[:3])}"
        desc = (
            f"Guerra interestatal certificada pelo Correlates of War (COW War #{wnum}: {war_name}). "
            f"Beligerantes principais: {combatants_str}. "
            f"Estimativa de baixas militares diretas: {total_deaths:,} mortes em combate."
        )

        events.append({
            "source_id": f"COW_{wnum}",
            "title": title_pt,
            "category": "Guerra & Conflito",
            "date": date_iso,
            "time": "desconhecido",
            "city": coords["city"],
            "country": coords["country"],
            "latitude": round(coords["lat"], 4),
            "longitude": round(coords["lon"], 4),
            "consequence": desc,
            "source": "Correlates of War Inter-State War Dataset v4.0",
            "severity_deaths": total_deaths
        })

    return events

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    events = extract_cow_wars()
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print(f"Extraídas {len(events)} guerras interestatais do COW v4.0 em {OUTPUT_JSON}")
