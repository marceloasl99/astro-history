"""
Motor de Previsão Pessoal (Personal Forecast Engine 2026–2050).
Consolida:
1. Trânsitos diários de planetas lentos aos pontos natais (prof["lifetime"]["windows"])
2. Progressões secundárias dia-por-ano e linha do tempo da Lua progredida (prog["moon"])
3. Grandes ciclos de vida (retornos de Saturno, Júpiter, Quíron, oposição de Urano)
4. Calibração dos 8 domínios vitais (escala 0–1000)
5. Identificação de confluências (trânsitos e progressões ativando simultaneamente o mesmo tema)

Produz uma linha do tempo prospectiva ano a ano (2026 a 2050 ou horizonte selecionável) com:
- Score de intensidade pessoal (0–1000)
- Nível de impacto (Pico Decisivo, Alta Ativação, Moderado, Estável)
- Radar dos 8 domínios de vida
- Datas críticas e acontecimentos detalhados com orientações práticas e reflexivas
"""

from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urlencode
import datetime
import numpy as np

from src.natal.models import BirthInput
from src.natal.service import build_profile, build_progressions, now_jd, jd_to_iso
from src.natal.interpretations import library, describe_window, describe_cycle


DOMAIN_TRANSLATIONS = {
    "identity": {"label": "Vitalidade & Identidade", "icon": "⚡", "theme_color": "rose"},
    "mind_learning": {"label": "Mente, Estudos & Comunicação", "icon": "💡", "theme_color": "sky"},
    "relationships": {"label": "Relações, Amor & Parcerias", "icon": "❤️", "theme_color": "rose"},
    "career": {"label": "Carreira, Visibilidade & Propósito", "icon": "👑", "theme_color": "amber"},
    "resources": {"label": "Finanças, Bens & Recursos", "icon": "💰", "theme_color": "emerald"},
    "home_family": {"label": "Estrutura, Família & Raízes", "icon": "🏡", "theme_color": "indigo"},
    "purpose_transformation": {"label": "Transformação & Crises Evolutivas", "icon": "🌋", "theme_color": "purple"},
    "health_routine": {"label": "Saúde, Rotina & Equilíbrio", "icon": "🌿", "theme_color": "teal"},
}

CRITICALITY_TIERS = [
    {
        "key": "climax",
        "label": "Pico Transformador",
        "min_score": 850,
        "max_score": 1000,
        "color": "rose",
        "icon": "💥",
        "badge_class": "bg-rose-500/20 text-rose-300 border-rose-500/40 shadow-sm shadow-rose-500/10",
        "text_color": "text-rose-400",
        "bar_class": "bg-rose-500",
        "range_label": "Score ≥ 850/1000",
        "description": "Momentos culminantes de metamorfose radical, pontos de virada máxima de destino ou grandes consagrações."
    },
    {
        "key": "turning_point",
        "label": "Ponto de Virada",
        "min_score": 700,
        "max_score": 849,
        "color": "orange",
        "icon": "⚡",
        "badge_class": "bg-orange-500/20 text-orange-300 border-orange-500/40 shadow-sm shadow-orange-500/10",
        "text_color": "text-orange-400",
        "bar_class": "bg-orange-500",
        "range_label": "Score 700–849/1000",
        "description": "Transições cruciais, redefinição de prioridades de vida, decisões estruturantes e marcos evolutivos."
    },
    {
        "key": "high_activation",
        "label": "Alta Ativação",
        "min_score": 550,
        "max_score": 699,
        "color": "amber",
        "icon": "🔥",
        "badge_class": "bg-amber-500/20 text-amber-300 border-amber-500/40 shadow-sm shadow-amber-500/10",
        "text_color": "text-amber-300",
        "bar_class": "bg-amber-400",
        "range_label": "Score 550–699/1000",
        "description": "Forte aceleração de acontecimentos, expansão de oportunidades, produtividade e movimento dinâmico."
    },
    {
        "key": "moderate",
        "label": "Moderado",
        "min_score": 400,
        "max_score": 549,
        "color": "sky",
        "icon": "🌊",
        "badge_class": "bg-sky-500/20 text-sky-300 border-sky-500/40",
        "text_color": "text-sky-300",
        "bar_class": "bg-sky-400",
        "range_label": "Score 400–549/1000",
        "description": "Desenvolvimento ritmado, evolução gradual, ajustes de rota e maturidade sem sobressaltos agudos."
    },
    {
        "key": "consolidation",
        "label": "Consolidação",
        "min_score": 250,
        "max_score": 399,
        "color": "emerald",
        "icon": "🌿",
        "badge_class": "bg-emerald-500/20 text-emerald-300 border-emerald-500/40",
        "text_color": "text-emerald-300",
        "bar_class": "bg-emerald-400",
        "range_label": "Score 250–399/1000",
        "description": "Fixação de conquistas anteriores, estabilização de rotinas e assimilação tranquila de aprendizados."
    },
    {
        "key": "stability",
        "label": "Estabilidade & Gestação",
        "min_score": 0,
        "max_score": 249,
        "color": "indigo",
        "icon": "🌱",
        "badge_class": "bg-indigo-500/20 text-indigo-300 border-indigo-500/40",
        "text_color": "text-indigo-300",
        "bar_class": "bg-indigo-400",
        "range_label": "Score < 250/1000",
        "description": "Período de serenidade cósmica, baixa fricção de planetas lentos, planejamento e digestão psíquica."
    }
]


def classify_criticality(score_1000: float) -> Dict[str, Any]:
    """Retorna o nível de criticidade (0-1000) correspondente."""
    for tier in CRITICALITY_TIERS:
        if score_1000 >= tier["min_score"]:
            return tier
    return CRITICALITY_TIERS[-1]


def _format_date_pt(iso_date: str) -> str:
    """Converte YYYY-MM-DD para DD/MM/AAAA."""
    if not iso_date or len(iso_date) < 10:
        return iso_date or ""
    parts = iso_date[:10].split("-")
    if len(parts) == 3:
        return f"{parts[2]}/{parts[1]}/{parts[0]}"
    return iso_date


def determine_default_forecast_window(birth_year: int) -> Tuple[int, int, str]:
    """
    Determina o horizonte padrão (start_year, end_year, window_mode) com base no nascimento:
    - Se a pessoa é contemporânea/viva (birth_year + 100 >= 2026):
      start_year = max(birth_year, 2026)
      end_year = start_year + 24 (ex.: 2026 a 2050)
      window_mode = "prospective"
    - Se é figura histórica (birth_year + 100 < 2026):
      start_year = birth_year + 21
      end_year = birth_year + 45
      window_mode = "historical_prime"
    """
    if birth_year + 100 >= 2026:
        start = max(birth_year, 2026)
        end = start + 24
        return start, end, "prospective"
    else:
        start = birth_year + 21
        end = birth_year + 45
        return start, end, "historical_prime"


def generate_personal_forecast(
    inp: BirthInput,
    profile: Optional[Dict[str, Any]] = None,
    prog: Optional[Dict[str, Any]] = None,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    scope: str = "all",
    reference_jd: Optional[float] = None
) -> Dict[str, Any]:
    """
    Gera o forecast pessoal completo ano a ano com scores dinâmicos, acontecimentos reais
    e categorização aprofundada de criticidade (6 níveis).
    Suporta filtros temporais: 'all' (mostrar tudo) ou 'future' (só o futuro que ainda não aconteceu).
    """
    lang = inp.lang or "pt"
    birth_year = int(inp.date[:4])
    is_historical = (birth_year + 100 < 2026)

    ref_jd = reference_jd if reference_jd is not None else now_jd()
    today_iso = jd_to_iso(ref_jd)[:10]
    current_year = int(today_iso[:4])

    if scope not in ("all", "future"):
        scope = "all"

    # Determinar janela de anos padrão se não fornecida
    def_start, def_end, def_mode = determine_default_forecast_window(birth_year)
    if start_year is None and end_year is None:
        start_year = def_start
        end_year = def_end
        window_mode = def_mode
    elif start_year is not None and end_year is None:
        end_year = start_year + 24
        window_mode = "custom"
    elif start_year is None and end_year is not None:
        start_year = max(birth_year, end_year - 24)
        window_mode = "custom"
    else:
        if start_year > end_year:
            start_year, end_year = end_year, start_year
        window_mode = "custom"

    if is_historical:
        if start_year >= 2026:
            window_mode = "historical_current"
            window_title = f"Projeção Cósmica Atual ({start_year}–{end_year})"
        elif start_year == birth_year + 21 and end_year == birth_year + 45:
            window_mode = "historical_prime"
            window_title = f"Ciclo Biográfico de Auge ({start_year}–{end_year})"
        else:
            window_mode = "historical_cycle"
            window_title = f"Ciclo Biográfico Histórico ({start_year}–{end_year})"
    else:
        window_title = f"Previsão Biográfica Pessoal ({start_year}–{end_year})"

    # Verificar se o perfil fornecido cobre toda a janela solicitada [start_year, end_year]
    profile_covers = False
    if profile is not None:
        p_years = profile.get("domains", {}).get("scored", {}).get("years", [])
        if p_years and p_years[0] <= start_year and p_years[-1] >= end_year:
            profile_covers = True

    if not profile_covers:
        scoped_inp = inp.model_copy(update={"range_from": start_year, "range_to": end_year})
        profile = build_profile(scoped_inp, include_detail=False)
        prog = build_progressions(scoped_inp)
    elif prog is None:
        prog = build_progressions(inp)

    scored_data = profile["domains"]["scored"]
    all_years = scored_data["years"]
    annual_totals = scored_data["annual_total_1000"]
    annual_domains = scored_data["annual_1000"]

    windows = profile["lifetime"]["windows"]
    cycles = profile["lifetime"]["cycles"]
    moon_aspects = prog["moon"].get("aspects", [])
    moon_sign_periods = prog["moon"].get("sign_periods", [])
    moon_house_ingresses = prog["moon"].get("house_ingresses", [])
    sign_ingresses = prog["ingresses"].get("sign_ingresses", [])
    stations = prog["ingresses"].get("stations", [])

    # Indexar janelas de trânsito por ano
    windows_by_year: Dict[int, List[Dict[str, Any]]] = {}
    for w in windows:
        w_start_y = int(w["start"][:4]) if w.get("start") else birth_year
        w_end_y = int(w["end"][:4]) if w.get("end") else birth_year
        for y in range(max(start_year, w_start_y), min(end_year, w_end_y) + 1):
            windows_by_year.setdefault(y, []).append(w)

    # Indexar ciclos por ano
    cycles_by_year: Dict[int, List[Dict[str, Any]]] = {}
    for c in cycles:
        if c.get("start") and c.get("end"):
            c_start_y = int(c["start"][:4])
            c_end_y = int(c["end"][:4])
            for y in range(max(start_year, c_start_y), min(end_year, c_end_y) + 1):
                cycles_by_year.setdefault(y, []).append(c)

    # Indexar aspectos da Lua progredida por ano
    moon_aspects_by_year: Dict[int, List[Dict[str, Any]]] = {}
    for a in moon_aspects:
        if a.get("date"):
            a_y = int(a["date"][:4])
            if start_year <= a_y <= end_year:
                moon_aspects_by_year.setdefault(a_y, []).append(a)

    # Indexar ingressos de casas da Lua progredida por ano
    moon_houses_by_year: Dict[int, List[Dict[str, Any]]] = {}
    for h in moon_house_ingresses:
        if h.get("date"):
            h_y = int(h["date"][:4])
            if start_year <= h_y <= end_year:
                moon_houses_by_year.setdefault(h_y, []).append(h)

    # Indexar ingressos planetários progredidos por ano
    planet_ingresses_by_year: Dict[int, List[Dict[str, Any]]] = {}
    for i in sign_ingresses:
        if i.get("date"):
            i_y = int(i["date"][:4])
            if start_year <= i_y <= end_year:
                planet_ingresses_by_year.setdefault(i_y, []).append(i)

    # Construir linha do tempo pessoal ano a ano com 6 categorias de criticidade
    timeline: List[Dict[str, Any]] = []
    impact_counts = {t["label"]: 0 for t in CRITICALITY_TIERS}

    for y in range(start_year, end_year + 1):
        age = y - birth_year
        idx = all_years.index(y) if y in all_years else -1

        is_past = (y < current_year)
        is_current_year = (y == current_year)
        is_future = (y > current_year)

        # Acontecimentos / Datas Críticas do Ano
        events: List[Dict[str, Any]] = []

        # 1. Trânsitos do ano
        year_windows = windows_by_year.get(y, [])
        for w in year_windows:
            peak_w = float(w.get("intensity_peak") or 0.0)
            score_ev = min(1000, int(peak_w * 1000)) if peak_w <= 1.0 else min(1000, int(peak_w))
            hits = w.get("hits") or []
            year_hits = [h for h in hits if h.get("date", "")[:4] == str(y)]
            if year_hits:
                for h in year_hits:
                    h_date = h["date"]
                    ev_is_future = (h_date >= today_iso)
                    events.append({
                        "date": h_date,
                        "formatted_date": _format_date_pt(h_date),
                        "type": "transit",
                        "type_label": "Trânsito Exato",
                        "title": f"{w.get('transit_symbol', '')} {w.get('transit_name', '')} {w.get('aspect_symbol', '')} {w.get('point_symbol', '')} {w.get('point_name', '')} Natal",
                        "domain_key": w.get("primary_domain", "career"),
                        "domain_label": DOMAIN_TRANSLATIONS.get(w.get("primary_domain"), {}).get("label", "Vida Pessoal"),
                        "domain_icon": DOMAIN_TRANSLATIONS.get(w.get("primary_domain"), {}).get("icon", "🪐"),
                        "domain_color": DOMAIN_TRANSLATIONS.get(w.get("primary_domain"), {}).get("theme_color", "amber"),
                        "tone": w.get("tone", "focus"),
                        "score_1000": max(score_ev, 650),
                        "description": w.get("text") or describe_window(w, lang),
                        "is_retrograde": bool(h.get("retrograde")),
                        "orb": 0.0,
                        "is_future": ev_is_future,
                        "status_label": "Futuro" if ev_is_future else "Concluído"
                    })
            else:
                w_start = w.get("start", f"{y}-01-01")
                w_end = w.get("end", f"{y}-12-31")
                clamped_start = max(w_start, f"{y}-01-01")
                clamped_end = min(w_end, f"{y}-12-31")
                ev_is_future = (clamped_end >= today_iso)
                if clamped_start == f"{y}-01-01" and clamped_end == f"{y}-12-31":
                    fmt_date = f"Ativo ao longo de {y}"
                else:
                    fmt_date = f"{_format_date_pt(clamped_start)} a {_format_date_pt(clamped_end)}"
                events.append({
                    "date": clamped_start,
                    "formatted_date": fmt_date,
                    "type": "transit",
                    "type_label": "Janela de Trânsito",
                    "title": f"{w.get('transit_symbol', '')} {w.get('transit_name', '')} {w.get('aspect_symbol', '')} {w.get('point_symbol', '')} {w.get('point_name', '')} Natal",
                    "domain_key": w.get("primary_domain", "career"),
                    "domain_label": DOMAIN_TRANSLATIONS.get(w.get("primary_domain"), {}).get("label", "Vida Pessoal"),
                    "domain_icon": DOMAIN_TRANSLATIONS.get(w.get("primary_domain"), {}).get("icon", "🪐"),
                    "domain_color": DOMAIN_TRANSLATIONS.get(w.get("primary_domain"), {}).get("theme_color", "amber"),
                    "tone": w.get("tone", "focus"),
                    "score_1000": max(score_ev, 400),
                    "description": w.get("text") or describe_window(w, lang),
                    "is_retrograde": False,
                    "orb": 1.0,
                    "is_future": ev_is_future,
                    "status_label": "Futuro" if ev_is_future else "Concluído"
                })

        # 2. Aspectos da Lua Progredida
        for ma in moon_aspects_by_year.get(y, []):
            ma_date = ma.get("date", f"{y}-06-01")
            ev_is_future = (ma_date >= today_iso)
            events.append({
                "date": ma_date,
                "formatted_date": _format_date_pt(ma_date),
                "type": "progression",
                "type_label": "Lua Progredida",
                "title": f"☽p Lua Progredida {ma.get('aspect_symbol', '')} {ma.get('n_symbol', '')} {ma.get('n_name', '')} Natal",
                "domain_key": "identity" if ma.get("n_id") in ("sun", "asc") else ("relationships" if ma.get("n_id") == "venus" else "career"),
                "domain_label": "Ciclo Emocional & Amadurecimento",
                "domain_icon": "☽",
                "domain_color": "sky",
                "tone": ma.get("family", "flowing"),
                "score_1000": 780,
                "description": f"Aspecto exato da Lua progredida ({ma.get('aspect_name', '')}) ao seu {ma.get('n_name', '')} natal. Marca um momento de amadurecimento emocional profundo e reorientação de prioridades internas.",
                "is_retrograde": False,
                "orb": float(ma.get("orb", 0.0)),
                "is_future": ev_is_future,
                "status_label": "Futuro" if ev_is_future else "Concluído"
            })

        # 3. Ingressos de Casas da Lua Progredida
        for mh in moon_houses_by_year.get(y, []):
            mh_date = mh.get("date", f"{y}-06-01")
            ev_is_future = (mh_date >= today_iso)
            events.append({
                "date": mh_date,
                "formatted_date": _format_date_pt(mh_date),
                "type": "progression",
                "type_label": "Ingresso da Lua Progredida",
                "title": f"☽p Lua Progredida ingressa na Casa {mh.get('to')}",
                "domain_key": "career" if mh.get("to") in (10, 6) else ("relationships" if mh.get("to") in (7, 5) else "resources"),
                "domain_label": f"Foco na Casa {mh.get('to')}",
                "domain_icon": "🏠",
                "domain_color": "indigo",
                "tone": "focus",
                "score_1000": 820,
                "description": f"A Lua progredida entra na Casa {mh.get('to')}. Nos próximos ~2,5 anos, as temáticas desta área da vida tornam-se o foco central de sua energia psíquica e investimentos práticos.",
                "is_retrograde": False,
                "orb": 0.0,
                "is_future": ev_is_future,
                "status_label": "Futuro" if ev_is_future else "Concluído"
            })

        # 4. Ciclos de Vida Monumentais (Saturno, Urano, Quíron, Júpiter)
        for c in cycles_by_year.get(y, []):
            c_start = c.get("start", f"{y}-01-01")
            c_end = c.get("end", f"{y}-12-31")
            clamped_start = max(c_start, f"{y}-01-01")
            clamped_end = min(c_end, f"{y}-12-31")
            c_peak = c.get("peak_date") or clamped_start
            ev_is_future = (c_end >= today_iso)
            if clamped_start == f"{y}-01-01" and clamped_end == f"{y}-12-31":
                fmt_date = f"Ativo em {y}"
            else:
                fmt_date = f"{_format_date_pt(clamped_start)} a {_format_date_pt(clamped_end)}"
            events.append({
                "date": c_peak,
                "formatted_date": fmt_date,
                "type": "cycle",
                "type_label": "Grande Ciclo de Vida",
                "title": c.get("label", "Ciclo Maior"),
                "domain_key": "career" if "saturn" in c.get("key", "") else ("identity" if "uranus" in c.get("key", "") else "purpose_transformation"),
                "domain_label": "Marco de Vida",
                "domain_icon": "⏳",
                "domain_color": "purple",
                "tone": "challenging" if "saturn" in c.get("key", "") or "uranus" in c.get("key", "") else "flowing",
                "score_1000": 950,
                "description": c.get("text") or describe_cycle(c, lang),
                "is_retrograde": False,
                "orb": 0.0,
                "is_future": ev_is_future,
                "status_label": "Futuro" if ev_is_future else "Concluído"
            })

        # Deduplicar e ordenar eventos do ano por data e depois score
        events.sort(key=lambda ev: (ev.get("date", ""), -ev.get("score_1000", 0)))

        future_events = [e for e in events if e.get("is_future")]
        past_events = [e for e in events if not e.get("is_future")]

        # Score geral do ano
        if idx >= 0:
            year_score_1000 = float(annual_totals[idx])
            domain_scores = {k: int(annual_domains[k][idx]) for k in annual_domains}
        else:
            # Fallback dinâmico se o ano não estiver nos índices
            if events:
                top_ev_score = max(e.get("score_1000", 400) for e in events)
                year_score_1000 = min(980.0, float(top_ev_score) * 0.95)
            else:
                year_score_1000 = 350.0 + 40.0 * np.sin(age * 0.4)
            domain_scores = {k: int(year_score_1000 * 0.8) for k in DOMAIN_TRANSLATIONS}

        # Classificação de Criticidade Aprofundada (6 Tiers)
        tier = classify_criticality(year_score_1000)
        impact_level = tier["label"]
        impact_color = tier["color"]
        badge_class = tier["badge_class"]
        tier_icon = tier["icon"]
        impact_counts[impact_level] += 1

        # Domínio mais ativado do ano
        sorted_domains = sorted(domain_scores.items(), key=lambda item: item[1], reverse=True)
        top_domain_key = sorted_domains[0][0] if sorted_domains else "career"
        top_domain_info = DOMAIN_TRANSLATIONS.get(top_domain_key, {"label": top_domain_key, "icon": "⭐", "theme_color": "amber"})

        # Posição da Lua progredida neste ano
        current_moon_sign = ""
        current_moon_text = ""
        mid_year_date = f"{y}-07-01"
        for p in moon_sign_periods:
            if p.get("start", "") <= mid_year_date <= p.get("end", ""):
                current_moon_sign = p.get("sign", "")
                current_moon_text = p.get("text", "")
                break

        # Síntese prospectiva / biográfica do ano
        top_events_titles = [e["title"] for e in events[:3]]
        annual_synthesis = (
            f"Aos {age} anos (em {y}), o período destaca forte ativação em {top_domain_info['label']}. "
            f"Classificação: {tier_icon} {impact_level} ({tier['range_label']}). "
            f"Principais dinâmicas ativas: {', '.join(top_events_titles) if top_events_titles else 'Ciclos estáveis de consolidação'}."
        )

        timeline.append({
            "year": y,
            "age": age,
            "score_1000": round(year_score_1000, 1),
            "score_percent": round(year_score_1000 / 10.0, 1),
            "impact_level": impact_level,
            "impact_color": impact_color,
            "badge_class": badge_class,
            "tier_icon": tier_icon,
            "tier_key": tier["key"],
            "bar_class": tier["bar_class"],
            "tier_description": tier["description"],
            "top_domain": top_domain_info,
            "top_domain_key": top_domain_key,
            "domains": domain_scores,
            "moon_sign": current_moon_sign,
            "moon_text": current_moon_text,
            "events": events,
            "events_count": len(events),
            "is_past": is_past,
            "is_current_year": is_current_year,
            "is_future": is_future,
            "future_events_count": len(future_events),
            "past_events_count": len(past_events),
            "annual_synthesis": annual_synthesis
        })

    # Resumo executivo dos anos mais críticos (Picos Transformadores e Pontos de Virada)
    critical_years = [y["year"] for y in timeline if y["impact_level"] in ("Pico Transformador", "Ponto de Virada")]

    # Anos futuros e passados
    future_years = [y for y in timeline if y["year"] >= current_year]
    past_years = [y for y in timeline if y["year"] < current_year]
    total_future_events = sum(y["future_events_count"] for y in timeline)
    total_past_events = sum(y["past_events_count"] for y in timeline)

    # Gerar Presets de navegação rápida por ciclos biográficos
    preset_windows = []
    base_params = {k: v for k, v in inp.query_params().items() if k not in ("start_year", "end_year")}
    if is_historical:
        p_list = [
            ("Auge Adulto (21–45a)", birth_year + 21, birth_year + 45),
            ("Maturidade (45–70a)", birth_year + 45, min(birth_year + 70, birth_year + 99)),
            ("Juventude (0–25a)", birth_year, birth_year + 24),
            ("Projeção Cósmica Atual", 2026, 2050),
        ]
    else:
        p_list = [
            ("Próximos 25 Anos", 2026, 2050),
            ("Próxima Década", 2026, 2035),
        ]
        if birth_year < 2026:
            p_list.append(("Primeira Fase Adulta", birth_year + 20, min(birth_year + 45, 2050)))

    for plabel, sy, ey in p_list:
        q = dict(base_params, start_year=sy, end_year=ey)
        if scope != "all":
            q["scope"] = scope
        preset_windows.append({
            "label": f"{plabel} ({sy}–{ey})",
            "start": sy,
            "end": ey,
            "active": (sy == start_year and ey == end_year),
            "url": f"/natal/forecast?{urlencode(q)}"
        })

    return {
        "start_year": start_year,
        "end_year": end_year,
        "total_years": len(timeline),
        "impact_counts": impact_counts,
        "criticality_tiers": CRITICALITY_TIERS,
        "critical_years": critical_years,
        "timeline": timeline,
        "domain_translations": DOMAIN_TRANSLATIONS,
        "birth_date": inp.date,
        "current_age": round((ref_jd - profile["chart"]["tjd_ut"]) / 365.2422, 1),
        "today_iso": today_iso,
        "today_formatted": _format_date_pt(today_iso),
        "current_year": current_year,
        "scope": scope,
        "future_years_count": len(future_years),
        "past_years_count": len(past_years),
        "total_future_events": total_future_events,
        "total_past_events": total_past_events,
        "is_historical": is_historical,
        "window_mode": window_mode,
        "window_title": window_title,
        "preset_windows": preset_windows
    }
