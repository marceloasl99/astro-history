#!/usr/bin/env python3
"""
NOAA NCEI Significant Earthquake Database (domínio público, US Gov).
API: https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes
Filtro: magnitude ≥ 7.5 (ou ≥ 1.000 mortes), 2150 a.C.–hoje. Precisão de data conforme campos disponíveis.

Uso: python scripts/importers/import_ncei_earthquakes.py [--merge] [--min-mag 7.5]
"""
import json
import os
import sys
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from scripts.importers.common import StagedEvent, merge_into_catalog, stage, update_manifest  # noqa: E402

API = "https://www.ngdc.noaa.gov/hazel/hazard-service/api/v1/earthquakes"
SOURCE_ID = "ncei_significant_earthquakes"
RAW_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "external", "ncei")

COUNTRY_PT = {
    "IRAN": "Irã", "TURKEY": "Turquia", "CHINA": "China", "JAPAN": "Japão", "ITALY": "Itália", "GREECE": "Grécia", "CHILE": "Chile",
    "PERU": "Peru", "MEXICO": "México", "INDONESIA": "Indonésia", "PHILIPPINES": "Filipinas", "INDIA": "Índia", "PAKISTAN": "Paquistão",
    "USA": "Estados Unidos", "RUSSIA": "Rússia", "PORTUGAL": "Portugal", "ECUADOR": "Equador", "COLOMBIA": "Colômbia", "GUATEMALA": "Guatemala",
    "NICARAGUA": "Nicarágua", "EL SALVADOR": "El Salvador", "HAITI": "Haiti", "JAMAICA": "Jamaica", "ARGENTINA": "Argentina", "BOLIVIA": "Bolívia",
    "VENEZUELA": "Venezuela", "NEPAL": "Nepal", "AFGHANISTAN": "Afeganistão", "ARMENIA": "Armênia", "GEORGIA": "Geórgia", "AZERBAIJAN": "Azerbaijão",
    "SYRIA": "Síria", "LEBANON": "Líbano", "ISRAEL": "Israel", "EGYPT": "Egito", "ALGERIA": "Argélia", "MOROCCO": "Marrocos", "TAIWAN": "Taiwan",
    "NEW ZEALAND": "Nova Zelândia", "PAPUA NEW GUINEA": "Papua-Nova Guiné", "SOLOMON ISLANDS": "Ilhas Salomão", "VANUATU": "Vanuatu", "TONGA": "Tonga",
    "FIJI": "Fiji", "SAMOA": "Samoa", "MYANMAR (BURMA)": "Mianmar", "BANGLADESH": "Bangladesh", "SRI LANKA": "Sri Lanka", "THAILAND": "Tailândia",
    "VIETNAM": "Vietnã", "CANADA": "Canadá", "ALASKA": "Estados Unidos", "HAWAII": "Estados Unidos", "ICELAND": "Islândia", "UZBEKISTAN": "Uzbequistão",
    "KYRGYZSTAN": "Quirguistão", "TAJIKISTAN": "Tajiquistão", "KAZAKHSTAN": "Cazaquistão", "MONGOLIA": "Mongólia", "SPAIN": "Espanha", "FRANCE": "França",
    "GERMANY": "Alemanha", "SWITZERLAND": "Suíça", "AUSTRIA": "Áustria", "ROMANIA": "Romênia", "BULGARIA": "Bulgária", "ALBANIA": "Albânia",
    "CROATIA": "Croácia", "MONTENEGRO": "Montenegro", "NORTH MACEDONIA": "Macedônia do Norte", "CYPRUS": "Chipre", "IRAQ": "Iraque", "YEMEN": "Iêmen",
    "SAUDI ARABIA": "Arábia Saudita", "OMAN": "Omã", "ETHIOPIA": "Etiópia", "KENYA": "Quênia", "TANZANIA": "Tanzânia", "MOZAMBIQUE": "Moçambique",
    "SOUTH AFRICA": "África do Sul", "SUDAN": "Sudão", "LIBYA": "Líbia", "TUNISIA": "Tunísia", "CUBA": "Cuba", "DOMINICAN REPUBLIC": "República Dominicana",
    "PUERTO RICO": "Porto Rico", "COSTA RICA": "Costa Rica", "PANAMA": "Panamá", "HONDURAS": "Honduras", "AUSTRALIA": "Austrália", "KOREA": "Coreia",
    "SOUTH KOREA": "Coreia do Sul", "NORTH KOREA": "Coreia do Norte", "UK": "Reino Unido", "NORWAY": "Noruega", "SOLOMON ISLANDS ": "Ilhas Salomão",
}


def fetch_all(min_mag: float) -> list:
    os.makedirs(RAW_DIR, exist_ok=True)
    raw_path = os.path.join(RAW_DIR, f"earthquakes_m{min_mag}.json")
    if os.path.exists(raw_path):
        with open(raw_path, encoding="utf-8") as f:
            return json.load(f)
    items, page = [], 1
    while True:
        q = urllib.parse.urlencode({"minEqMagnitude": min_mag, "itemsPerPage": 200, "page": page})
        with urllib.request.urlopen(f"{API}?{q}", timeout=120) as r:
            d = json.load(r)
        items.extend(d["items"])
        if page >= d.get("totalPages", 1):
            break
        page += 1
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(items, f)
    return items


def to_events(items: list) -> list:
    out = []
    for it in items:
        y = it.get("year")
        if y is None:
            continue
        m, d = it.get("month"), it.get("day")
        precision = "day" if (m and d) else ("month" if m else "year")
        m = m or 7
        d = d or 1
        if y <= 0:
            date = f"-{abs(y) if y < 0 else 1:04d}-{m:02d}-{d:02d}"
        else:
            date = f"{y:04d}-{m:02d}-{d:02d}"
        hour, minute = it.get("hour"), it.get("minute")
        time_str = f"{int(hour):02d}:{int(minute or 0):02d}" if hour is not None and precision == "day" else "desconhecido"
        country_raw = (it.get("country") or "").strip()
        country = COUNTRY_PT.get(country_raw, country_raw.title() if country_raw else "Oceano")
        loc = (it.get("locationName") or "").split(":")[-1].strip().title() or country
        mag = it.get("eqMagnitude")
        deaths = it.get("deathsTotal") or it.get("deaths")
        tsunami = " Gerou tsunami." if it.get("tsunamiEventId") else ""
        cons = (f"Terremoto de magnitude {mag} registrado pelo catálogo de sismos significativos da NOAA/NCEI em {loc}, {country}"
                f"{f', com cerca de {int(deaths):,} mortes'.replace(',', '.') if deaths else ''}.{tsunami} "
                f"Evento geofísico incluído como controle cético: o céu não deveria 'prever' terremotos melhor do que guerras.")
        title = f"Terremoto de {loc} (M {mag})" if mag else f"Terremoto de {loc}"
        out.append(StagedEvent(
            title=title[:160], date=date, macro_category="natural_disasters", subcategory="earthquake", polarity="disruptive",
            country=country, city=loc[:80], latitude=float(it.get("latitude") or 0.0), longitude=float(it.get("longitude") or 0.0),
            consequence=cons, source_id=SOURCE_ID, source_url=f"https://www.ngdc.noaa.gov/hazel/view/hazards/earthquake/event-more-info/{it['id']}",
            quality_tier="B", date_precision=precision, time=time_str, magnitude=float(mag) if mag else None,
            external_ids={"ncei_eq": it["id"]},
        ))
    return out


def main():
    min_mag = 7.5
    if "--min-mag" in sys.argv:
        min_mag = float(sys.argv[sys.argv.index("--min-mag") + 1])
    items = fetch_all(min_mag)
    events = to_events(items)
    print(f"NCEI: {len(items)} registros brutos → {len(events)} eventos")
    stage(SOURCE_ID, events)
    if "--merge" in sys.argv:
        res = merge_into_catalog(SOURCE_ID, events)
        update_manifest({
            "id": SOURCE_ID, "name": "NOAA NCEI Significant Earthquake Database (M ≥ 7.5)",
            "institution": "National Centers for Environmental Information (NOAA)",
            "url": "https://www.ngdc.noaa.gov/hazel/view/hazards/earthquake/search", "license": "Domínio Público (US Government Work)",
            "file_path": f"data/external/ncei/earthquakes_m{min_mag}.json", "time_span": "2150 BCE / 2025 CE",
            "records_count": res["inserted"], "category": "natural_disasters", "date_precision": "day|month|year",
            "features": ["magnitude", "deaths", "tsunami_flag", "coordinates"], "skeptical_control": True,
        })


if __name__ == "__main__":
    main()
