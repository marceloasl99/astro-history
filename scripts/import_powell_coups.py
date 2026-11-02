#!/usr/bin/env python3
"""
import_powell_coups.py
Extrai os golpes de Estado do Powell & Thyne Coup d'État Dataset (1950-2026).
Gera eventos de 'Revolução & Conflito Interno' ou 'Reforma Política & Tratado' com data exata de eclosão.
"""

import csv
import json
import os
from typing import Dict, Any, List

INPUT_CSV = "data/external/powell_thyne_coups.csv"
OUTPUT_JSON = "data/external/powell_coups.json"
COUNTRIES_DB = "data/countries_database.json"

# Nomes em português para países comuns do dataset de golpes
COUNTRY_NAMES_PT = {
    "Afghanistan": "Afeganistão",
    "Algeria": "Argélia",
    "Argentina": "Argentina",
    "Azerbaijan": "Azerbaijão",
    "Bangladesh": "Bangladesh",
    "Benin": "Benin",
    "Bolivia": "Bolívia",
    "Burkina Faso": "Burkina Faso",
    "Burundi": "Burundi",
    "Cambodia": "Camboja",
    "Central African Republic": "República Centro-Africana",
    "Chad": "Chade",
    "Chile": "Chile",
    "Comoros": "Comores",
    "Congo": "República do Congo",
    "Cote d'Ivoire": "Costa do Marfim",
    "Cuba": "Cuba",
    "Cyprus": "Chipre",
    "Democratic Republic of Congo": "República Democrática do Congo",
    "Dominican Republic": "República Dominicana",
    "Ecuador": "Equador",
    "Egypt": "Egito",
    "El Salvador": "El Salvador",
    "Equatorial Guinea": "Guiné Equatorial",
    "Ethiopia": "Etiópia",
    "Fiji": "Fiji",
    "Gabon": "Gabão",
    "Gambia": "Gâmbia",
    "Georgia": "Geórgia",
    "Ghana": "Gana",
    "Greece": "Grécia",
    "Guatemala": "Guatemala",
    "Guinea": "Guiné",
    "Guinea-Bissau": "Guiné-Bissau",
    "Haiti": "Haiti",
    "Honduras": "Honduras",
    "Indonesia": "Indonésia",
    "Iran": "Irã",
    "Iraq": "Iraque",
    "Jordan": "Jordânia",
    "Kenya": "Quênia",
    "Laos": "Laos",
    "Lebanon": "Líbano",
    "Lesotho": "Lesoto",
    "Liberia": "Libéria",
    "Libya": "Líbia",
    "Madagascar": "Madagascar",
    "Mali": "Mali",
    "Mauritania": "Mauritânia",
    "Myanmar": "Mianmar",
    "Nepal": "Nepal",
    "Niger": "Níger",
    "Nigeria": "Nigéria",
    "Pakistan": "Paquistão",
    "Panama": "Panamá",
    "Paraguay": "Paraguai",
    "Peru": "Peru",
    "Philippines": "Filipinas",
    "Portugal": "Portugal",
    "Rwanda": "Ruanda",
    "Sierra Leone": "Serra Leoa",
    "Somalia": "Somália",
    "Sudan": "Sudão",
    "Suriname": "Suriname",
    "Syria": "Síria",
    "Thailand": "Tailândia",
    "Togo": "Togo",
    "Tunisia": "Tunísia",
    "Turkey": "Turquia",
    "Uganda": "Uganda",
    "Uruguay": "Uruguai",
    "Venezuela": "Venezuela",
    "Yemen": "Iêmen",
    "Zambia": "Zâmbia",
    "Zimbabwe": "Zimbábue"
}

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
    return lookup

def extract_powell_coups() -> List[Dict[str, Any]]:
    country_lookup = load_country_lookup()
    events = []

    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            cname = row["country"].strip()
            y = int(row["year"])
            m = int(row["month"])
            d = int(row["day"])
            coup_type = row["coup"]  # 1 = attempted, 2 = successful

            date_iso = f"{y:04d}-{m:02d}-{d:02d}"
            pt_country = COUNTRY_NAMES_PT.get(cname, cname)

            geo = country_lookup.get(cname.lower()) or country_lookup.get(pt_country.lower())
            if geo:
                city = geo.get("capital") or geo.get("city") or "Capital"
                lat = geo["latitude"]
                lon = geo["longitude"]
            else:
                city = "Capital"
                lat = 0.0
                lon = 0.0

            status_str = "Golpe de Estado Consumado" if coup_type == "2" else "Tentativa de Golpe Militar"
            title_pt = f"{status_str} em {pt_country} ({y})"

            desc = (
                f"{status_str} registrado na base Powell & Thyne Coup d'État Dataset. "
                f"País: {pt_country} ({cname}, COW ccode: {row.get('ccode')}). "
                f"Resultado: {'Poder deposto com sucesso' if coup_type == '2' else 'Tentativa frustrada / debelada'}."
            )

            events.append({
                "source_id": f"PT_COUP_{i+1}",
                "title": title_pt,
                "category": "Revolução & Conflito Interno",
                "date": date_iso,
                "time": "desconhecido",
                "city": city,
                "country": pt_country,
                "latitude": round(lat, 4),
                "longitude": round(lon, 4),
                "consequence": desc,
                "source": "Powell & Thyne Coup d'État Dataset (v2026.08)",
                "coup_success": (coup_type == "2")
            })

    return events

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    events = extract_powell_coups()
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print(f"Extraídos {len(events)} golpes de Estado de Powell & Thyne em {OUTPUT_JSON}")
