"""
Motor de Precedentes e Analogias Históricas para Previsão Futura (2026–2050).
Conecta cada trânsito planetário futuro a fatos históricos reais ocorridos no passado,
gerando diagnósticos analíticos e geopolíticos empiricamente fundamentados.
"""

from typing import Dict, List, Any, Optional
from datetime import date

from src.mundane.transits_engine import (
    calculate_transits_for_date,
    TRANSIT_ASPECTS
)
from src.mundane.historical_analyzer import get_country_analyzed_history

# Mapeamento arquetípico de precedentes mundiais para trânsitos raros/inéditos
GLOBAL_ARCHETYPAL_PRECEDENTS = {
    "PLUTO_SUN": {
        "theme": "Crise de Soberania e Reinvenção do Poder de Estado",
        "historical_analogy": "Revolução Francesa (1789) e Queda de Dinastias Imperiais",
        "lesson": "Colapso de modelos centralizados antigos e refundação da autoridade nacional."
    },
    "PLUTO_MARS": {
        "theme": "Mobilização Bélica Extrema e Conflito Existencial",
        "historical_analogy": "Primeira e Segunda Guerras Mundiais / Guerra do Paraguai (1864)",
        "lesson": "Tensão máxima nas forças de segurança, exigindo coesão estratégica e modernização militar."
    },
    "URANUS_SUN": {
        "theme": "Ruptura Súbita no Poder Executivo e Revoluções Institucionais",
        "historical_analogy": "Golpe Militar de 1964 (Brasil) / Guerra Civil Americana (1861)",
        "lesson": "Choque imprevisto de modelos políticos, instabilidade na liderança e aceleração tecnológica."
    },
    "SATURN_JUPITER": {
        "theme": "Contração de Crédito, Austeridade e Reestruturação Financeira",
        "historical_analogy": "Grande Depressão de 1929 / Crise da Dívida e Moratória de 1987",
        "lesson": "Necessidade de disciplina fiscal severa, renegociação de passivos e corte de gastos excessivos."
    },
    "NEPTUNE_SUN": {
        "theme": "Dissolução Ideológica, Escândalos e Perda de Clareza Política",
        "historical_analogy": "Fim da União Soviética (1991) / Crise de Watergate (1974)",
        "lesson": "Crise de legitimidade moral nos governantes e surgimento de novos mitos ou utopias sociais."
    },
    "SATURN_SUN": {
        "theme": "Sobrecarga Institucional, Teste de Realidade e Prestação de Contas",
        "historical_analogy": "Processos de Impeachment (1992 / 2016) e Crises Constitucionais",
        "lesson": "O governo enfrenta resistência popular, freios parlamentares e auditoria implacável da sociedade."
    }
}

def generate_grounded_future_forecast(country_chart: Dict[str, Any], start_year: int = 2026, end_year: int = 2050) -> List[Dict[str, Any]]:
    """
    Gera previsões futuras fundamentadas em fatos históricos reais para as janelas de 2026 a 2050.
    Identifica os trânsitos exatos futuros e busca precedentes correspondentes na história do país.
    """
    country_history = get_country_analyzed_history(country_chart)
    forecasts = []

    # Amostragem de janelas chave de 2026 a 2050
    key_evaluation_points = [
        {"year_range": "2026–2027", "sample_date": "2026-07-01", "era_context": "Ingresso de Saturno e Netuno em Áries (Ponto Vernal 0°)"},
        {"year_range": "2028–2030", "sample_date": "2029-01-01", "era_context": "Urano em Gêmeos em quadratura com signos mutáveis & Plutão em Aquário"},
        {"year_range": "2031–2033", "sample_date": "2032-07-01", "era_context": "Avanço de Plutão em Aquário e conjunções de Saturno em Touro"},
        {"year_range": "2034–2036", "sample_date": "2035-01-01", "era_context": "Júpiter e Saturno ativando ciclos sociais nos signos de Ar"},
        {"year_range": "2038–2040", "sample_date": "2039-07-01", "era_context": "Clímax da Era de Plutão em Aquário e novas alianças geopolíticas"}
    ]

    for pt in key_evaluation_points:
        t_res = calculate_transits_for_date(country_chart, pt["sample_date"])
        transits = t_res.get("transits", [])

        # Filtra trânsitos de planetas lentos
        slow_transits = [t for t in transits if t["transit_planet_id"] in ["pluto", "neptune", "uranus", "saturn", "jupiter", "mars"]]
        if not slow_transits:
            continue

        # Trânsito protagonista da janela
        protagonist = slow_transits[0]
        t_id = protagonist["transit_planet_id"]
        n_id = protagonist["natal_planet_id"]
        pair_key = f"{t_id.upper()}_{n_id.upper()}"

        # 1. Busca Precedente Histórico do Próprio País
        matched_precedents = []
        for h in country_history:
            # Verifica se algum trânsito do evento histórico envolvia o mesmo par arquetípico
            for h_trans in h.get("top_transits", []):
                h_pair = f"{h_trans['transit_planet_id'].upper()}_{h_trans['natal_planet_id'].upper()}"
                if h_pair == pair_key or (h_trans["transit_planet_id"] == t_id and h_trans["aspect_nature"] == protagonist["aspect_nature"]):
                    matched_precedents.append({
                        "event_title": h["title"],
                        "date": h["date"],
                        "category": h["category"],
                        "description": h["description"],
                        "source": h["historical_source"],
                        "past_transit": f"{h_trans['transit_symbol']} {h_trans['transit_planet']} {h_trans['aspect_symbol']} {h_trans['natal_planet']} Natal ({h_trans['formatted_orb']})",
                        "past_score": h["activation_index_1000"]
                    })
                    break

        # Se encontrou precedente nacional:
        if matched_precedents:
            best_prec = matched_precedents[0]
            precedent_type = "Nacional Direto"
            precedent_headline = f"{best_prec['event_title']} ({best_prec['date'][:4]})"
            precedent_narrative = (
                f"No passado de {country_chart['country_name_pt']}, quando configuração similar de {protagonist['transit_planet']} sobre {protagonist['natal_planet']} natal esteve ativa "
                f"em {best_prec['date']}, ocorreu o seguinte fato histórico: '{best_prec['event_title']}' ({best_prec['category']}). "
                f"{best_prec['description']} (Fonte: {best_prec['source']})."
            )
            future_synthesis = (
                f"A repetição desse ciclo na janela {pt['year_range']} ativa padrões arquetípicos correlatos. "
                f"Espera-se pressão sobre {protagonist['natal_planet']} natal ({country_chart['country_name_pt']}), demandando postura preventiva "
                f"em relação a {best_prec['category'].lower()} e ajustes estruturais de governança para mitigar vulnerabilidades institucionais históricas."
            )
        else:
            # Precedente global comparado
            precedent_type = "Arquetípico Comparado"
            global_info = GLOBAL_ARCHETYPAL_PRECEDENTS.get(pair_key, {
                "theme": f"Ciclo de {protagonist['transit_planet']} sobre {protagonist['natal_planet']}",
                "historical_analogy": "Grandes ciclos de transformação geopolítica moderna",
                "lesson": "Necessidade de renovação institucional e adaptação às novas realidades de poder global."
            })
            precedent_headline = f"{global_info['theme']}"
            precedent_narrative = (
                f"Trata-se de um ciclo raro para {country_chart['country_name_pt']}. Na história mundial comparada, a ativação de {protagonist['transit_planet']} em {protagonist['aspect_name']} com {protagonist['natal_planet']} "
                f"manifestou-se em eventos análogos como: '{global_info['historical_analogy']}', cuja lição central foi: {global_info['lesson']}."
            )
            future_synthesis = (
                f"Para a janela {pt['year_range']}, a projeção aponta para o tema: '{global_info['theme']}'. "
                f"O país será estimulado a consolidar novas alianças e atualizar seu arcabouço normativo para enfrentar transformações estruturais inevitáveis."
            )

        forecasts.append({
            "year_range": pt["year_range"],
            "sample_date": pt["sample_date"],
            "era_context": pt["era_context"],
            "activation_index_1000": t_res["activation_index_1000"],
            "future_transit": {
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
            "precedent_type": precedent_type,
            "precedent_headline": precedent_headline,
            "precedent_narrative": precedent_narrative,
            "grounded_forecast": future_synthesis,
            "matched_historical_events": matched_precedents[:2]
        })

    return forecasts
