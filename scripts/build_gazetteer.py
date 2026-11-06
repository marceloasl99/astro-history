#!/usr/bin/env python3
"""
Constrói o gazetteer offline (cidades ≥ 15 mil habitantes) a partir dos dumps do GeoNames
(CC BY 4.0 — https://www.geonames.org/) em data/external/geonames/:
  cities15000.zip, admin1CodesASCII.txt, countryInfo.txt

Saída: data/gazetteer/cities.sqlite (tabela `cities` + índice FTS5 `cities_fts`).
Uso:   python scripts/build_gazetteer.py
"""
import io
import json
import os
import sqlite3
import sys
import unicodedata
import zipfile

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SRC = os.path.join(ROOT, "data", "external", "geonames")
OUT_DIR = os.path.join(ROOT, "data", "gazetteer")
OUT = os.path.join(OUT_DIR, "cities.sqlite")
COUNTRIES_PT = os.path.join(ROOT, "data", "countries_database.json")

# Nomes em português para países frequentes que não constam em countries_database.json.
EXTRA_PT = {
    "AF": "Afeganistão", "AL": "Albânia", "DZ": "Argélia", "AO": "Angola", "AR": "Argentina", "AM": "Armênia",
    "AU": "Austrália", "AT": "Áustria", "AZ": "Azerbaijão", "BD": "Bangladesh", "BY": "Bielorrússia", "BE": "Bélgica",
    "BO": "Bolívia", "BA": "Bósnia e Herzegovina", "BR": "Brasil", "BG": "Bulgária", "KH": "Camboja", "CM": "Camarões",
    "CA": "Canadá", "CL": "Chile", "CN": "China", "CO": "Colômbia", "CD": "República Democrática do Congo",
    "CR": "Costa Rica", "HR": "Croácia", "CU": "Cuba", "CZ": "Tchéquia", "DK": "Dinamarca", "DO": "República Dominicana",
    "EC": "Equador", "EG": "Egito", "SV": "El Salvador", "ET": "Etiópia", "FI": "Finlândia", "FR": "França",
    "DE": "Alemanha", "GH": "Gana", "GR": "Grécia", "GT": "Guatemala", "HT": "Haiti", "HN": "Honduras", "HU": "Hungria",
    "IN": "Índia", "ID": "Indonésia", "IR": "Irã", "IQ": "Iraque", "IE": "Irlanda", "IL": "Israel", "IT": "Itália",
    "JM": "Jamaica", "JP": "Japão", "JO": "Jordânia", "KZ": "Cazaquistão", "KE": "Quênia", "KR": "Coreia do Sul",
    "KP": "Coreia do Norte", "LB": "Líbano", "LY": "Líbia", "MY": "Malásia", "MX": "México", "MA": "Marrocos",
    "MZ": "Moçambique", "NL": "Países Baixos", "NZ": "Nova Zelândia", "NI": "Nicarágua", "NG": "Nigéria", "NO": "Noruega",
    "PK": "Paquistão", "PA": "Panamá", "PY": "Paraguai", "PE": "Peru", "PH": "Filipinas", "PL": "Polônia", "PT": "Portugal",
    "RO": "Romênia", "RU": "Rússia", "SA": "Arábia Saudita", "RS": "Sérvia", "SG": "Singapura", "SK": "Eslováquia",
    "SI": "Eslovênia", "ZA": "África do Sul", "ES": "Espanha", "LK": "Sri Lanka", "SE": "Suécia", "CH": "Suíça",
    "SY": "Síria", "TW": "Taiwan", "TZ": "Tanzânia", "TH": "Tailândia", "TN": "Tunísia", "TR": "Turquia", "UA": "Ucrânia",
    "AE": "Emirados Árabes Unidos", "GB": "Reino Unido", "US": "Estados Unidos", "UY": "Uruguai", "UZ": "Uzbequistão",
    "VE": "Venezuela", "VN": "Vietnã", "YE": "Iêmen", "ZW": "Zimbábue", "ZM": "Zâmbia", "SN": "Senegal", "CI": "Costa do Marfim",
    "GE": "Geórgia", "LT": "Lituânia", "LV": "Letônia", "EE": "Estônia", "IS": "Islândia", "LU": "Luxemburgo", "MT": "Malta",
    "CY": "Chipre", "MK": "Macedônia do Norte", "MD": "Moldávia", "ME": "Montenegro", "XK": "Kosovo", "MN": "Mongólia",
    "NP": "Nepal", "MM": "Mianmar", "LA": "Laos", "GN": "Guiné", "ML": "Mali", "NE": "Níger", "TD": "Chade", "SD": "Sudão",
    "SS": "Sudão do Sul", "SO": "Somália", "UG": "Uganda", "RW": "Ruanda", "MG": "Madagascar", "NA": "Namíbia", "BW": "Botsuana",
    "CV": "Cabo Verde", "GW": "Guiné-Bissau", "ST": "São Tomé e Príncipe", "TL": "Timor-Leste", "MO": "Macau", "HK": "Hong Kong",
    "PR": "Porto Rico", "TT": "Trinidad e Tobago", "GY": "Guiana", "SR": "Suriname", "GF": "Guiana Francesa", "BZ": "Belize",
    "QA": "Catar", "KW": "Kuwait", "OM": "Omã", "BH": "Bahrein", "PS": "Palestina", "AF ": "Afeganistão",
}


def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def is_latinish(s: str) -> bool:
    return all(ord(c) < 0x0530 for c in s)


def load_country_names():
    en, pt = {}, {}
    with open(os.path.join(SRC, "countryInfo.txt"), encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            cols = line.rstrip("\n").split("\t")
            iso2, iso3, name = cols[0], cols[1], cols[4]
            en[iso2] = name
            pt[iso2] = EXTRA_PT.get(iso2, name)
    try:
        with open(COUNTRIES_PT, encoding="utf-8") as f:
            for c in json.load(f):
                iso3 = c.get("iso_code")
                for iso2, n3 in _iso3_map().items():
                    if n3 == iso3 and c.get("name_pt"):
                        pt[iso2] = c["name_pt"]
    except Exception:
        pass
    return en, pt


_ISO3 = None


def _iso3_map():
    global _ISO3
    if _ISO3 is None:
        _ISO3 = {}
        with open(os.path.join(SRC, "countryInfo.txt"), encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or not line.strip():
                    continue
                cols = line.split("\t")
                _ISO3[cols[0]] = cols[1]
    return _ISO3


def load_admin1():
    out = {}
    with open(os.path.join(SRC, "admin1CodesASCII.txt"), encoding="utf-8") as f:
        for line in f:
            cols = line.rstrip("\n").split("\t")
            if len(cols) >= 2:
                out[cols[0]] = cols[1]
    return out


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    if os.path.exists(OUT):
        os.remove(OUT)
    en, pt = load_country_names()
    admin1 = load_admin1()
    conn = sqlite3.connect(OUT)
    conn.executescript("""
        CREATE TABLE cities (
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, ascii_name TEXT NOT NULL,
            country_code TEXT NOT NULL, country_pt TEXT, country_en TEXT, admin1 TEXT,
            lat REAL NOT NULL, lon REAL NOT NULL, population INTEGER, tz TEXT NOT NULL
        );
        CREATE VIRTUAL TABLE cities_fts USING fts5(name, ascii_name, alt_names, country, admin1,
            content='', tokenize='unicode61 remove_diacritics 2');
        CREATE INDEX idx_cities_pop ON cities(population DESC);
    """)
    with zipfile.ZipFile(os.path.join(SRC, "cities15000.zip")) as z:
        raw = z.read("cities15000.txt").decode("utf-8")
    n = 0
    rows, fts = [], []
    for line in io.StringIO(raw):
        c = line.rstrip("\n").split("\t")
        if len(c) < 18:
            continue
        gid, name, ascii_name, alts, lat, lon = int(c[0]), c[1], c[2], c[3], float(c[4]), float(c[5])
        fclass, cc, a1, pop, tz = c[6], c[8], c[10], int(c[14] or 0), c[17]
        if fclass != "P" or not tz:
            continue
        alt_list = [a for a in alts.split(",") if a and is_latinish(a) and len(a) <= 40]
        alt_join = " ".join(dict.fromkeys(alt_list))[:600]
        admin = admin1.get(f"{cc}.{a1}", "")
        rows.append((gid, name, ascii_name, cc, pt.get(cc, en.get(cc, cc)), en.get(cc, cc), admin, lat, lon, pop, tz))
        fts.append((gid, name, strip_accents(ascii_name), alt_join,
                    f"{pt.get(cc, '')} {en.get(cc, '')} {cc}", strip_accents(admin)))
        n += 1
    conn.executemany("INSERT INTO cities VALUES (?,?,?,?,?,?,?,?,?,?,?)", rows)
    conn.executemany("INSERT INTO cities_fts(rowid, name, ascii_name, alt_names, country, admin1) VALUES (?,?,?,?,?,?)", fts)
    conn.commit()
    conn.execute("INSERT INTO cities_fts(cities_fts) VALUES('optimize')")
    conn.commit()
    conn.execute("VACUUM")
    conn.close()
    print(f"{n} cidades gravadas em {OUT} ({os.path.getsize(OUT)/1e6:.1f} MB)")


if __name__ == "__main__":
    main()
