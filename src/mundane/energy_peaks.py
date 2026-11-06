"""
Motor de Detecção de Picos de Energia Astrológica & Tendências Cíclicas Recorrentes (2026–2050).
Varre a linha do tempo futura, identifica picos de ativação da nação e classifica
em tendências temáticas que tendem a se manifestar novamente:
- ⚔️ Guerra / Conflito Militar / Tensão Territorial
- 📉 Quebra Econômica / Colapso Financeiro / Crise Cambial
- 🏛️ Crise Institucional / Ruptura de Poder / Golpe de Estado
- 🌊 Comoção Social / Movimentos de Massa / Choque Coletivo
"""

import json
import os
from typing import Dict, List, Any, Optional
from src.mundane.transits_engine import calculate_transits_for_date
from src.mundane.historical_analyzer import get_country_analyzed_history

PEAKS_CATALOG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "energy_peaks_2026_2060.json"))

def load_energy_peaks_catalog() -> Dict[str, Any]:
    """Carrega o catálogo completo de picos de energia 2026–2060 com cache em memória."""
    if os.path.exists(PEAKS_CATALOG_FILE):
        try:
            with open(PEAKS_CATALOG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"peaks": [], "kpis": {}, "scenario_meta": ENERGY_CATEGORIES, "countries_meta": []}


def _load_energy_categories():
    """v6: 8 categorias estimáveis de config/categories.yaml (compatível com o dicionário legado de 4)."""
    import yaml
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "config", "categories.yaml"))
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
    except Exception:
        cfg = {"categories": {}, "order": []}
    out = {}
    for key in cfg.get("order", []) or cfg.get("categories", {}).keys():
        c = cfg["categories"][key]
        out[key] = {
            "label": c["label_pt"], "label_en": c.get("label_en", c["label_pt"]), "short_label": c["short_pt"],
            "short_label_en": c.get("short_en", c["short_pt"]), "icon": c["icon"], "theme_color": c["theme_color"],
            "border_class": c["border_class"], "bg_badge": c["bg_badge"], "description": c["description_pt"],
            "hindcast_targets": c.get("hindcast_targets", []), "skeptical_control": bool(c.get("skeptical_control", False)),
        }
    return out


ENERGY_CATEGORIES = _load_energy_categories()
LEGACY_CATEGORY_KEYS = ["WAR_CONFLICT", "ECONOMIC_CRASH", "REGIME_CRISIS", "SOCIAL_UPHEAVAL"]

def classify_transit_recurrence_theme(transit_planet_id: str, natal_planet_id: str, aspect_nature: str) -> str:
    """Classifica um aspecto de trânsito em uma das 4 categorias de eventos históricos recorrentes."""
    t_id = transit_planet_id.lower()
    n_id = natal_planet_id.lower()
    nature = (aspect_nature or "").lower()
    harmonious = nature in ("fluido", "harmonico", "harmônico", "harmonioso", "flowing")

    # 0. v6 — categorias construtivas e controles (regras explícitas e auditáveis; ver config/categories.yaml)
    if harmonious and t_id in ("jupiter", "venus") and n_id in ("sun", "venus", "jupiter", "moon"):
        return "DIPLOMACY_PEACE"
    if harmonious and t_id in ("uranus", "mercury", "jupiter") and n_id in ("mercury", "uranus"):
        return "SCIENCE_INNOVATION"
    if t_id in ("neptune", "chiron") and n_id in ("moon", "mercury", "chiron") and not harmonious:
        return "HEALTH_EPIDEMIC"
    if t_id == "uranus" and n_id == "saturn" and not harmonious:
        return "NATURAL_DISASTER"  # controle cético: ruptura de estrutura; não há mecanismo plausível

    # 1. Risco de Conflito Militar / Guerra
    if n_id == "mars" or t_id == "mars":
        return "WAR_CONFLICT"
    if (t_id in ["pluto", "uranus"]) and (n_id in ["mars", "north_node"]):
        return "WAR_CONFLICT"

    # 2. Risco de Quebra Econômica / Crise Financeira
    if n_id in ["jupiter", "venus"] and t_id in ["saturn", "pluto", "uranus", "neptune"]:
        return "ECONOMIC_CRASH"
    if t_id == "saturn" and n_id == "jupiter":
        return "ECONOMIC_CRASH"

    # 3. Risco de Crise Institucional / Poder / Governo
    if n_id == "sun" or (n_id == "saturn" and t_id in ["uranus", "pluto"]):
        return "REGIME_CRISIS"
    if t_id == "uranus" and n_id in ["sun", "saturn"]:
        return "REGIME_CRISIS"

    # 4. Risco de Comoção Social / População
    if n_id in ["moon", "chiron"]:
        return "SOCIAL_UPHEAVAL"
    if t_id in ["neptune", "uranus"] and n_id == "moon":
        return "SOCIAL_UPHEAVAL"

    # Fallback conforme a natureza do aspecto
    if t_id in ["pluto", "uranus"]:
        return "REGIME_CRISIS"
    elif t_id == "saturn":
        return "ECONOMIC_CRASH"
    else:
        return "WAR_CONFLICT"

def detect_energy_peaks_and_recurrences(country_chart: Dict[str, Any], start_year: int = 2026, end_year: int = 2050) -> List[Dict[str, Any]]:
    """
    Varre os anos futuros, detecta os grandes picos de ativação cósmica e associa diretamente
    a precedentes históricos passados do país, indicando o que tende a acontecer novamente.
    """
    country_history = get_country_analyzed_history(country_chart)
    peaks_detected = []

    # Amostragem bienal/estratégica cobrindo os grandes ciclos de 2026 a 2050
    windows = [
        {"range": "2026–2027", "date": "2026-07-01", "era_label": "Ingresso de Saturno e Netuno em Áries (Ponto Vernal 0°)"},
        {"range": "2028–2030", "date": "2029-01-01", "era_label": "Urano em Gêmeos & Avanço de Plutão em Aquário"},
        {"range": "2031–2033", "date": "2032-07-01", "era_label": "Saturno em Touro e aspectos nos signos fixos"},
        {"range": "2035–2037", "date": "2036-01-01", "era_label": "Grandes ciclos sociais de Júpiter e Saturno no Ar"},
        {"range": "2039–2041", "date": "2040-07-01", "era_label": "Clímax da Era de Plutão em Aquário e redefinições globais"}
    ]

    for win in windows:
        t_res = calculate_transits_for_date(country_chart, win["date"])
        transits = t_res.get("transits", [])
        score_1000 = t_res.get("activation_index_1000", 300)

        # Filtra trânsitos de planetas de grande impacto
        slow_transits = [t for t in transits if t["transit_planet_id"] in ["pluto", "neptune", "uranus", "saturn", "jupiter", "mars"]]
        if not slow_transits:
            continue

        # Seleciona o trânsito protagonista de maior tensão/impacto
        protagonist = slow_transits[0]
        cat_key = classify_transit_recurrence_theme(
            protagonist["transit_planet_id"],
            protagonist["natal_planet_id"],
            protagonist["aspect_nature"]
        )
        cat_meta = ENERGY_CATEGORIES.get(cat_key, ENERGY_CATEGORIES["WAR_CONFLICT"])

        # Procura nos fatos históricos passados do país um evento similar da mesma categoria
        matched_event = None
        for h in country_history:
            # Primeiro tenta casar pela mesma categoria ou pelo mesmo par de planetas
            h_cat = h.get("category", "")
            is_same_cat = False
            if cat_key == "WAR_CONFLICT" and "Guerra" in h_cat:
                is_same_cat = True
            elif cat_key == "ECONOMIC_CRASH" and "Crise Financeira" in h_cat:
                is_same_cat = True
            elif cat_key == "REGIME_CRISIS" and ("Revolução" in h_cat or "Golpe" in h_cat):
                is_same_cat = True
            elif cat_key == "SOCIAL_UPHEAVAL" and ("Conflito Interno" in h_cat or "Social" in h_cat):
                is_same_cat = True

            # Ou se o planeta em trânsito era o mesmo
            has_same_transit = any(t["transit_planet_id"] == protagonist["transit_planet_id"] for t in h.get("top_transits", []))

            if is_same_cat or has_same_transit:
                matched_event = h
                break

        # Se não achou na busca estrita, pega o evento histórico de maior score do país
        if not matched_event and country_history:
            matched_event = max(country_history, key=lambda x: x.get("activation_index_1000", 0))

        # Síntese: O que aconteceu no passado vs O que tende a acontecer novamente
        if matched_event:
            past_summary = (
                f"Em {matched_event['date'][:4]}, durante o evento '{matched_event['title']}' ({matched_event['category']}), "
                f"quando {matched_event['protagonist_headline']}, o país enfrentou: {matched_event['description']}"
            )
            future_tendency = (
                f"A repetição desse nível de energia na janela {win['range']} aponta para uma reativação cíclica no tema '{cat_meta['label']}'. "
                f"Tendência: Sob a passagem de {protagonist['transit_symbol']} {protagonist['transit_planet']} em {protagonist['aspect_name']} com {protagonist['natal_symbol']} {protagonist['natal_planet']} natal, "
                f"a nação tende a reviver demandas de rigor em {cat_meta['short_label'].lower()}, exigindo planejamento estratégico para conter choques e salvaguardar a estabilidade."
            )
            precedent_title = f"{matched_event['title']} ({matched_event['date'][:4]})"
            precedent_date = matched_event["date"]
        else:
            past_summary = f"Momento de tensão histórica máxima em ciclos anteriores envolvendo {protagonist['transit_planet']} e {protagonist['natal_planet']}."
            future_tendency = (
                f"A janela {win['range']} concentra alta pressão cósmica. Sob {protagonist['transit_planet']} {protagonist['aspect_name']} {protagonist['natal_planet']}, "
                f"há tendência de pico em '{cat_meta['label']}', demandando prontidão em segurança, governabilidade e equilíbrio financeiro."
            )
            precedent_title = f"Ciclo Histórico Arquetípico ({cat_meta['short_label']})"
            precedent_date = "Passado Histórico"

        peaks_detected.append({
            "window_range": win["range"],
            "sample_date": win["date"],
            "era_label": win["era_label"],
            "activation_index_1000": score_1000,
            "category_key": cat_key,
            "category_label": cat_meta["label"],
            "category_short": cat_meta["short_label"],
            "icon": cat_meta["icon"],
            "badge_class": cat_meta["bg_badge"],
            "border_class": cat_meta["border_class"],
            "protagonist_transit": {
                "transit_planet": protagonist["transit_planet"],
                "transit_symbol": protagonist["transit_symbol"],
                "aspect_name": protagonist["aspect_name"],
                "aspect_symbol": protagonist["aspect_symbol"],
                "aspect_nature": protagonist["aspect_nature"],
                "natal_planet": protagonist["natal_planet"],
                "natal_symbol": protagonist["natal_symbol"],
                "formatted_orb": protagonist["formatted_orb"],
                "is_exact": protagonist["is_exact"]
            },
            "precedent_title": precedent_title,
            "precedent_date": precedent_date,
            "past_manifestation": past_summary,
            "future_recurrence_tendency": future_tendency
        })

    return peaks_detected
