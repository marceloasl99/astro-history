#!/usr/bin/env python3
"""
import_usgs_earthquakes.py
Extrai os 200 grandes terremotos com Magnitude >= 7.8 do USGS Earthquake Hazards Program.
Inclui data ISO, hora UTC exata, magnitude e coordenadas precisas do epicentro.
"""

import json
import os
from datetime import datetime, timezone
from typing import Dict, Any, List

INPUT_JSON = "data/external/usgs_earthquakes_m78.json"
OUTPUT_JSON = "data/external/usgs_earthquakes.json"

def extract_usgs_earthquakes() -> List[Dict[str, Any]]:
    with open(INPUT_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)

    features = data.get("features", [])
    events = []

    for i, feat in enumerate(features):
        props = feat.get("properties", {})
        geom = feat.get("geometry", {})
        coords = geom.get("coordinates", [0.0, 0.0, 0.0])
        
        lon = coords[0]
        lat = coords[1]
        depth = coords[2] if len(coords) > 2 else 0.0

        mag = props.get("mag", 7.8)
        place = props.get("place", "Região Sísmica")
        time_ms = props.get("time")

        if not time_ms:
            continue

        dt = datetime.fromtimestamp(time_ms / 1000.0, tz=timezone.utc)
        date_iso = dt.strftime("%Y-%m-%d")
        time_utc = dt.strftime("%H:%M")

        # Tentar isolar o país/região do campo 'place'
        parts = [p.strip() for p in place.split(",")]
        country = parts[-1] if len(parts) > 1 else parts[0]
        city = parts[0]

        title = f"Grande Terremoto M{mag:.1f} - {place}"
        if len(title) > 90:
            title = f"Terremoto M{mag:.1f} em {country}"

        desc = (
            f"Grande sismo com magnitude de momento M {mag:.1f} e profundidade focal de {depth:.1f} km, "
            f"registrado e catalogado pelo United States Geological Survey (USGS). "
            f"Epicentro: {place} ({lat:.3f}°, {lon:.3f}°). Ocorrência em {time_utc} UTC."
        )

        events.append({
            "source_id": f"USGS_{props.get('code', i+1)}",
            "title": title,
            "category": "Desastre & Saúde Pública",
            "date": date_iso,
            "time": time_utc,
            "city": city,
            "country": country,
            "latitude": round(lat, 4),
            "longitude": round(lon, 4),
            "consequence": desc,
            "source": "USGS Earthquake Hazards Program Comprehensive Catalog (ComCat)",
            "magnitude": mag,
            "depth_km": depth
        })

    return events

if __name__ == "__main__":
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    events = extract_usgs_earthquakes()
    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    print(f"Extraídos {len(events)} grandes terremotos M>=7.8 do USGS em {OUTPUT_JSON}")
