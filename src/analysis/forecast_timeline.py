"""
Motor Unificado de Linha do Tempo e Previsão 2026–2060 (Forecast Timeline).
Consolida:
1. Modelos probabilísticos com skill medido (forecast_v3.json)
2. Catálogo de 148 picos de energia com datas exatas, precedentes e cenários (energy_peaks_2026_2060.json)
3. Projeções de tensão geométrica e portais sazonais (projections_2027_2060.json e timeline_1800_2100.json)
4. Metadados das 8 categorias canônicas estimáveis (config/categories.yaml)

Permite visualização cronológica ano a ano e data a data, com scores de pontuação (0–1000),
níveis de alerta, categorias temáticas, acontecimentos projetados e correlações históricas.
"""

import json
import os
from typing import Dict, Any, List, Optional
import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

FORECAST_FILE = os.path.join(ROOT, "data", "forecast_v3.json")
PEAKS_FILE = os.path.join(ROOT, "data", "energy_peaks_2026_2060.json")
PROJECTIONS_FILE = os.path.join(ROOT, "data", "projections_2027_2060.json")
TIMELINE_FILE = os.path.join(ROOT, "data", "timeline_1800_2100.json")
CATEGORIES_FILE = os.path.join(ROOT, "config", "categories.yaml")

_CACHE_TIMELINE: Optional[Dict[str, Any]] = None


def load_categories_meta() -> Dict[str, Dict[str, Any]]:
    """Carrega metadados das categorias canônicas estimáveis."""
    categories: Dict[str, Dict[str, Any]] = {}
    if os.path.exists(CATEGORIES_FILE):
        try:
            with open(CATEGORIES_FILE, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                categories = data.get("categories", {})
        except Exception:
            pass

    # Aliases e fallbacks úteis
    if "SCIENCE_INNOVATION" in categories and "TECH_INNOVATION" not in categories:
        categories["TECH_INNOVATION"] = categories["SCIENCE_INNOVATION"]
    return categories


def _format_date_pt(iso_date: str) -> str:
    """Converte YYYY-MM-DD para DD/MM/AAAA."""
    if not iso_date or len(iso_date) < 10:
        return iso_date or ""
    parts = iso_date[:10].split("-")
    if len(parts) == 3:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return iso_date


def build_unified_forecast_data() -> Dict[str, Any]:
    """
    Constrói a estrutura unificada de previsão (2026–2060) consolidando
    anos, datas de picos de energia, scores de 0 a 1000, categorias e cenários.
    """
    global _CACHE_TIMELINE
    if _CACHE_TIMELINE is not None:
        return _CACHE_TIMELINE

    categories_meta = load_categories_meta()

    # 1. Carregar datasets
    fc_data: Dict[str, Any] = {}
    if os.path.exists(FORECAST_FILE):
        with open(FORECAST_FILE, "r", encoding="utf-8") as f:
            fc_data = json.load(f)

    peaks_raw: List[Dict[str, Any]] = []
    if os.path.exists(PEAKS_FILE):
        with open(PEAKS_FILE, "r", encoding="utf-8") as f:
            peaks_data = json.load(f)
            peaks_raw = peaks_data.get("peaks", [])

    projections_map: Dict[int, Dict[str, Any]] = {}
    if os.path.exists(PROJECTIONS_FILE):
        with open(PROJECTIONS_FILE, "r", encoding="utf-8") as f:
            pj_data = json.load(f)
            for p in pj_data.get("projections", []):
                projections_map[p["year"]] = p

    # Obter dados de 2026 da linha do tempo
    if 2026 not in projections_map and os.path.exists(TIMELINE_FILE):
        try:
            with open(TIMELINE_FILE, "r", encoding="utf-8") as f:
                tl = json.load(f).get("timeline", [])
                y26 = next((y for y in tl if y.get("year") == 2026), None)
                if y26:
                    projections_map[2026] = {
                        "year": 2026,
                        "decade": "2020s",
                        "peak_date": y26.get("peak_date", "2026-02-27"),
                        "peak_season": "Verão / Inverno",
                        "seasonal_gates": [],
                        "annual_percentile_1000": y26.get("annual_percentile_1000", 425.2),
                        "annual_percentile_str": f"{y26.get('annual_percentile_1000', 425.2):.1f}",
                        "tension_1000": y26.get("peak_tension_1000", 978.2),
                        "tension_percent": y26.get("tension_index", 42.5),
                        "tension_percent_str": f"{y26.get('tension_index', 42.5):.1f}%",
                        "avg_tension_1000": y26.get("avg_tension_1000", 436.0),
                        "days_above_p90": y26.get("days_above_p90", 18),
                        "expected_days_above_p90": 36.5,
                        "tier_label": "Percentil Moderado (Pico Crítico em Fev/2026)",
                        "tier_color": "rose",
                        "alert_level": "Crítico",
                        "alert_color": "rose",
                        "dominant_category": "Revolução & Conflito Interno",
                        "cosmic_trigger": y26.get("cosmic_trigger", "Saturno conjunção Netuno a 0° de Áries"),
                        "pluto_sign": y26.get("pluto_sign", "Aquário"),
                        "neptune_sign": y26.get("neptune_sign", "Áries"),
                        "uranus_sign": y26.get("uranus_sign", "Touro"),
                        "saturn_sign": y26.get("saturn_sign", "Áries"),
                        "top_precedent": {
                            "title": "Doutrina Truman / Início da Guerra Fria (1947) e Eclosão do Sputnik (1957)",
                            "year": 1947,
                            "category": "Política, Tratados & Cultura",
                            "similarity": 0.40
                        },
                        "top_matches": y26.get("top_matches", []),
                        "scenarios_and_possibilities": "Marco zero da ordem internacional do século XXI. O encontro histórico de Saturno e Netuno no Ponto Vernal (0° Áries) e a entrada de Plutão em Aquário inauguram um ciclo de desmantelamento de tratados obsoletos, corridas espaciais e ciberdefesa quântica."
                    }
        except Exception:
            pass

    # 2. Agrupar picos por ano
    peaks_by_year: Dict[int, List[Dict[str, Any]]] = {}
    for p in peaks_raw:
        yr = p.get("year")
        if yr is None and p.get("peak_date"):
            try:
                yr = int(p["peak_date"][:4])
            except Exception:
                pass
        if yr is None:
            continue

        cat_key = p.get("scenario_key", "WAR_CONFLICT")
        meta = categories_meta.get(cat_key, {})
        score_1000 = float(p.get("energy_score_1000") or 0.0)

        # Determinar cor do alerta baseado no score
        if score_1000 >= 900:
            alert_lvl = "Crítico"
            alert_clr = "rose"
        elif score_1000 >= 750:
            alert_lvl = "Alto"
            alert_clr = "amber"
        elif score_1000 >= 500:
            alert_lvl = "Moderado"
            alert_clr = "sky"
        else:
            alert_lvl = "Estável"
            alert_clr = "emerald"

        processed_peak = {
            "id": p.get("id"),
            "year": yr,
            "peak_date": p.get("peak_date", ""),
            "formatted_date": _format_date_pt(p.get("peak_date", "")),
            "category_key": cat_key,
            "category_label": meta.get("label_pt", p.get("scenario_label_pt", cat_key)),
            "category_short": meta.get("short_pt", p.get("scenario_label_pt", cat_key)),
            "category_icon": meta.get("icon", p.get("scenario_icon", "🪐")),
            "category_color": meta.get("theme_color", p.get("scenario_color", "amber")),
            "badge_class": meta.get("bg_badge", p.get("badge_class", "bg-amber-500/20 text-amber-300 border-amber-500/40")),
            "energy_score_1000": round(score_1000, 1),
            "score_percent": round(score_1000 / 10.0, 1),
            "alert_level": alert_lvl,
            "alert_color": alert_clr,
            "scope_type": p.get("scope_type", "world"),
            "country_iso": p.get("country_iso"),
            "country_name": p.get("country_name_pt", "Global / Mundial"),
            "country_flag": p.get("country_flag", "🌐"),
            "cosmic_signature": p.get("cosmic_signature", ""),
            "cosmic_signature_detail": p.get("cosmic_signature_detail", p.get("cosmic_signature", "")),
            "historical_precedent_title": p.get("historical_precedent_title", ""),
            "historical_precedent_year": p.get("historical_precedent_year", ""),
            "historical_precedent_summary": p.get("historical_precedent_summary", ""),
            "prospective_synthesis": p.get("prospective_synthesis", ""),
            "decade": p.get("decade", f"{(yr // 10) * 10}s")
        }
        peaks_by_year.setdefault(yr, []).append(processed_peak)

    # Ordenar picos dentro de cada ano por data
    for yr in peaks_by_year:
        peaks_by_year[yr].sort(key=lambda x: (x["peak_date"], -x["energy_score_1000"]))

    # 3. Construir lista de anos 2026 a 2060
    years_list: List[Dict[str, Any]] = []
    fc_calendar = fc_data.get("calendar", {})
    fc_analogs = fc_data.get("analogs", {})
    fc_targets = fc_data.get("targets", {})

    category_counts: Dict[str, int] = {}
    alert_counts: Dict[str, int] = {"Crítico": 0, "Alto": 0, "Moderado": 0, "Estável": 0}
    decade_counts: Dict[str, int] = {}

    for year in range(2026, 2061):
        decade = f"{(year // 10) * 10}s"
        decade_counts[decade] = decade_counts.get(decade, 0) + 1

        proj = projections_map.get(year, {})
        cal = fc_calendar.get(str(year), {"aspects": [], "ingresses": [], "eclipses": []})
        analogs = fc_analogs.get(str(year), {"analogs": [], "lift": 1.0, "hit_rate_6m": 0.0, "expected_rate_6m": 0.0})
        year_peaks = peaks_by_year.get(year, [])

        # Calcular score anual e pico
        tension_score = float(proj.get("tension_1000") or (year_peaks[0]["energy_score_1000"] if year_peaks else 500.0))
        pct_1000 = float(proj.get("annual_percentile_1000") or (tension_score * 0.8))

        # Determinar nível de alerta do ano
        if tension_score >= 900 or any(p["alert_level"] == "Crítico" for p in year_peaks):
            year_alert = "Crítico"
            year_alert_color = "rose"
        elif tension_score >= 750 or any(p["alert_level"] == "Alto" for p in year_peaks):
            year_alert = "Alto"
            year_alert_color = "amber"
        elif tension_score >= 500 or year_peaks:
            year_alert = "Moderado"
            year_alert_color = "sky"
        else:
            year_alert = "Estável"
            year_alert_color = "emerald"

        alert_counts[year_alert] += 1

        # Categoria dominante do ano
        dom_cat = proj.get("dominant_category", "")
        if year_peaks and not dom_cat:
            dom_cat = year_peaks[0]["category_label"]

        # Resumo das probabilidades dos modelos para este ano
        prob_summary: Dict[str, Any] = {}
        for t_key, t_info in fc_targets.items():
            t_years = t_info.get("years", [])
            matched_yr = next((r for r in t_years if r.get("year") == year), None)
            if matched_yr:
                prob_summary[t_key] = {
                    "label": t_info.get("label", t_key),
                    "base_rate": t_info.get("base_rate", 0.0),
                    "p_mean": matched_yr.get("p_mean", 0.0),
                    "p_lo": matched_yr.get("p_lo", 0.0),
                    "p_hi": matched_yr.get("p_hi", 0.0),
                    "ratio_to_base": matched_yr.get("ratio_to_base", 1.0),
                    "p_peak_month": matched_yr.get("p_peak_month", 1),
                    "drivers": matched_yr.get("drivers", [])[:3]
                }

        # Atualizar contadores de categoria a partir dos picos
        for p in year_peaks:
            ck = p["category_key"]
            category_counts[ck] = category_counts.get(ck, 0) + 1

        year_entry = {
            "year": year,
            "decade": decade,
            "tension_score_1000": round(tension_score, 1),
            "tension_percent": round(tension_score / 10.0, 1),
            "annual_percentile_1000": round(pct_1000, 1),
            "alert_level": year_alert,
            "alert_color": year_alert_color,
            "dominant_category": dom_cat,
            "peak_date": proj.get("peak_date", year_peaks[0]["peak_date"] if year_peaks else f"{year}-06-21"),
            "formatted_peak_date": _format_date_pt(proj.get("peak_date", year_peaks[0]["peak_date"] if year_peaks else f"{year}-06-21")),
            "cosmic_trigger": proj.get("cosmic_trigger", "Alinhamentos dos planetas lentos no zodíaco"),
            "scenarios_and_possibilities": proj.get("scenarios_and_possibilities", "Projeção de ciclos mundanos e reorganização de forças geopolíticas e econômicas."),
            "top_precedent": proj.get("top_precedent", {}),
            "peaks": year_peaks,
            "peaks_count": len(year_peaks),
            "calendar": cal,
            "analogs": analogs,
            "probabilities": prob_summary,
            "pluto_sign": proj.get("pluto_sign", "Aquário" if year < 2043 else "Peixes"),
            "neptune_sign": proj.get("neptune_sign", "Áries" if year < 2038 else "Touro"),
            "uranus_sign": proj.get("uranus_sign", "Gêmeos" if year < 2033 else "Câncer"),
            "saturn_sign": proj.get("saturn_sign", "Áries" if year < 2028 else "Touro"),
            "has_critical_peaks": any(p["alert_level"] == "Crítico" for p in year_peaks),
        }
        years_list.append(year_entry)

    # 4. Compilar KPIs gerais
    kpis = {
        "total_years": len(years_list),
        "total_peaks": len(peaks_raw),
        "alert_counts": alert_counts,
        "critical_years": [y["year"] for y in years_list if y["alert_level"] == "Crítico"],
        "category_counts": category_counts,
        "decade_counts": decade_counts,
        "start_year": 2026,
        "end_year": 2060
    }

    _CACHE_TIMELINE = {
        "years": years_list,
        "kpis": kpis,
        "categories_meta": categories_meta,
        "targets": fc_targets
    }
    return _CACHE_TIMELINE
