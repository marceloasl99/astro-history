"""
Motor de Cálculo Astrológico Mundano de Países e Trânsitos Planetários.
Baseado no Swiss Ephemeris (pyswisseph).
Versão Canônica:
- Cada país tem exatamente um mapa natal oficial.
- Se o horário for desconhecido (regra padrão), o mapa é calculado SEM casas (Carta Solar / Zodíaco Natural).
- Cálculo exato de trânsitos históricos e futuros (aspectos maiores, orbes, aplicando/separando, interpretações mundanas).
"""

import math
import os
from typing import Dict, List, Optional, Tuple, Any
from datetime import date, datetime
import swisseph as swe

from src.astro_engine import (
    degree_to_sign_info,
    resolve_event_instant,
    calculate_houses,
    ZODIAC_SIGNS
)
from src.core.scoring import aspect_definitions

# Caminhos de efemérides
from src.core.ephemeris import ensure_ephe_path
ensure_ephe_path()

# Corpos celestes considerados na Astrologia Mundana
MUNDANE_BODIES = [
    {"id": "sun", "name": "Sol", "symbol": "☉", "swe_id": swe.SUN, "weight": 2.5, "mundane_role": "Chefe de Estado, soberania, autoridade máxima e prestígio internacional"},
    {"id": "moon", "name": "Lua", "symbol": "☽", "swe_id": swe.MOON, "weight": 2.0, "mundane_role": "População em geral, o povo, humor social e opinião pública"},
    {"id": "mercury", "name": "Mercúrio", "symbol": "☿", "swe_id": swe.MERCURY, "weight": 1.2, "mundane_role": "Comércio interno, comunicações, imprensa, transportes e acordos"},
    {"id": "venus", "name": "Vênus", "symbol": "♀", "swe_id": swe.VENUS, "weight": 1.3, "mundane_role": "Recursos financeiros, paz, artes, alianças e relações exteriores"},
    {"id": "mars", "name": "Marte", "symbol": "♂", "swe_id": swe.MARS, "weight": 2.0, "mundane_role": "Forças Armadas, conflitos, segurança nacional e agressividade coletiva"},
    {"id": "jupiter", "name": "Júpiter", "symbol": "♃", "swe_id": swe.JUPITER, "weight": 1.8, "mundane_role": "Poder judiciário, expansão econômica, prosperidade e tratados"},
    {"id": "saturn", "name": "Saturno", "symbol": "♄", "swe_id": swe.SATURN, "weight": 2.2, "mundane_role": "Instituições do Estado, leis consolidadas, austeridade e ordem pública"},
    {"id": "uranus", "name": "Urano", "symbol": "♅", "swe_id": swe.URANUS, "weight": 2.4, "mundane_role": "Rupturas políticas, inovações tecnológicas, revoltas e golpes"},
    {"id": "neptune", "name": "Netuno", "symbol": "♆", "swe_id": swe.NEPTUNE, "weight": 2.2, "mundane_role": "Ideologias coletivas, crises de identidade, escândalos e ilusões"},
    {"id": "pluto", "name": "Plutão", "symbol": "♇", "swe_id": swe.PLUTO, "weight": 2.8, "mundane_role": "Poder profundo, transformação estrutural, crises de soberania e reconstrução"},
    {"id": "north_node", "name": "Nodo Norte", "symbol": "☊", "swe_id": swe.TRUE_NODE, "weight": 1.0, "mundane_role": "Destino coletivo e vetor de desenvolvimento histórico"},
    {"id": "chiron", "name": "Quíron", "symbol": "⚷", "swe_id": swe.CHIRON, "weight": 1.0, "mundane_role": "Feridas históricas não cicatrizadas e processos de reparação"}
]

# Aspectos Maiores de Trânsito
TRANSIT_ASPECTS = [
    {"name": "Conjunção", "symbol": "☌", "angle": 0.0, "max_orb": 2.5, "base_nature": "foco"},
    {"name": "Oposição", "symbol": "☍", "angle": 180.0, "max_orb": 2.5, "base_nature": "tenso"},
    {"name": "Quadratura", "symbol": "□", "angle": 90.0, "max_orb": 2.5, "base_nature": "tenso"},
    {"name": "Trígono", "symbol": "△", "angle": 120.0, "max_orb": 2.5, "base_nature": "fluido"},
    {"name": "Sextil", "symbol": "⚹", "angle": 60.0, "max_orb": 2.0, "base_nature": "fluido"}
]


# Cache em memória para cartas natais dos países
_NATAL_CHARTS_CACHE: Dict[str, Dict[str, Any]] = {}

def calculate_country_chart(country: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula o mapa natal canônico de fundação de um país.
    Se country['is_time_known'] for False, o cálculo é estritamente SEM CASAS
    (Carta Solar/Zodíaco Natural), conforme solicitado.
    """
    ensure_ephe_path()
    iso = country.get("iso_code", "").upper()
    if iso in _NATAL_CHARTS_CACHE:
        return _NATAL_CHARTS_CACHE[iso]

    date_str = country.get("date", "1900-01-01")
    time_str = country.get("time", "desconhecido")
    is_time_known = country.get("is_time_known", False)
    lat = float(country.get("latitude", 0.0))
    lon = float(country.get("longitude", 0.0))

    instant = resolve_event_instant(
        date_str=date_str,
        time_str=time_str if is_time_known else "desconhecido",
        longitude=lon,
        latitude=lat
    )
    tjd_ut = instant["tjd_ut"]

    # Cálculo dos corpos planetários
    planets = []
    for b in MUNDANE_BODIES:
        try:
            # Tenta com efemérides suíças e fallback para Moshier
            try:
                res, _ = swe.calc_ut(tjd_ut, b["swe_id"], swe.FLG_SPEED)
            except Exception:
                res, _ = swe.calc_ut(tjd_ut, b["swe_id"], swe.FLG_MOSEPH | swe.FLG_SPEED)

            lon_deg = res[0] % 360.0
            lat_deg = res[1]
            dist = res[2]
            speed = res[3]
            is_retrograde = speed < 0.0

            sign_info = degree_to_sign_info(lon_deg)
            planets.append({
                "id": b["id"],
                "name": b["name"],
                "symbol": b["symbol"],
                "weight": b["weight"],
                "mundane_role": b["mundane_role"],
                "longitude": round(lon_deg, 4),
                "latitude": round(lat_deg, 4),
                "distance": round(dist, 5),
                "speed": round(speed, 5),
                "is_retrograde": is_retrograde,
                "sign_name": sign_info["sign_name"],
                "sign_symbol": sign_info["sign_symbol"],
                "sign_index": sign_info["sign_index"],
                "degree_in_sign": sign_info["degree_in_sign"],
                "formatted": sign_info["formatted"],
                "element": sign_info["element"],
                "modality": sign_info["modality"],
                "ruler": sign_info["ruler"]
            })
        except Exception:
            continue

    # Tratamento das Casas: rigorosamente sem casas se horário desconhecido
    houses_data = calculate_houses(tjd_ut, lat, lon, is_time_known=is_time_known)

    # Identificação de Sol e Lua para badges de destaque
    sun_info = next((p for p in planets if p["id"] == "sun"), None)
    moon_info = next((p for p in planets if p["id"] == "moon"), None)

    chart_result = {
        "country_iso": iso,
        "country_name_pt": country.get("name_pt"),
        "country_name_en": country.get("name_en"),
        "continent": country.get("continent"),
        "flag_emoji": country.get("flag_emoji"),
        "foundation_event": country.get("foundation_event"),
        "date": date_str,
        "time": time_str,
        "is_time_known": is_time_known,
        "tjd_ut": tjd_ut,
        "city": country.get("city"),
        "latitude": lat,
        "longitude": lon,
        "historical_justification": country.get("historical_justification"),
        "source_reference": country.get("source_reference"),
        "sun_sign": sun_info["sign_name"] if sun_info else "Desconhecido",
        "sun_symbol": sun_info["sign_symbol"] if sun_info else "",
        "moon_sign": moon_info["sign_name"] if moon_info else "Desconhecido",
        "moon_symbol": moon_info["sign_symbol"] if moon_info else "",
        "moon_uncertainty_note": "Atenção: como o horário exato da fundação é desconhecido, a Lua pode ter variado em até ~12° ao longo do dia; as posições do Sol e planetas são altamente precisas." if not is_time_known else None,
        "planets": planets,
        "houses": houses_data
    }

    _NATAL_CHARTS_CACHE[iso] = chart_result
    return chart_result

def get_angular_distance(deg1: float, deg2: float) -> float:
    """Retorna a menor distância angular na eclíptica (0° a 180°)."""
    diff = abs(deg1 - deg2) % 360.0
    if diff > 180.0:
        diff = 360.0 - diff
    return diff

def calculate_transits_for_date(country_chart: Dict[str, Any], target_date_str: str) -> Dict[str, Any]:
    """
    Calcula todos os trânsitos planetários ativos sobre a carta natal do país em uma data específica.
    Detecta aspectos maiores, orbes precisos, status aplicativo/separativo e interpretação mundana.
    """
    ensure_ephe_path()
    # Converte data de trânsito em Julian Day (ao meio-dia UT)
    instant = resolve_event_instant(date_str=target_date_str, time_str="12:00")
    transit_tjd = instant["tjd_ut"]

    # Posições dos planetas em trânsito no céu
    transit_bodies = []
    # No trânsito mundano, os planetas mais determinantes são Júpiter até Plutão, além de Marte (gatilho) e Sol/Lua
    transit_tracked_ids = ["pluto", "neptune", "uranus", "saturn", "jupiter", "mars", "sun", "north_node"]
    tracked_swe_map = {b["id"]: b for b in MUNDANE_BODIES if b["id"] in transit_tracked_ids}

    for b_id in transit_tracked_ids:
        b_def = tracked_swe_map[b_id]
        try:
            res, _ = swe.calc_ut(transit_tjd, b_def["swe_id"], swe.FLG_SPEED)
        except Exception:
            res, _ = swe.calc_ut(transit_tjd, b_def["swe_id"], swe.FLG_MOSEPH | swe.FLG_SPEED)
        lon_deg = res[0] % 360.0
        speed = res[3]
        sign_info = degree_to_sign_info(lon_deg)
        transit_bodies.append({
            "id": b_id,
            "name": b_def["name"],
            "symbol": b_def["symbol"],
            "weight": b_def["weight"],
            "longitude": round(lon_deg, 4),
            "speed": round(speed, 5),
            "is_retrograde": speed < 0.0,
            "sign_name": sign_info["sign_name"],
            "sign_symbol": sign_info["sign_symbol"],
            "formatted": sign_info["formatted"]
        })

    natal_planets_map = {p["id"]: p for p in country_chart["planets"]}
    active_transits = []

    # Comparar cada planeta em trânsito com os planetas natais da nação
    for t_planet in transit_bodies:
        for n_id, n_planet in natal_planets_map.items():
            # Não calcular Lua natal se horário desconhecido e aspecto depender de fração de grau
            if n_id == "moon" and not country_chart["is_time_known"]:
                # Inclui trânsito sobre a Lua com aviso de orbe elástico
                pass

            dist = get_angular_distance(t_planet["longitude"], n_planet["longitude"])

            for asp in TRANSIT_ASPECTS:
                angle = asp["angle"]
                max_orb = asp["max_orb"]
                diff = abs(dist - angle)

                if diff <= max_orb:
                    # Determinar se aspecto é aplicativo ou separativo
                    # Se o planeta em trânsito está se movendo em direção à exatidão
                    # Aproximação simples pela velocidade diária
                    dist_future = get_angular_distance(t_planet["longitude"] + t_planet["speed"], n_planet["longitude"])
                    diff_future = abs(dist_future - angle)
                    is_applying = diff_future < diff

                    # Classificação da natureza do aspecto
                    aspect_nature = asp["base_nature"]
                    if asp["name"] == "Conjunção":
                        if t_planet["id"] in ["pluto", "neptune", "uranus"]:
                            aspect_nature = "transformação profunda"
                        elif t_planet["id"] in ["saturn", "mars"]:
                            aspect_nature = "tenso"
                        elif t_planet["id"] in ["jupiter", "venus"]:
                            aspect_nature = "fluido"
                        else:
                            aspect_nature = "foco"

                    # Formatar orbe em graus e minutos
                    orb_deg = int(diff)
                    orb_min = int(round((diff - orb_deg) * 60))
                    formatted_orb = f"{orb_deg}°{orb_min:02d}'"

                    significance = generate_mundane_transit_meaning(
                        transit_body=t_planet,
                        natal_body=n_planet,
                        aspect_name=asp["name"],
                        aspect_nature=aspect_nature,
                        is_exact=diff < 1.0
                    )

                    # Peso de impacto mundano
                    impact_score = (t_planet["weight"] * 1.5 + n_planet["weight"]) * (1.0 - (diff / max_orb) * 0.5)
                    if aspect_nature in ["tenso", "transformação profunda"]:
                        impact_score *= 1.3

                    active_transits.append({
                        "transit_planet": t_planet["name"],
                        "transit_symbol": t_planet["symbol"],
                        "transit_planet_id": t_planet["id"],
                        "transit_longitude": t_planet["longitude"],
                        "transit_formatted": t_planet["formatted"],
                        "transit_retrograde": t_planet["is_retrograde"],
                        "aspect_name": asp["name"],
                        "aspect_symbol": asp["symbol"],
                        "aspect_nature": aspect_nature,
                        "natal_planet": n_planet["name"],
                        "natal_symbol": n_planet["symbol"],
                        "natal_planet_id": n_id,
                        "natal_longitude": n_planet["longitude"],
                        "natal_formatted": n_planet["formatted"],
                        "orb": round(diff, 3),
                        "formatted_orb": formatted_orb,
                        "is_exact": diff < 1.0,
                        "status": "Aplicando" if is_applying else "Separando",
                        "impact_score": round(impact_score, 2),
                        "significance": significance
                    })

    # Ordenar por relevância de impacto mundano (maior para menor)
    active_transits.sort(key=lambda x: (x["is_exact"] is False, -x["impact_score"]))

    # Calcular índice global de ativação na data (escala 0 a 1000)
    activation_index = calculate_transits_activation_score(active_transits)

    return {
        "country_iso": country_chart["country_iso"],
        "target_date": target_date_str,
        "transit_tjd": transit_tjd,
        "active_transits_count": len(active_transits),
        "activation_index_1000": activation_index,
        "transits": active_transits,
        "transit_bodies": transit_bodies
    }

def generate_mundane_transit_meaning(
    transit_body: Dict[str, Any],
    natal_body: Dict[str, Any],
    aspect_name: str,
    aspect_nature: str,
    is_exact: bool
) -> str:
    """Gera síntese interpretativa mundana contextualizada para o trânsito planetário."""
    t_name = transit_body["name"]
    n_name = natal_body["name"]
    role = natal_body.get("mundane_role", "")

    prefix = "Pico de ativação exata: " if is_exact else ""

    if aspect_nature == "tenso":
        if transit_body["id"] == "pluto":
            return f"{prefix}Crise estrutural e expurgo de poder sobre {n_name} natal ({role}). Exigência de transformação profunda ou ruptura com modelos arcaicos."
        elif transit_body["id"] == "saturn":
            return f"{prefix}Teste de limites, austeridade, freio institucional ou sobrecarga sobre {n_name} natal ({role}). Período de prestação de contas históricas."
        elif transit_body["id"] == "uranus":
            return f"{prefix}Instabilidade repentina, choque imprevisto ou impulsos rebeldes afetando {n_name} natal ({role}). Desestabilização do status quo."
        elif transit_body["id"] == "neptune":
            return f"{prefix}Desilusão coletiva, perda de clareza, escândalos ou dissolução afetando {n_name} natal ({role})."
        elif transit_body["id"] == "mars":
            return f"{prefix}Gatilho imediato de tensão, agressividade pública, conflito ou resposta enérgica sobre {n_name} natal ({role})."
        else:
            return f"{prefix}Atrito dinâmico e divergência de interesses ativando {n_name} natal ({role})."
    elif aspect_nature == "transformação profunda":
        return f"{prefix}Renascimento e reinvenção irreversível de {n_name} natal ({role}). Consolidação de um novo capítulo histórico para a nação."
    else: # fluido / harmonia
        if transit_body["id"] == "jupiter":
            return f"{prefix}Janela favorável de expansão, crescimento econômico, prestígio internacional e alianças estratégicas ativando {n_name} natal ({role})."
        elif transit_body["id"] == "uranus":
            return f"{prefix}Avanço tecnológico, reformas progressistas e modernização construtiva harmonizando com {n_name} natal ({role})."
        elif transit_body["id"] == "saturn":
            return f"{prefix}Consolidação legal duradoura, estabilização institucional e maturidade de Estado fortalecendo {n_name} natal ({role})."
        else:
            return f"{prefix}Harmonia e fluidez nas deliberações nacionais associadas a {n_name} natal ({role})."

def calculate_transits_activation_score(transits: List[Dict[str, Any]]) -> int:
    """Calcula um score calibrado de 0 a 1000 da intensidade dos trânsitos sobre a carta da nação."""
    if not transits:
        return 150

    raw_sum = 0.0
    for t in transits:
        raw_sum += t["impact_score"]

    # Calibração sigmoid-like para escala 0 a 1000
    # Média típica de trânsitos importantes dá soma entre 15 e 60
    score = int(round(1000.0 * (1.0 - math.exp(-raw_sum / 38.0))))
    return max(50, min(995, score))

CATEGORY_METADATA = {
    "WAR_CONFLICT": {
        "label": "Guerra & Conflito Militar",
        "short_label": "Guerra / Conflito",
        "icon": "⚔️",
        "color": "#f43f5e",
        "bg": "rgba(244, 63, 94, 0.15)",
        "border": "rgba(244, 63, 94, 0.5)"
    },
    "ECONOMIC_CRASH": {
        "label": "Quebra Econômica & Crise Fiscal",
        "short_label": "Quebra Econômica",
        "icon": "📉",
        "color": "#f59e0b",
        "bg": "rgba(245, 158, 11, 0.15)",
        "border": "rgba(245, 158, 11, 0.5)"
    },
    "REGIME_CRISIS": {
        "label": "Crise Institucional & Ruptura de Poder",
        "short_label": "Crise de Poder",
        "icon": "🏛️",
        "color": "#a855f7",
        "bg": "rgba(168, 85, 247, 0.15)",
        "border": "rgba(168, 85, 247, 0.5)"
    },
    "SOCIAL_UPHEAVAL": {
        "label": "Comoção Social & Movimentos de Massa",
        "short_label": "Comoção Social",
        "icon": "🌊",
        "color": "#38bdf8",
        "bg": "rgba(56, 189, 248, 0.15)",
        "border": "rgba(56, 189, 248, 0.5)"
    }
}

def calculate_activation_timeline(
    country_chart: Dict[str, Any],
    start_year: int = 1800,
    end_year: int = 2060
) -> Dict[str, Any]:
    """
    Gera a série temporal de ativação de trânsitos (1800 a 2060) para o gráfico da nação,
    decomposta por categorias temáticas (Guerra, Economia, Regime e Comoção Social)
    e com demarcação entre Histórico (Passado) e Futuro.
    """
    from src.mundane.energy_peaks import classify_transit_recurrence_theme, detect_energy_peaks_and_recurrences
    from src.mundane.historical_analyzer import get_country_analyzed_history

    years = []
    scores = []
    cat_series = {
        "WAR_CONFLICT": [],
        "ECONOMIC_CRASH": [],
        "REGIME_CRISIS": [],
        "SOCIAL_UPHEAVAL": []
    }
    major_transits_summary = []

    for yr in range(start_year, end_year + 1):
        sample_date = f"{yr:04d}-07-01"
        res = calculate_transits_for_date(country_chart, sample_date)
        years.append(yr)
        scores.append(res["activation_index_1000"])

        # Decomposição categórica por aspecto
        cat_sums = {
            "WAR_CONFLICT": 0.0,
            "ECONOMIC_CRASH": 0.0,
            "REGIME_CRISIS": 0.0,
            "SOCIAL_UPHEAVAL": 0.0
        }
        for t in res["transits"]:
            c_key = classify_transit_recurrence_theme(
                t["transit_planet_id"],
                t["natal_planet_id"],
                t["aspect_nature"]
            )
            cat_sums[c_key] += t["impact_score"]

        for c_key, raw_val in cat_sums.items():
            if raw_val > 0:
                s = int(round(1000.0 * (1.0 - math.exp(-raw_val / 24.0))))
                cat_series[c_key].append(min(995, s))
            else:
                cat_series[c_key].append(0)

        # Identifica trânsito mais intenso do ano
        if res["transits"]:
            top = res["transits"][0]
            major_transits_summary.append({
                "year": yr,
                "headline": f"{top['transit_symbol']} {top['transit_planet']} {top['aspect_symbol']} {top['natal_planet']} ({top['formatted_orb']})",
                "nature": top["aspect_nature"],
                "score": res["activation_index_1000"]
            })
        else:
            major_transits_summary.append({
                "year": yr,
                "headline": "Sem trânsitos maiores estritos",
                "nature": "neutro",
                "score": res["activation_index_1000"]
            })

    # Extrai o ano de fundação para ancoragem histórica
    try:
        foundation_year = int(country_chart.get("date", "1800")[:4])
    except (ValueError, TypeError):
        foundation_year = start_year

    # Extrai fatos históricos passados reais analisados
    analyzed_history = get_country_analyzed_history(country_chart)
    formatted_historical_events = []
    for h in analyzed_history:
        try:
            h_year = int(h["date"][:4])
        except (ValueError, TypeError):
            continue

        h_cat = h.get("category", "")
        if "Guerra" in h_cat or ("Conflito" in h_cat and "Interno" not in h_cat):
            cat_id = "WAR_CONFLICT"
        elif "Crise Financeira" in h_cat or "Econômica" in h_cat:
            cat_id = "ECONOMIC_CRASH"
        elif "Revolução" in h_cat or "Golpe" in h_cat or "Tratado" in h_cat or "Reforma" in h_cat:
            cat_id = "REGIME_CRISIS"
        else:
            cat_id = "SOCIAL_UPHEAVAL"

        formatted_historical_events.append({
            "year": h_year,
            "date": h["date"],
            "title": h["title"],
            "category_key": cat_id,
            "category_label": h["category"],
            "score": h.get("activation_index_1000", 500),
            "headline": h.get("protagonist_headline", ""),
            "description": h.get("description", "")
        })

    # Extrai os picos futuros detectados (2026–2050)
    detected_peaks = detect_energy_peaks_and_recurrences(country_chart, start_year=2026, end_year=2050)
    formatted_future_peaks = []
    for p in detected_peaks:
        try:
            p_year = int(p["sample_date"][:4])
        except (ValueError, TypeError):
            continue

        proto = p.get("protagonist_transit", {})
        proto_hl = f"{proto.get('transit_symbol', '')} {proto.get('transit_planet', '')} {proto.get('aspect_symbol', '')} {proto.get('natal_planet', '')} Natal"

        formatted_future_peaks.append({
            "year": p_year,
            "date": p["sample_date"],
            "range": p["window_range"],
            "title": p.get("era_label", ""),
            "category_key": p["category_key"],
            "category_label": p["category_label"],
            "category_short": p["category_short"],
            "score": p["activation_index_1000"],
            "headline": proto_hl,
            "precedent_title": p.get("precedent_title", ""),
            "tendency": p.get("future_recurrence_tendency", "")
        })

    return {
        "country_iso": country_chart["country_iso"],
        "start_year": start_year,
        "end_year": end_year,
        "foundation_year": foundation_year,
        "split_year": 2026,
        "years": years,
        "activation_scores": scores,
        "series": {
            "total": scores,
            "WAR_CONFLICT": cat_series["WAR_CONFLICT"],
            "ECONOMIC_CRASH": cat_series["ECONOMIC_CRASH"],
            "REGIME_CRISIS": cat_series["REGIME_CRISIS"],
            "SOCIAL_UPHEAVAL": cat_series["SOCIAL_UPHEAVAL"]
        },
        "historical_events": formatted_historical_events,
        "future_peaks": formatted_future_peaks,
        "category_meta": CATEGORY_METADATA,
        "major_transits": major_transits_summary
    }
