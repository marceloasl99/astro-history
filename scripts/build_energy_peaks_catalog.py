"""
Script de Compilação do Catálogo de Picos de Energia Cósmica (2026–2060).
Varre a linha do tempo mundial e os mapas natais dos principais países soberanos,
extraindo apenas os PICOS DE ENERGIA (ativações críticas e altas), categorizando
por cenário temático e ordenando em sequência cronológica rigorosa.
"""

import json
import os
import math
from typing import Dict, List, Any

from src.mundane.countries_data import load_countries_data, get_country_by_iso
from src.mundane.transits_engine import calculate_country_chart, calculate_transits_for_date
from src.mundane.energy_peaks import classify_transit_recurrence_theme, ENERGY_CATEGORIES
from src.mundane.historical_analyzer import get_country_analyzed_history

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUTPUT_FILE = os.path.join(BASE_DIR, "data", "energy_peaks_2026_2060.json")
TIMELINE_FILE = os.path.join(BASE_DIR, "data", "timeline_1800_2100.json")

KEY_COUNTRIES = [
    {"iso": "USA", "name_pt": "Estados Unidos", "name_en": "United States", "flag": "🇺🇸"},
    {"iso": "BRA", "name_pt": "Brasil", "name_en": "Brazil", "flag": "🇧🇷"},
    {"iso": "CHN", "name_pt": "China", "name_en": "China", "flag": "🇨🇳"},
    {"iso": "RUS", "name_pt": "Rússia", "name_en": "Russia", "flag": "🇷🇺"},
    {"iso": "ISR", "name_pt": "Israel", "name_en": "Israel", "flag": "🇮🇱"},
    {"iso": "IRN", "name_pt": "Irã", "name_en": "Iran", "flag": "🇮🇷"},
    {"iso": "GBR", "name_pt": "Reino Unido", "name_en": "United Kingdom", "flag": "🇬🇧"},
    {"iso": "FRA", "name_pt": "França", "name_en": "France", "flag": "🇫🇷"},
    {"iso": "DEU", "name_pt": "Alemanha", "name_en": "Germany", "flag": "🇩🇪"},
    {"iso": "UKR", "name_pt": "Ucrânia", "name_en": "Ukraine", "flag": "🇺🇦"},
    {"iso": "JPN", "name_pt": "Japão", "name_en": "Japan", "flag": "🇯🇵"},
    {"iso": "IND", "name_pt": "Índia", "name_en": "India", "flag": "🇮🇳"}
]

SCENARIO_META = {
    "WAR_CONFLICT": {
        "label_pt": "Guerra & Conflito Militar",
        "label_en": "War & Military Conflict",
        "icon": "⚔️",
        "color": "rose",
        "badge_class": "bg-rose-500/20 text-rose-300 border-rose-500/40"
    },
    "ECONOMIC_CRASH": {
        "label_pt": "Quebra Econômica & Crise Financeira",
        "label_en": "Economic Crash & Financial Crisis",
        "icon": "📉",
        "color": "amber",
        "badge_class": "bg-amber-500/20 text-amber-300 border-amber-500/40"
    },
    "REGIME_CRISIS": {
        "label_pt": "Crise Institucional & Ruptura de Poder",
        "label_en": "Institutional Crisis & Regime Shift",
        "icon": "🏛️",
        "color": "purple",
        "badge_class": "bg-purple-500/20 text-purple-300 border-purple-500/40"
    },
    "SOCIAL_UPHEAVAL": {
        "label_pt": "Comoção Social & Movimentos Coletivos",
        "label_en": "Social Upheaval & Mass Movements",
        "icon": "🌊",
        "color": "sky",
        "badge_class": "bg-sky-500/20 text-sky-300 border-sky-500/40"
    },
    "TECH_INNOVATION": {
        "label_pt": "Salto Tecnológico & Fronteira Espacial",
        "label_en": "Tech Leap & Space Frontier",
        "icon": "🚀",
        "color": "emerald",
        "badge_class": "bg-emerald-500/20 text-emerald-300 border-emerald-500/40"
    }
}

def get_decade(year: int) -> str:
    if year < 2030:
        return "2020s"
    elif year < 2040:
        return "2030s"
    elif year < 2050:
        return "2040s"
    else:
        return "2050s"

def extract_world_peaks() -> List[Dict[str, Any]]:
    """Extrai os grandes picos de tensão mundial da timeline 1800-2100 para o horizonte 2026-2060."""
    if not os.path.exists(TIMELINE_FILE):
        return []

    with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
        timeline_data = json.load(f)

    world_peaks = []
    for item in timeline_data.get("timeline", []):
        year = item.get("year", 0)
        if not (2026 <= year <= 2060):
            continue

        peak_score = float(item.get("peak_tension_1000", 0.0))
        avg_score = float(item.get("annual_percentile_1000", 0.0))

        # Seleciona apenas anos com pico de energia expressivo (Top tiers)
        if peak_score < 960.0 and avg_score < 550.0:
            continue

        # Determina o cenário predominante com base nos sub-índices
        c_risk = float(item.get("conflict_risk_index_1000", 0.0))
        cr_risk = float(item.get("crisis_risk_index_1000", 0.0))
        t_risk = float(item.get("tech_innovation_index_1000", 0.0))
        s_risk = float(item.get("social_transformation_index_1000", 0.0))

        # Cenário de maior ativação
        scenarios_scores = [
            ("WAR_CONFLICT", c_risk),
            ("ECONOMIC_CRASH", cr_risk),
            ("TECH_INNOVATION", t_risk),
            ("SOCIAL_UPHEAVAL", s_risk)
        ]
        best_scenario, best_val = max(scenarios_scores, key=lambda x: x[1])

        # Se houver forte quadratura planetária ou saturno/plutão, prioriza conflito ou crise
        trigger = item.get("cosmic_trigger", "")
        if "♄" in trigger and "♇" in trigger:
            best_scenario = "REGIME_CRISIS"
        elif "♅" in trigger and "Gêmeos" in trigger and t_risk > 500:
            best_scenario = "TECH_INNOVATION"

        meta = SCENARIO_META[best_scenario]
        top_match = item.get("top_matches", [{}])[0] if item.get("top_matches") else {}
        precedent_title = top_match.get("title", "Alinhamento Cíclico Histórico")
        precedent_year = top_match.get("year", "Passado")

        world_peaks.append({
            "id": f"world_{year}_{best_scenario}",
            "year": year,
            "scope_type": "world",
            "country_iso": None,
            "country_name_pt": "Global / Mundial",
            "country_name_en": "Global / Worldwide",
            "country_flag": "🌐",
            "scenario_key": best_scenario,
            "scenario_label_pt": meta["label_pt"],
            "scenario_label_en": meta["label_en"],
            "scenario_icon": meta["icon"],
            "scenario_color": meta["color"],
            "badge_class": meta["badge_class"],
            "energy_score_1000": round(peak_score, 1),
            "alert_level": "Crítico" if peak_score >= 980 else "Alto",
            "peak_date": item.get("peak_date", f"{year}-06-21"),
            "cosmic_signature": trigger[:80] + ("..." if len(trigger) > 80 else ""),
            "cosmic_signature_detail": trigger,
            "historical_precedent_title": f"{precedent_title} ({precedent_year})",
            "historical_precedent_year": precedent_year,
            "historical_precedent_summary": f"Na base de dados de 1.342 fatos, momentos com geometria isomórfica registraram: {top_match.get('category', 'Marcos Globais')} ({precedent_year}).",
            "prospective_synthesis": f"Pico global da era ({peak_score}/1000). A convergência astronômica de {year} pressiona o cenário '{meta['label_pt']}', mobilizando coordenação internacional e governança multilíngue.",
            "decade": get_decade(year)
        })

    return world_peaks

def extract_country_peaks() -> List[Dict[str, Any]]:
    """Extrai os picos de energia nos mapas natais dos países prioritários entre 2026 e 2060."""
    country_peaks = []

    for c_info in KEY_COUNTRIES:
        iso = c_info["iso"]
        c_record = get_country_by_iso(iso)
        if not c_record:
            continue

        chart = calculate_country_chart(c_record)
        analyzed_history = get_country_analyzed_history(chart)

        # Varre ano a ano (2026 a 2060)
        # Amostra no dia 1 de julho para medir a ativação de planetas lentos
        yearly_activations = []
        for yr in range(2026, 2061):
            t_res = calculate_transits_for_date(chart, f"{yr}-07-01")
            score = t_res["activation_index_1000"]
            slow_transits = [t for t in t_res.get("transits", []) if t["transit_planet_id"] in ["pluto", "neptune", "uranus", "saturn", "jupiter", "mars"]]
            yearly_activations.append((yr, score, t_res, slow_transits))

        # Encontra picos locais ou anos com score >= 740
        for i, (yr, score, t_res, slow_transits) in enumerate(yearly_activations):
            # Critério de pico: score >= 750 OU (score >= 700 e maior que o ano anterior e posterior)
            prev_score = yearly_activations[i-1][1] if i > 0 else 0
            next_score = yearly_activations[i+1][1] if i < len(yearly_activations) - 1 else 0

            is_local_peak = (score >= 720 and score >= prev_score and score >= next_score)
            is_critical = (score >= 780)

            if not (is_local_peak or is_critical):
                continue

            if not slow_transits:
                continue

            top_t = slow_transits[0]
            cat_key = classify_transit_recurrence_theme(
                top_t["transit_planet_id"],
                top_t["natal_planet_id"],
                top_t["aspect_nature"]
            )
            meta = SCENARIO_META.get(cat_key, SCENARIO_META["WAR_CONFLICT"])

            # Busca fato análogo no histórico do país
            matched_hist = None
            for h in analyzed_history:
                if any(t["transit_planet_id"] == top_t["transit_planet_id"] for t in h.get("top_transits", [])):
                    matched_hist = h
                    break
            if not matched_hist and analyzed_history:
                matched_hist = analyzed_history[0]

            prec_title = f"{matched_hist['title']} ({matched_hist['date'][:4]})" if matched_hist else "Ciclo Arquetípico Nacional"
            prec_year = matched_hist["date"][:4] if matched_hist else "Passado"
            prec_summary = matched_hist.get("description", "Momento de transição de poder ou estresse territorial registrado no passado.") if matched_hist else ""

            headline = f"{top_t['transit_symbol']} {top_t['transit_planet']} {top_t['aspect_symbol']} {top_t['natal_planet']} natal ({top_t['formatted_orb']})"
            detail = f"{top_t['transit_planet']} em trânsito forma {top_t['aspect_name']} com {top_t['natal_planet']} na carta de fundação do país."

            country_peaks.append({
                "id": f"{iso.lower()}_{yr}_{cat_key}",
                "year": yr,
                "scope_type": "country",
                "country_iso": iso,
                "country_name_pt": c_info["name_pt"],
                "country_name_en": c_info["name_en"],
                "country_flag": c_info["flag"],
                "scenario_key": cat_key,
                "scenario_label_pt": meta["label_pt"],
                "scenario_label_en": meta["label_en"],
                "scenario_icon": meta["icon"],
                "scenario_color": meta["color"],
                "badge_class": meta["badge_class"],
                "energy_score_1000": score,
                "alert_level": "Crítico" if score >= 800 else "Alto",
                "peak_date": f"{yr}-07-01",
                "cosmic_signature": headline,
                "cosmic_signature_detail": detail,
                "historical_precedent_title": prec_title,
                "historical_precedent_year": prec_year,
                "historical_precedent_summary": prec_summary[:160] + ("..." if len(prec_summary) > 160 else ""),
                "prospective_synthesis": f"Pico de energia no mapa de {c_info['name_pt']} ({score}/1000). A passagem de {top_t['transit_planet']} tensiona o eixo de {meta['label_pt']}, exigindo prontidão estratégica governamental.",
                "decade": get_decade(yr)
            })

    return country_peaks

def build_full_peaks_catalog():
    print("Extraindo picos mundiais (2026–2060)...")
    world_peaks = extract_world_peaks()
    print(f"Picos mundiais extraídos: {len(world_peaks)}")

    print("Extraindo picos por país (2026–2060)...")
    country_peaks = extract_country_peaks()
    print(f"Picos por país extraídos: {len(country_peaks)}")

    # Unifica e ordena em estrita sequência cronológica: year ASC, depois score DESC
    all_peaks = world_peaks + country_peaks
    all_peaks.sort(key=lambda x: (x["year"], -x["energy_score_1000"]))

    # Estatísticas
    kpis = {
        "total_peaks": len(all_peaks),
        "world_peaks_count": len(world_peaks),
        "country_peaks_count": len(country_peaks),
        "start_year": 2026,
        "end_year": 2060,
        "critical_count": sum(1 for p in all_peaks if p["alert_level"] == "Crítico"),
        "high_count": sum(1 for p in all_peaks if p["alert_level"] == "Alto"),
        "by_scenario": {
            s: sum(1 for p in all_peaks if p["scenario_key"] == s)
            for s in SCENARIO_META
        },
        "by_decade": {
            "2020s": sum(1 for p in all_peaks if p["decade"] == "2020s"),
            "2030s": sum(1 for p in all_peaks if p["decade"] == "2030s"),
            "2040s": sum(1 for p in all_peaks if p["decade"] == "2040s"),
            "2050s": sum(1 for p in all_peaks if p["decade"] == "2050s"),
        }
    }

    result = {
        "generated_at": "2026-11-02T02:20:00Z",
        "horizon": "2026–2060",
        "kpis": kpis,
        "scenario_meta": SCENARIO_META,
        "countries_meta": KEY_COUNTRIES,
        "peaks": all_peaks
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Catálogo de Picos de Energia salvo com sucesso em: {OUTPUT_FILE}")
    print(f"Total de Picos Catalogados: {len(all_peaks)} (Mundiais: {len(world_peaks)}, Países: {len(country_peaks)})")

if __name__ == "__main__":
    build_full_peaks_catalog()
