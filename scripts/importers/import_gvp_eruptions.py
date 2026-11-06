#!/usr/bin/env python3
"""
Smithsonian Global Volcanism Program — Volcanoes of the World (erupções do Holoceno, VEI ≥ 5).
WFS: https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows (uso livre com citação).

Uso: python scripts/importers/import_gvp_eruptions.py [--merge] [--min-vei 5]
"""
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.importers.common import StagedEvent, merge_into_catalog, stage, update_manifest  # noqa: E402

WFS = "https://webservices.volcano.si.edu/geoserver/GVP-VOTW/ows"
SOURCE_ID = "gvp_holocene_eruptions_vei5"
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "external", "gvp")


def fetch(min_vei: int) -> dict:
    os.makedirs(RAW_DIR, exist_ok=True)
    raw = os.path.join(RAW_DIR, f"eruptions_vei{min_vei}.json")
    if os.path.exists(raw):
        with open(raw, encoding="utf-8") as f:
            return json.load(f)
    q = urllib.parse.urlencode({"service": "WFS", "version": "1.0.0", "request": "GetFeature",
                                "typeName": "GVP-VOTW:Smithsonian_VOTW_Holocene_Eruptions", "outputFormat": "application/json",
                                "CQL_FILTER": f"ExplosivityIndexMax>={min_vei}"})
    with urllib.request.urlopen(f"{WFS}?{q}", timeout=180) as r:
        d = json.load(r)
    with open(raw, "w", encoding="utf-8") as f:
        json.dump(d, f)
    return d


def volcano_countries() -> dict:
    """Nome do vulcão → país (camada de vulcões)."""
    raw = os.path.join(RAW_DIR, "volcanoes.json")
    if not os.path.exists(raw):
        q = urllib.parse.urlencode({"service": "WFS", "version": "1.0.0", "request": "GetFeature",
                                    "typeName": "GVP-VOTW:Smithsonian_VOTW_Holocene_Volcanoes", "outputFormat": "application/json"})
        with urllib.request.urlopen(f"{WFS}?{q}", timeout=180) as r:
            d = json.load(r)
        with open(raw, "w", encoding="utf-8") as f:
            json.dump(d, f)
    else:
        with open(raw, encoding="utf-8") as f:
            d = json.load(f)
    out = {}
    for ft in d.get("features", []):
        p = ft["properties"]
        out[p.get("Volcano_Number")] = (p.get("Country") or "", p.get("Volcanic_Region") or "")
    return out


COUNTRY_PT = {"Indonesia": "Indonésia", "Italy": "Itália", "Japan": "Japão", "Iceland": "Islândia", "Philippines": "Filipinas",
              "United States": "Estados Unidos", "Mexico": "México", "Chile": "Chile", "Peru": "Peru", "Ecuador": "Equador",
              "Guatemala": "Guatemala", "Nicaragua": "Nicarágua", "El Salvador": "El Salvador", "Russia": "Rússia", "Greece": "Grécia",
              "Papua New Guinea": "Papua-Nova Guiné", "New Zealand": "Nova Zelândia", "Vanuatu": "Vanuatu", "Tonga": "Tonga",
              "Ethiopia": "Etiópia", "Tanzania": "Tanzânia", "DR Congo": "República Democrática do Congo", "Cameroon": "Camarões",
              "China": "China", "North Korea": "Coreia do Norte", "Turkey": "Turquia", "Iran": "Irã", "Argentina": "Argentina",
              "Colombia": "Colômbia", "Costa Rica": "Costa Rica", "Martinique": "Martinica (França)", "Saint Vincent and the Grenadines": "São Vicente e Granadinas",
              "Portugal": "Portugal", "Spain": "Espanha", "Comoros": "Comores", "Eritrea": "Eritreia", "Yemen": "Iêmen", "Antarctica": "Antártida",
              "Canada": "Canadá", "Alaska": "Estados Unidos", "Kamchatka": "Rússia", "Solomon Islands": "Ilhas Salomão", "Taiwan": "Taiwan"}


def to_events(d: dict, countries: dict, min_vei: int) -> list:
    out = []
    for ft in d.get("features", []):
        p = ft["properties"]
        vei = p.get("ExplosivityIndexMax")
        y = p.get("StartDateYear")
        if vei is None or y is None or vei < min_vei:
            continue
        if p.get("StartDateYearUncertainty") and abs(p["StartDateYearUncertainty"]) > 50:
            continue  # datação por radiocarbono muito incerta
        m, dd = p.get("StartDateMonth") or 0, p.get("StartDateDay") or 0
        precision = "day" if (m and dd) else ("month" if m else ("year" if not p.get("StartDateYearUncertainty") else "decade"))
        m, dd = (m or 7), (dd or 1)
        date = f"-{abs(y):04d}-{m:02d}-{dd:02d}" if y <= 0 else f"{y:04d}-{m:02d}-{dd:02d}"
        lon, lat = ft["geometry"]["coordinates"][:2]
        cname, region = countries.get(p.get("Volcano_Number"), ("", ""))
        country = COUNTRY_PT.get(cname, cname or region or "—")
        name = p.get("Volcano_Name", "Vulcão")
        if ", " in name:  # "Chichon, El" → "El Chichon"
            base, art = name.split(", ", 1)
            name = f"{art} {base}"
        cons = (f"Erupção do vulcão {name} com Índice de Explosividade Vulcânica (VEI) {vei}, segundo o catálogo Volcanoes of the World "
                f"do Smithsonian Global Volcanism Program. Erupções VEI ≥ 5 injetam aerossóis na estratosfera e podem alterar o clima global "
                f"por anos (ex.: Tambora 1815, 'ano sem verão'). Incluída como controle cético de desastre natural.")
        out.append(StagedEvent(
            title=f"Erupção do {name} (VEI {vei})", date=date, macro_category="natural_disasters", subcategory="volcanic_eruption",
            polarity="disruptive", country=country, city=name, latitude=float(lat), longitude=float(lon), consequence=cons,
            source_id=SOURCE_ID, source_url=f"https://volcano.si.edu/volcano.cfm?vn={p.get('Volcano_Number')}", quality_tier="B",
            date_precision=precision, magnitude=float(vei), external_ids={"gvp_eruption": p.get("Eruption_Number")},
        ))
    return out


def main():
    min_vei = int(sys.argv[sys.argv.index("--min-vei") + 1]) if "--min-vei" in sys.argv else 5
    d = fetch(min_vei)
    countries = volcano_countries()
    events = to_events(d, countries, min_vei)
    print(f"GVP: {len(d.get('features', []))} erupções brutas → {len(events)} eventos")
    stage(SOURCE_ID, events)
    if "--merge" in sys.argv:
        res = merge_into_catalog(SOURCE_ID, events)
        update_manifest({
            "id": SOURCE_ID, "name": f"Smithsonian GVP — Volcanoes of the World, erupções do Holoceno VEI ≥ {min_vei}",
            "institution": "Smithsonian Institution, Global Volcanism Program", "url": "https://volcano.si.edu/",
            "license": "Uso livre com citação (Global Volcanism Program, 2024)", "file_path": f"data/external/gvp/eruptions_vei{min_vei}.json",
            "time_span": "Holoceno / 2025 CE", "records_count": res["inserted"], "category": "natural_disasters",
            "date_precision": "day|month|year|decade", "features": ["vei", "coordinates", "volcano_number"], "skeptical_control": True,
        })


if __name__ == "__main__":
    main()
