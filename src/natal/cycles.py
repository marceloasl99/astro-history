"""
Rotulagem dos ciclos de vida (retornos planetários e aspectos genéricos de idade)
a partir das janelas de trânsito em que o corpo em trânsito encontra o próprio ponto natal.
"""

from typing import Any, Dict, List

from src.natal.bodies import SAME_BODY

# Períodos sinódicos/orbitais aproximados (anos) para numerar os retornos.
PERIOD_YEARS = {
    "sun": 1.0, "jupiter": 11.86, "saturn": 29.46, "uranus": 84.0, "neptune": 164.8, "pluto": 248.0,
    "chiron": 50.4, "mean_node": 18.6, "mars": 1.88, "venus": 1.0, "mercury": 1.0, "lilith": 8.85,
}

CYCLE_LABELS = {
    ("saturn", "conjunction"): ("Retorno de Saturno", "Saturn Return"),
    ("saturn", "square"): ("Quadratura de Saturno", "Saturn Square"),
    ("saturn", "opposition"): ("Oposição de Saturno", "Saturn Opposition"),
    ("jupiter", "conjunction"): ("Retorno de Júpiter", "Jupiter Return"),
    ("jupiter", "opposition"): ("Oposição de Júpiter", "Jupiter Opposition"),
    ("uranus", "square"): ("Quadratura de Urano", "Uranus Square"),
    ("uranus", "opposition"): ("Oposição de Urano (meia-vida)", "Uranus Opposition (midlife)"),
    ("uranus", "conjunction"): ("Retorno de Urano", "Uranus Return"),
    ("neptune", "square"): ("Quadratura de Netuno", "Neptune Square"),
    ("neptune", "opposition"): ("Oposição de Netuno", "Neptune Opposition"),
    ("pluto", "square"): ("Quadratura de Plutão", "Pluto Square"),
    ("pluto", "opposition"): ("Oposição de Plutão", "Pluto Opposition"),
    ("chiron", "conjunction"): ("Retorno de Quíron", "Chiron Return"),
    ("chiron", "square"): ("Quadratura de Quíron", "Chiron Square"),
    ("chiron", "opposition"): ("Oposição de Quíron", "Chiron Opposition"),
    ("mean_node", "conjunction"): ("Retorno Nodal", "Nodal Return"),
    ("mean_node", "opposition"): ("Retorno Nodal Inverso", "Inverse Nodal Return"),
    ("sun", "conjunction"): ("Retorno Solar (aniversário)", "Solar Return (birthday)"),
    ("mars", "conjunction"): ("Retorno de Marte", "Mars Return"),
}


def label_cycles(windows: List[Dict[str, Any]], lang: str = "pt") -> List[Dict[str, Any]]:
    """Marca `cycle_label`/`cycle_key`/`cycle_number` nas janelas que são ciclos de vida; devolve lista dos ciclos."""
    cycles: List[Dict[str, Any]] = []
    for w in windows:
        body = w["transit_body"]
        if SAME_BODY.get(body) != w["natal_point"]:
            w["cycle_key"] = None
            w["cycle_label"] = None
            continue
        key = (body, w["aspect"])
        labels = CYCLE_LABELS.get(key)
        if not labels:
            w["cycle_key"] = None
            w["cycle_label"] = None
            continue
        label = labels[1] if lang == "en" else labels[0]
        period = PERIOD_YEARS.get(body, 0.0)
        ref_age = w["hits"][0]["age"] if w["hits"] else (w["age_start"] + w["age_end"]) / 2.0
        number = None
        if w["aspect"] == "conjunction" and period > 0:
            number = int(round(ref_age / period))
            if number >= 1 and body not in ("sun", "mercury", "venus"):
                label = f"{label} #{number}"
        phase = None
        if w["aspect"] == "square":
            phase = ("crescente" if lang == "pt" else "waxing") if w.get("waxing") else ("decrescente" if lang == "pt" else "waning")
            label = f"{label} ({phase})"
        w["cycle_key"] = f"{body}_{w['aspect']}"
        w["cycle_label"] = label
        w["cycle_number"] = number
        cycles.append({
            "id": w["id"], "key": w["cycle_key"], "label": label, "body": body, "aspect": w["aspect"],
            "symbol": w["transit_symbol"], "aspect_symbol": w["aspect_symbol"], "number": number, "phase": phase,
            "start": w["start"], "end": w["end"], "hits": w["hits"], "n_passes": w["n_passes"],
            "age": round(ref_age, 1),
        })
    cycles.sort(key=lambda c: c["start"])
    return cycles
