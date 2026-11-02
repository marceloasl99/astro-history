#!/usr/bin/env python3
"""
expand_historical_database.py
Orquestrador central de expansão da base histórica do AstroHistory.
Funde o catálogo legado (300 eventos) com as bases internacionais auditadas:
- COW Inter-State Wars v4.0 (95 guerras)
- UCDP/PRIO v24.1 (264 conflitos armados com data precisa)
- Powell & Thyne Coup d'État Dataset (497 golpes)
- USGS Earthquake Hazards Program (200 grandes terremotos M>=7.8 com hora UTC)
- NBER US Business Cycles (34 picos de recessão)
- Curated Milestones (28 tratados, descobertas e marcos da Antiguidade ao séc. XXI)

Aplica deduplicação fuzzy, preserva os IDs 1-300 originais,
atualiza data/historical_events.json e alimenta db/history_astrology.db.
"""

import json
import os
import re
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Set, Tuple

LEGACY_EVENTS_JSON = "data/historical_events.json"
EXPANDED_EVENTS_JSON = "data/historical_events.json"
DB_PATH = "db/history_astrology.db"

SOURCE_FILES = [
    ("Curated Milestones", "data/external/curated_milestones.json"),
    ("COW Inter-State Wars v4.0", "data/external/cow_wars.json"),
    ("UCDP/PRIO Conflicts v24.1", "data/external/ucdp_conflicts.json"),
    ("USGS Earthquakes M>=7.8", "data/external/usgs_earthquakes.json"),
    ("NBER Business Cycles", "data/external/nber_cycles.json"),
    ("Powell & Thyne Coups", "data/external/powell_coups.json"),
]

# Normalização de categorias para o padrão canônico do AstroHistory
CATEGORY_NORMALIZATION = {
    "Guerra & Conflito": "Guerra & Conflito",
    "Guerra e Conflito": "Guerra & Conflito",
    "Revolução & Conflito Interno": "Revolução & Conflito Interno",
    "Revolução e Conflito Interno": "Revolução & Conflito Interno",
    "Revolução Política": "Revolução & Conflito Interno",
    "Crise Financeira & Econômica": "Crise Financeira & Econômica",
    "Crise Financeira e Econômica": "Crise Financeira & Econômica",
    "Crise Econômica": "Crise Financeira & Econômica",
    "Desastre & Saúde Pública": "Desastre & Saúde Pública",
    "Desastre e Saúde Pública": "Desastre & Saúde Pública",
    "Pandemia & Desastre": "Desastre & Saúde Pública",
    "Ciência & Tecnologia": "Ciência & Tecnologia",
    "Ciência e Tecnologia": "Ciência & Tecnologia",
    "Reforma Política & Tratado": "Política, Tratados & Cultura",
    "Reforma Política e Tratado": "Política, Tratados & Cultura",
    "Cultura & Filosofia": "Política, Tratados & Cultura",
    "Cultura e Filosofia": "Política, Tratados & Cultura",
    "Transformação Cultural": "Política, Tratados & Cultura",
    "Política, Tratados & Cultura": "Política, Tratados & Cultura",
}

def clean_text_for_sim(text: str) -> Set[str]:
    """Retorna conjunto de tokens significativos para comparação léxica."""
    stop = {"de", "da", "do", "das", "dos", "em", "no", "na", "nos", "nas", "e", "a", "o", "as", "os", "por", "para", "com", "the", "of", "and", "in", "guerra", "batalha", "conflito", "golpe"}
    words = re.findall(r"\w+", text.lower())
    return {w for w in words if len(w) > 2 and w not in stop}

def parse_date_safe(date_str: str) -> Tuple[int, int, int]:
    """Extrai (ano, mês, dia) de uma data string."""
    try:
        clean = date_str.strip()
        is_bc = clean.startswith("-")
        if is_bc:
            clean = clean[1:]
        parts = clean.split("-")
        y = int(parts[0]) * (-1 if is_bc else 1)
        m = int(parts[1]) if len(parts) > 1 else 1
        d = int(parts[2]) if len(parts) > 2 else 1
        return (y, m, d)
    except Exception:
        return (1800, 1, 1)

def is_duplicate(candidate: Dict[str, Any], accepted: List[Dict[str, Any]]) -> Tuple[bool, str]:
    """
    Verifica se o candidato já existe na base aceita.
    Critérios:
    1. Mesma data exata (ou até 3 dias) E alta sobreposição de palavras-chave no título/cidade.
    2. Mesmo país E mesma data exata (ano, mês, dia) E mesma categoria.
    """
    c_y, c_m, c_d = parse_date_safe(candidate["date"])
    c_tokens = clean_text_for_sim(candidate["title"])
    c_country = candidate.get("country", "").lower().strip()
    c_cat = candidate.get("category", "")

    for acc in accepted:
        a_y, a_m, a_d = parse_date_safe(acc["date"])
        
        # Se anos forem diferentes, não é duplicata
        if c_y != a_y:
            continue

        # Se meses e dias forem próximos (<= 3 dias no mesmo mês/ano)
        same_date = (c_m == a_m and abs(c_d - a_d) <= 3)
        if not same_date:
            continue

        a_tokens = clean_text_for_sim(acc["title"])
        common_tokens = c_tokens.intersection(a_tokens)
        a_country = acc.get("country", "").lower().strip()
        a_cat = acc.get("category", "")

        # Condição 1: mesma data e tokens em comum significativos
        if len(common_tokens) >= 2:
            return True, f"Similaridade textual com #{acc['id']} '{acc['title']}' na data {acc['date']}"

        # Condição 2: mesmo país, mesma data e mesma categoria
        if c_country and a_country and (c_country in a_country or a_country in c_country):
            if c_cat == a_cat and c_m == a_m and c_d == a_d:
                return True, f"Mesmo país ({c_country}), categoria ({c_cat}) e data exata ({acc['date']}) que #{acc['id']}"

    return False, ""

def expand_database():
    print("Iniciando expansão da base histórica do AstroHistory...")

    # 1. Carregar catálogo legado
    if not os.path.exists(LEGACY_EVENTS_JSON):
        raise FileNotFoundError(f"Arquivo legado não encontrado: {LEGACY_EVENTS_JSON}")

    with open(LEGACY_EVENTS_JSON, "r", encoding="utf-8") as f:
        legacy_events = json.load(f)

    print(f"Catálogo legado carregado: {len(legacy_events)} eventos.")

    accepted_events: List[Dict[str, Any]] = []
    # Preservar 100% dos eventos legados com seus IDs e atributos
    for ev in legacy_events:
        ev["category"] = CATEGORY_NORMALIZATION.get(ev.get("category"), ev.get("category"))
        accepted_events.append(ev)

    next_id = max(e["id"] for e in accepted_events) + 1
    rejected_duplicates = []

    # 2. Iterar fontes externas e integrar
    for source_name, file_path in SOURCE_FILES:
        if not os.path.exists(file_path):
            print(f"Aviso: arquivo da fonte '{source_name}' ({file_path}) não encontrado. Pulando.")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            candidates = json.load(f)

        added_from_source = 0
        for cand in candidates:
            # Normalizar categoria
            cat = CATEGORY_NORMALIZATION.get(cand.get("category"), "Reforma Política & Tratado")
            
            # Sanitizar campos
            clean_event = {
                "id": next_id,
                "title": cand["title"].strip(),
                "category": cat,
                "date": cand["date"].strip(),
                "time": cand.get("time", "desconhecido"),
                "city": cand.get("city", "Capital"),
                "country": cand.get("country", "Internacional"),
                "latitude": float(cand.get("latitude", 0.0)),
                "longitude": float(cand.get("longitude", 0.0)),
                "consequence": cand.get("consequence", cand.get("description", "")).strip(),
            }

            is_dup, reason = is_duplicate(clean_event, accepted_events)
            if is_dup:
                rejected_duplicates.append({
                    "source": source_name,
                    "title": clean_event["title"],
                    "date": clean_event["date"],
                    "reason": reason
                })
                continue

            accepted_events.append(clean_event)
            next_id += 1
            added_from_source += 1

        print(f"Fonte '{source_name}': adicionados {added_from_source} de {len(candidates)} candidatos.")

    print(f"\nTotal final de eventos no catálogo expandido: {len(accepted_events)} (Duplicatas descartadas: {len(rejected_duplicates)})")

    # 3. Salvar catálogo expandido em JSON
    with open(EXPANDED_EVENTS_JSON, "w", encoding="utf-8") as f:
        json.dump(accepted_events, f, indent=2, ensure_ascii=False)
    print(f"Salvo arquivo {EXPANDED_EVENTS_JSON}")

    # 4. Atualizar banco SQLite db/history_astrology.db
    if os.path.exists(DB_PATH):
        print(f"Sincronizando {len(accepted_events)} eventos na tabela 'events' do SQLite ({DB_PATH})...")
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        # Inserir ou atualizar na tabela events mantendo dados calculados existentes para os IDs 1-300
        cur.executemany("""
            INSERT INTO events (
                id, title, category, date, time, city, country,
                latitude, longitude, consequence, calculated
            ) VALUES (
                :id, :title, :category, :date, :time, :city, :country,
                :latitude, :longitude, :consequence, 0
            ) ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                category=excluded.category,
                date=excluded.date,
                time=excluded.time,
                city=excluded.city,
                country=excluded.country,
                latitude=excluded.latitude,
                longitude=excluded.longitude,
                consequence=excluded.consequence;
        """, accepted_events)

        conn.commit()
        
        cur.execute("SELECT COUNT(*) FROM events;")
        total_db = cur.fetchone()[0]
        print(f"Tabela 'events' atualizada no SQLite. Total de registros: {total_db}")
        conn.close()

    return accepted_events, rejected_duplicates

if __name__ == "__main__":
    expand_database()
