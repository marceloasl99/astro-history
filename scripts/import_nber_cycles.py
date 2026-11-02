#!/usr/bin/env python3
"""
import_nber_cycles.py
Extrai os picos de ciclos econômicos (início de recessões) certificados pelo NBER (1857-2020).
Categoria: 'Crise Financeira & Econômica'.
"""

import json
import os
from typing import Dict, Any, List

INPUT_JSON = "data/external/business_cycle_dates.json"
OUTPUT_JSON = "data/external/nber_cycles.json"

def extract_nber_cycles() -> List[Dict[str, Any]]:
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    events = []
    for i, item in enumerate(data):
        peak = item.get("peak")
        trough = item.get("trough")
        if not peak:
            continue

        year = peak[:4]
        title = f"Pico do Ciclo Econômico e Início de Recessão NBER ({year})"
        desc = (
            f"Ponto de inflexão macroeconômica certificado pelo Business Cycle Dating Committee do NBER. "
            f"Marca a transição de expansão para contração econômica (recessão até o vale em {trough})."
        )

        events.append({
            "source_id": f"NBER_PEAK_{i+1}",
            "title": title,
            "category": "Crise Financeira & Econômica",
            "date": peak,
            "time": "desconhecido",
            "city": "Nova York",
            "country": "Estados Unidos",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "consequence": desc,
            "source": "National Bureau of Economic Research (NBER) US Business Cycle Expansions and Contractions",
            "trough_date": trough
        })

    return events

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    events = extract_nber_cycles()
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print(f"Extraídos {len(events)} picos de recessão do NBER em {OUTPUT_JSON}")
