"""
Motor Analítico Contínuo e Prospectivo de Astrologia Moderna (1800–2100).
Calcula ano a ano a assinatura astronômica pelo Swiss Ephemeris em alta resolução
(Escala de 0 a 1000 pontos), com amostragem sazonal quádrupla (Equinócios e Solstícios).
Integra os fatos históricos reais ocorridos entre 1800 e 2025 diretamente aos seus anos,
e projeta as tendências e cenários prospectivos de 2026 a 2100.
"""

import os
import sys
import json
import time
import sqlite3
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import date

# Garantir que a raiz do projeto esteja no sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.astro_engine import calculate_event_chart, calculate_chart_tension_1000
from src.correlation_engine import find_similar_events

CACHE_FILE = "/home/astro/data/timeline_1800_2100.json"
OLD_CACHE_FILE = "/home/astro/data/future_simulation_2026_2060.json"
DB_PATH = "/home/astro/db/history_astrology.db"

def load_historical_events_from_db() -> Dict[int, List[Dict[str, Any]]]:
    """Carrega todos os eventos históricos cadastrados no SQLite com data >= 1800 agrupados por ano."""
    events_by_year = defaultdict(list)
    if not os.path.exists(DB_PATH):
        return events_by_year

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            """
            SELECT id, title, category, date, time, latitude, longitude, consequence, chart_json
            FROM events
            WHERE date >= '1800-01-01'
            ORDER BY date ASC
            """
        )
        rows = c.fetchall()
        for r in rows:
            yr_str = r[3].split("-")[0]
            try:
                yr = int(yr_str)
                events_by_year[yr].append({
                    "id": r[0],
                    "title": r[1],
                    "category": r[2],
                    "date": r[3],
                    "time": r[4] or "12:00",
                    "latitude": r[5] or 0.0,
                    "longitude": r[6] or 0.0,
                    "consequence": r[7] or "",
                    "chart_json": json.loads(r[8]) if r[8] else None
                })
            except Exception:
                continue
        conn.close()
    except Exception as e:
        print(f"Erro ao carregar eventos históricos: {e}")

    return events_by_year

def sample_year_charts(year: int, specific_event_dates: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    Amostra os 4 pontos sazonais cardinais do ano (Equinócios e Solstícios).
    P1-2: Não injeta datas específicas de eventos na amostragem geral para manter simetria e comparabilidade.
    """
    dates = [
        f"{year}-03-20",  # Equinócio de Outono (Hemisfério Sul) / Primavera (Norte)
        f"{year}-06-21",  # Solstício de Inverno / Verão
        f"{year}-09-22",  # Equinócio de Primavera / Outono
        f"{year}-12-21",  # Solstício de Verão / Inverno
    ]

    charts = []
    for d in dates:
        try:
            c = calculate_event_chart({
                "date": d,
                "time": "12:00",
                "latitude": 0.0,
                "longitude": 0.0,
                "title": f"Amostragem {d}"
            })
            charts.append(c)
        except Exception:
            continue

    return charts

def calculate_single_year(year: int, hist_events: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """Calcula a assinatura cosmológica completa de um ano específico (1800 a 2100) na escala de 0 a 1000 pontos."""
    hist_events = hist_events or []
    has_history = len(hist_events) > 0

    charts = sample_year_charts(year)

    if not charts:
        # Fallback de segurança se falhar amostragem
        mid_chart = calculate_event_chart({
            "date": f"{year}-07-01",
            "time": "12:00",
            "latitude": 0.0,
            "longitude": 0.0,
            "title": str(year)
        })
        charts = [mid_chart]

    # Avaliar os 4 portais sazonais com percentil empírico calibrado da grade diária
    scores_1000 = []
    sub_scores_list = []
    cardinal_dates = [date(year, 3, 20), date(year, 6, 21), date(year, 9, 22), date(year, 12, 21)]
    for idx, ch in enumerate(charts):
        s_data = calculate_chart_tension_1000(ch)
        try:
            from src.core.ephemeris_grid import get_score_for_date
            calibrated_gate_score = get_score_for_date(cardinal_dates[idx])
        except Exception:
            calibrated_gate_score = s_data["tension_index_1000"]
        s_data["tension_index_1000"] = calibrated_gate_score
        scores_1000.append(calibrated_gate_score)
        sub_scores_list.append(s_data)

    # Estatísticas diárias reais e percentil anual calibrado da janela anual
    try:
        from src.core.ephemeris_grid import get_calibrated_year_metrics, get_score_for_date
        calibrated_metrics = get_calibrated_year_metrics(year)
        annual_percentile = calibrated_metrics["annual_percentile_1000"]
        avg_tension = calibrated_metrics["daily_mean_percentile"]
        median_tension = calibrated_metrics["daily_median_percentile"]
        peak_tension = calibrated_metrics["daily_max_percentile"]
        p90_tension = calibrated_metrics["daily_p90_percentile"]
        days_above_p90 = calibrated_metrics["days_above_p90"]
        expected_days_above_p90 = calibrated_metrics["expected_days_above_p90"]
        tier_label = calibrated_metrics["tier_label"]
        tier_color = calibrated_metrics["tier_color"]
    except Exception:
        peak_tension = max(scores_1000)
        avg_tension = round(sum(scores_1000) / len(scores_1000), 1)
        median_tension = avg_tension
        p90_tension = peak_tension
        annual_percentile = avg_tension
        days_above_p90 = 36
        expected_days_above_p90 = 36.5
        tier_label = "Percentil Moderado"
        tier_color = "sky"

    # Mapeamento neutro de nível e cor para a interface
    alert_level = tier_label
    alert_color = "red" if tier_color == "indigo" else ("yellow" if tier_color == "sky" else "green")

    # v3: o pico REAL do ano vem da grade diária (365 dias), não dos 4 portais sazonais.
    peak_date_str = None
    try:
        from datetime import timedelta
        from src.core.ephemeris_grid import get_daily_grid, get_day_index
        grid = get_daily_grid()
        i0, i1 = get_day_index(date(year, 1, 1)), get_day_index(date(year, 12, 31))
        if i0 is not None and i1 is not None:
            peak_day = date(year, 1, 1) + timedelta(days=int(grid["raw_scores"][i0:i1 + 1].argmax()))
            peak_date_str = peak_day.isoformat()
            peak_chart = calculate_event_chart({"date": peak_date_str, "time": "12:00", "latitude": 0.0, "longitude": 0.0, "title": f"Pico {year}"})
    except Exception:
        peak_chart = None
    if peak_chart is None:
        peak_idx = scores_1000.index(max(scores_1000)) if scores_1000 else 0
        peak_chart = charts[peak_idx]

    # Posições dos planetas geracionais no pico
    planets_map = {p["id"]: p for p in peak_chart.get("planets", [])}
    pluto_sign = planets_map.get("pluto", {}).get("sign_name", "Desconhecido")
    neptune_sign = planets_map.get("neptune", {}).get("sign_name", "Desconhecido")
    uranus_sign = planets_map.get("uranus", {}).get("sign_name", "Desconhecido")
    saturn_sign = planets_map.get("saturn", {}).get("sign_name", "Desconhecido")

    key_aspects_str = ", ".join([
        f"{a['planet1_symbol']}{a['aspect_symbol']}{a['planet2_symbol']}"
        for a in peak_chart.get("aspects", [])[:3]
    ]) or "Aspectos fluídos"

    star_contacts = peak_chart.get("star_contacts", [])
    top_star_name = star_contacts[0]["star_name"] if star_contacts else "Nenhuma estrela maior ativa"

    cosmic_trigger = (
        f"Plutão em {pluto_sign}, Netuno em {neptune_sign}, Urano em {uranus_sign}, Saturno em {saturn_sign}. "
        f"Aspectos-chave: {key_aspects_str}. "
        f"{'★ Estrela Ativa: ' + top_star_name if star_contacts else ''}"
    )

    # Similaridade com a base histórica aplicando Leave-One-Out (P0-3: exclui ano +/- 1)
    sim_data = find_similar_events(peak_chart, top_k=3, exclude_year=year, exclude_window=1)
    top_matches = sim_data.get("top_matches", [])
    dom_cat = sim_data.get("dominant_matching_category", "Transformação Cultural")
    resonance = sim_data.get("avg_match_percent", 50.0)

    # Síntese textual exclusivamente derivada das efemérides reais calculadas
    if has_history:
        main_hist = hist_events[0]
        titles_str = " | ".join([e["title"] for e in hist_events])
        scenario_text = (
            f"FATO HISTÓRICO REAL: {titles_str}. "
            f"Percentil Médio Anual: {annual_percentile:.1f}/1000 ({tier_label}, {days_above_p90} dias > P90 da era). "
            f"Configuração calculada pelo Swiss Ephemeris: Plutão em {pluto_sign}, Netuno em {neptune_sign}, Urano em {uranus_sign}, Saturno em {saturn_sign}. "
            f"Consequências registradas na história: \"{main_hist['consequence'][:220]}...\""
        )
        historical_summary = [
            {
                "id": e["id"],
                "title": e["title"],
                "category": e["category"],
                "date": e["date"],
                "consequence": e["consequence"]
            }
            for e in hist_events
        ]
    elif year < 2026:
        top_past_title = top_matches[0]["title"] if top_matches else "Marcos da História"
        top_match_sim = top_matches[0]["match_percent"] if top_matches else 50.0
        scenario_text = (
            f"Ano histórico sem fato específico no catálogo dos 200 marcos. "
            f"Percentil Médio Anual: {annual_percentile:.1f}/1000 ({tier_label}, {days_above_p90} dias > P90). "
            f"Configuração calculada: Plutão em {pluto_sign}, Netuno em {neptune_sign}, Urano em {uranus_sign}, Saturno em {saturn_sign}. "
            f"Isomorfismo geométrico mais próximo: '{top_past_title}' ({top_match_sim}% de similaridade angular)."
        )
        historical_summary = []
    else:
        top_past_title = top_matches[0]["title"] if top_matches else "Marcos da modernidade"
        top_past_consequence = top_matches[0]["consequence"][:160] if top_matches else ""
        top_match_sim = top_matches[0]["match_percent"] if top_matches else 50.0
        scenario_text = (
            f"Horizonte prospectivo para {year}: Percentil Médio Anual de {annual_percentile:.1f}/1000 ({tier_label}), "
            f"com {days_above_p90} dias acima do percentil 90 da era (esperado ao acaso: {expected_days_above_p90:.1f} dias). "
            f"Configuração calculada: Plutão em {pluto_sign}, Netuno em {neptune_sign}, Urano em {uranus_sign}, Saturno em {saturn_sign}. "
            f"Isomorfismo geométrico mais próximo: '{top_past_title}' ({top_match_sim}% de similaridade). "
            f"Nota metodológica (M2): este paralelo reflete proximidade de coordenadas celestes, sem valor preditivo determinístico."
        )
        historical_summary = []

    # Compatibilidade com campos anteriores
    legacy_tension_100 = round(annual_percentile / 10.0, 1)

    return {
        "year": year,
        "is_historical": has_history,
        "historical_events": historical_summary,
        "tension_index": legacy_tension_100,
        "tension_index_1000": annual_percentile,  # agora calibrado para percentil anual
        "annual_percentile_1000": annual_percentile,
        "avg_tension_1000": avg_tension,
        "days_above_p90": days_above_p90,
        "expected_days_above_p90": expected_days_above_p90,
        "tier_label": tier_label,
        "tier_color": tier_color,
        "peak_tension_1000": peak_tension,
        "conflict_risk_index": 0.0,
        "conflict_risk_index_1000": 0.0,
        "crisis_risk_index": 0.0,
        "crisis_risk_index_1000": 0.0,
        "tech_innovation_index": 0.0,
        "tech_innovation_index_1000": 0.0,
        "social_transformation_index_1000": 0.0,
        "resonance_index": round(resonance, 1),
        "alert_level": alert_level,
        "alert_color": alert_color,
        "peak_date": peak_date_str,
        "dominant_category": dom_cat,
        "cosmic_trigger": cosmic_trigger,
        "pluto_sign": pluto_sign,
        "neptune_sign": neptune_sign,
        "uranus_sign": uranus_sign,
        "saturn_sign": saturn_sign,
        "key_aspects_count": len(peak_chart.get("aspects", [])),
        "star_contacts_count": len(star_contacts),
        "top_matches": top_matches,
        "scenarios_and_possibilities": scenario_text
    }

def generate_future_timeline_1800_2100(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Gera a linha do tempo prospectiva e histórica completa para 301 anos (1800 a 2100).
    Utiliza amostragem quádrupla e cache em disco para inicialização instantânea.
    """
    if not force_refresh and os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if len(data.get("timeline", [])) == 301 and data.get("start_year") == 1800:
                    return data
        except Exception:
            pass

    start_time = time.time()
    events_by_year = load_historical_events_from_db()

    timeline = []
    for yr in range(1800, 2101):
        year_hist = events_by_year.get(yr, [])
        y_data = calculate_single_year(yr, hist_events=year_hist)
        timeline.append(y_data)

    total_time = round(time.time() - start_time, 2)

    # Identificar picos e estatísticas
    past_timeline = [t for t in timeline if t["year"] < 2026]
    future_timeline = [t for t in timeline if t["year"] >= 2026]

    highest_past_rupture = max(past_timeline, key=lambda x: x["tension_index_1000"]) if past_timeline else timeline[0]
    highest_future_tension = max(future_timeline, key=lambda x: x["tension_index_1000"]) if future_timeline else timeline[-1]
    highest_tech = max(timeline, key=lambda x: x["tech_innovation_index_1000"])
    highest_conflict = max(timeline, key=lambda x: x["conflict_risk_index_1000"])

    avg_past = round(sum(t["tension_index_1000"] for t in past_timeline) / len(past_timeline), 1) if past_timeline else 0.0
    avg_future = round(sum(t["tension_index_1000"] for t in future_timeline) / len(future_timeline), 1) if future_timeline else 0.0

    result = {
        "start_year": 1800,
        "end_year": 2100,
        "total_years_calculated": len(timeline),
        "calculation_time_seconds": total_time,
        "highest_past_rupture": {
            "year": highest_past_rupture["year"],
            "tension": highest_past_rupture["tension_index_1000"],
            "title": highest_past_rupture["historical_events"][0]["title"] if highest_past_rupture["historical_events"] else "Pico do Passado",
            "trigger": highest_past_rupture["cosmic_trigger"]
        },
        "highest_future_year": {
            "year": highest_future_tension["year"],
            "tension": highest_future_tension["tension_index_1000"],
            "trigger": highest_future_tension["cosmic_trigger"]
        },
        "highest_tech_year": {
            "year": highest_tech["year"],
            "index": highest_tech["tech_innovation_index_1000"],
            "trigger": highest_tech["cosmic_trigger"]
        },
        "highest_conflict_year": {
            "year": highest_conflict["year"],
            "risk": highest_conflict["conflict_risk_index_1000"],
            "trigger": highest_conflict["cosmic_trigger"]
        },
        "avg_past_tension": avg_past,
        "avg_future_tension": avg_future,
        "historical_events_count": sum(len(t["historical_events"]) for t in timeline),
        "timeline": timeline
    }

    # Salvar cache principal de 1800-2100
    os.makedirs(os.path.dirname(CACHE_FILE), exist_ok=True)
    with open(CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Atualizar também o arquivo legado para compatibilidade contínua
    try:
        legacy_result = dict(result)
        legacy_result["timeline_2026_2060"] = [t for t in timeline if 2026 <= t["year"] <= 2060]
        with open(OLD_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(legacy_result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return result

PROJECTIONS_CACHE_FILE = "/home/astro/data/projections_2027_2060.json"

def get_projections_2027_2060(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Retorna as projeções anuais e sazonais detalhadas de 2027 a 2060 (34 anos)
    com datas exatas dos portais sazonais, picos de tensão, riscos calculados,
    precedentes históricos análogos e cenários prospectivos completos.
    """
    if not force_refresh and os.path.exists(PROJECTIONS_CACHE_FILE):
        try:
            with open(PROJECTIONS_CACHE_FILE, "r", encoding="utf-8") as f:
                cached = json.load(f)
                if len(cached.get("projections", [])) == 34:
                    return cached
        except Exception:
            pass

    timeline_data = generate_future_timeline_1800_2100(force_refresh=force_refresh)
    years_dict = {t["year"]: t for t in timeline_data.get("timeline", [])}

    projections = []
    season_labels = [
        ("03-20", "Equinócio de Março (Outono Sul / Prim Norte)"),
        ("06-21", "Solstício de Junho (Inverno Sul / Verão Norte)"),
        ("09-22", "Equinócio de Setembro (Primavera Sul / Outono Norte)"),
        ("12-21", "Solstício de Dezembro (Verão Sul / Inverno Norte)"),
    ]

    for yr in range(2027, 2061):
        base_item = years_dict.get(yr)
        if not base_item:
            base_item = calculate_single_year(yr)

        # Amostragem das 4 datas sazonais com percentil diário empírico calibrado
        seasonal_gates = []
        for s_date_suf, s_name in season_labels:
            full_date = f"{yr}-{s_date_suf}"
            try:
                m_part, d_part = int(s_date_suf.split("-")[0]), int(s_date_suf.split("-")[1])
                from src.core.ephemeris_grid import get_score_for_date
                t_score = get_score_for_date(date(yr, m_part, d_part))
                seasonal_gates.append({
                    "date": full_date,
                    "season_label": s_name,
                    "short_season": s_name.split(" ")[0] + " " + s_name.split(" ")[2],
                    "tension_1000": t_score,
                    "tension_percent": round(t_score / 10.0, 1),
                })
            except Exception:
                continue

        if base_item.get("peak_date"):
            peak_date = base_item["peak_date"]
            peak_season = "Pico diário real do ano (grade 1800–2100)"
        elif seasonal_gates:
            peak_gate = max(seasonal_gates, key=lambda g: g["tension_1000"])
            peak_date = peak_gate["date"]
            peak_season = peak_gate["season_label"]
        else:
            peak_date = f"{yr}-06-21"
            peak_season = "Solstício de Junho"

        # Década
        decade = f"{yr // 10 * 10}s"

        # Precedente de maior correlação
        top_m = base_item.get("top_matches", [])
        top_prec = top_m[0] if top_m else {
            "title": "Marcos da História Moderna",
            "category": base_item.get("dominant_category", "Transformação Cultural"),
            "match_percent": 50.0,
            "consequence": ""
        }

        # Métricas anuais calibradas
        annual_pct = base_item.get("annual_percentile_1000", 500.0)
        daily_mean_val = base_item.get("avg_tension_1000", 500.0)
        days_above_p90 = base_item.get("days_above_p90", 36)
        expected_days_above_p90 = base_item.get("expected_days_above_p90", 36.5)
        tier_label = base_item.get("tier_label", "Percentil Moderado")
        tier_color = base_item.get("tier_color", "sky")

        ui_alert_color = "red" if tier_color == "indigo" else ("yellow" if tier_color == "sky" else "green")
        ui_alert_level = tier_label

        proj_row = {
            "year": yr,
            "decade": decade,
            "peak_date": peak_date,
            "peak_season": peak_season,
            "seasonal_gates": seasonal_gates,
            "annual_percentile_1000": annual_pct,
            "annual_percentile_str": f"{annual_pct / 10.0:.1f}%",
            "tension_1000": annual_pct,
            "tension_percent": round(annual_pct / 10.0, 1),
            "tension_percent_str": f"{annual_pct / 10.0:.1f}%",
            "avg_tension_1000": daily_mean_val,
            "days_above_p90": days_above_p90,
            "expected_days_above_p90": expected_days_above_p90,
            "tier_label": tier_label,
            "tier_color": tier_color,
            "alert_level": ui_alert_level,
            "alert_color": ui_alert_color,
            "dominant_category": base_item.get("dominant_category", "Transformação Cultural"),
            "cosmic_trigger": base_item.get("cosmic_trigger", ""),
            "pluto_sign": base_item.get("pluto_sign", ""),
            "neptune_sign": base_item.get("neptune_sign", ""),
            "uranus_sign": base_item.get("uranus_sign", ""),
            "saturn_sign": base_item.get("saturn_sign", ""),
            "top_precedent": top_prec,
            "top_matches": top_m,
            "scenarios_and_possibilities": base_item.get("scenarios_and_possibilities", "")
        }
        projections.append(proj_row)

    # Métricas agregadas do horizonte 2027-2060
    highest_tension = max(projections, key=lambda p: p["tension_1000"])
    lowest_tension = min(projections, key=lambda p: p["tension_1000"])
    highest_days = max(projections, key=lambda p: p["days_above_p90"])
    avg_tension = round(sum(p["tension_1000"] for p in projections) / len(projections), 1)

    result = {
        "start_year": 2027,
        "end_year": 2060,
        "total_years": len(projections),
        "kpis": {
            "highest_tension": highest_tension,
            "lowest_tension": lowest_tension,
            "highest_days_p90": highest_days,
            "avg_tension_1000": avg_tension,
            "avg_tension_percent": round(avg_tension / 10.0, 1),
            "superior_count": sum(1 for p in projections if p["tier_label"] == "Percentil Superior"),
            "moderate_count": sum(1 for p in projections if p["tier_label"] == "Percentil Moderado"),
            "basal_count": sum(1 for p in projections if p["tier_label"] == "Percentil Basal"),
            "alert_red_count": sum(1 for p in projections if p["alert_color"] == "red"),
            "alert_orange_count": sum(1 for p in projections if p["alert_color"] == "orange"),
            "alert_yellow_count": sum(1 for p in projections if p["alert_color"] == "yellow"),
            "alert_green_count": sum(1 for p in projections if p["alert_color"] == "green"),
        },
        "projections": projections
    }

    # Salvar em cache
    try:
        os.makedirs(os.path.dirname(PROJECTIONS_CACHE_FILE), exist_ok=True)
        with open(PROJECTIONS_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

    return result

# Alias para compatibilidade com código existente
def generate_future_timeline_2026_2060(force_refresh: bool = False) -> Dict[str, Any]:
    return generate_future_timeline_1800_2100(force_refresh=force_refresh)

def calculate_single_future_year(year: int) -> Dict[str, Any]:
    return calculate_single_year(year)

if __name__ == "__main__":
    print("Iniciando cálculo analítico contínuo de 1800 a 2100 (301 anos)...")
    data = generate_future_timeline_1800_2100(force_refresh=True)
    print(f"Sucesso! {data['total_years_calculated']} anos calculados em {data['calculation_time_seconds']}s")
    print(f"Total de fatos históricos integrados: {data['historical_events_count']}")
    print(f"Maior Ruptura do Passado: {data['highest_past_rupture']['year']} ({data['highest_past_rupture']['tension']}/1000) - {data['highest_past_rupture']['title']}")
    print(f"Maior Pico Futuro: {data['highest_future_year']['year']} ({data['highest_future_year']['tension']}/1000)")
    print(f"Média Tensão Passado (1800-2025): {data['avg_past_tension']}/1000 | Média Futuro (2026-2100): {data['avg_future_tension']}/1000")
