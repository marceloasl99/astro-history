"""
Módulo de Correlações Históricas e Diagnóstico/Prognóstico Futuro (2026–2050+).
Cruza os trânsitos com os eventos históricos reais do país e projeta os cenários dos próximos ciclos.
"""

import sqlite3
import os
from typing import Dict, List, Any, Optional
from datetime import datetime

from src.mundane.transits_engine import (
    calculate_transits_for_date,
    get_angular_distance,
    TRANSIT_ASPECTS
)

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "db", "history_astrology.db"))

# Marcos históricos nacionais de referência pré-catalogados
KEY_NATIONAL_HISTORICAL_EVENTS = {
    "BRA": [
        {"title": "Proclamação da República", "date": "1889-11-15", "description": "Fim do Império e deposição de D. Pedro II. Saturno e Urano ativando pontos natais."},
        {"title": "Revolução de 1930", "date": "1930-10-24", "description": "Ascensão de Getúlio Vargas e término da República Velha. Plutão em Câncer em sextil/trígono."},
        {"title": "Golpe Militar de 1964", "date": "1964-03-31", "description": "Conjunção exata de Urano e Plutão em Virgem em conjunção direta sobre o Sol natal do Brasil (14° Virgem)."},
        {"title": "Fim do Regime Militar & Redemocratização", "date": "1985-01-15", "description": "Eleição de Tancredo Neves e transição democrática. Júpiter em Aquário e Urano em Sagitário."},
        {"title": "Plano Real (Estabilização Monetária)", "date": "1994-07-01", "description": "Fim da hiperinflação e criação da nova moeda sob Júpiter em Escorpião em sextil com o Sol natal."},
        {"title": "Jornadas de Junho & Crise Política", "date": "2013-06-17", "description": "Protestos em massa pelo país sob a tensa Quadratura Urano-Plutão ativando signos cardinais e mutáveis."}
    ],
    "USA": [
        {"title": "Início da Guerra Civil Americana", "date": "1861-04-12", "description": "Ataque a Fort Sumter. Retorno exato de Urano em Gêmeos (84 anos após 1776)."},
        {"title": "Terça-Feira Negra (Quebra de 1929)", "date": "1929-10-29", "description": "Início da Grande Depressão sob Saturno em quadratura com planetas natais."},
        {"title": "Ataque a Pearl Harbor (Segunda Guerra)", "date": "1941-12-07", "description": "Segundo Retorno de Urano em Gêmeos coincidindo com a entrada dos EUA na Segunda Guerra Mundial."},
        {"title": "Ataques de 11 de Setembro", "date": "2001-09-11", "description": "Oposição exata Saturno-Plutão alinhada ao eixo Gêmeos-Sagitário da carta dos EUA."},
        {"title": "Primeiro Retorno de Plutão nos EUA", "date": "2022-02-22", "description": "Plutão retorna a 27° de Capricórnio pela primeira vez desde 1776, marcando intensa polarização política e crise institucional."}
    ],
    "FRA": [
        {"title": "Movimento de Maio de 1968", "date": "1968-05-10", "description": "Greve geral e protestos estudantis sob conjunção Urano-Plutão."},
        {"title": "Queda do Muro de Berlim & Reconfiguração Europeia", "date": "1989-11-09", "description": "Alinhamento Saturno-Urano-Netuno em Capricórnio redefinindo o eixo franco-alemão."},
        {"title": "Adoção do Euro", "date": "2002-01-01", "description": "Substituição do Franco Francês sob Júpiter em Câncer."}
    ],
    "GBR": [
        {"title": "Batalha da Grã-Bretanha (Segunda Guerra)", "date": "1940-07-10", "description": "Resistência heroica contra a Luftwaffe sob Saturno e Júpiter em Touro."},
        {"title": "Entrada na Comunidade Econômica Europeia", "date": "1973-01-01", "description": "Ingresso no bloco europeu sob Saturno em Gêmeos."},
        {"title": "Referendo do Brexit", "date": "2016-06-23", "description": "Votação pela saída da União Europeia sob Saturno em Sagitário em quadratura com Netuno."}
    ],
    "RUS": [
        {"title": "Crise Constitucional de Moscou de 1993", "date": "1993-10-04", "description": "Confronto entre Yeltsin e o Parlamento sob Saturno em Aquário e Urano/Netuno em Capricórnio."},
        {"title": "Crise do Rublo de 1998", "date": "1998-08-17", "description": "Moratória e desvalorização da moeda sob trânsitos tensos de Netuno em Aquário."},
        {"title": "Início da Guerra da Ucrânia", "date": "2022-02-24", "description": "Plutão no final de Capricórnio em quadratura e Saturno em Aquário."}
    ],
    "CHN": [
        {"title": "Revolução Cultural", "date": "1966-05-16", "description": "Mobilização de massas sob oposição Saturno-Plutão e Urano."},
        {"title": "Abertura Econômica de Deng Xiaoping", "date": "1978-12-18", "description": "Terceiro Plenário do PCC inaugurando as reformas econômicas sob Júpiter em Leão."},
        {"title": "Entrada na Organização Mundial do Comércio (OMC)", "date": "2001-12-11", "description": "Integração plena na economia globalizada sob trígonos benéficos."}
    ],
    "JPN": [
        {"title": "Bombardeio Atômico de Hiroshima", "date": "1945-08-06", "description": "Detonação da primeira arma nuclear de combate sobre Hiroshima, precipitando o fim da Segunda Guerra Mundial e redefinindo a história militar global."},
        {"title": "Bombardeio Atômico de Nagasaki & Rendição do Japão", "date": "1945-08-09", "description": "Segunda detonação atômica e anúncio da capitulação incondicional do Império do Japão (Gyokuon-hoso)."},
        {"title": "Jogos Olímpicos de Tóquio & Shinkansen", "date": "1964-10-10", "description": "Reintegração pacífica e consagração do milagre econômico e tecnológico pós-guerra."},
        {"title": "Grande Terremoto de Tohoku e Fukushima", "date": "2011-03-11", "description": "Sismo M9.1 seguido de tsunami e colapso nuclear sob trânsitos de Urano no início de Áries em oposição."}
    ],
    "DEU": [
        {"title": "Invasão da Polônia e Início da Segunda Guerra Mundial", "date": "1939-09-01", "description": "Ataque da Alemanha Nazista deflagrando o conflito bélico mais destrutivo da história sob Plutão em Leão e Saturno-Urano em Touro."},
        {"title": "Rendição Incondicional e Fim da Segunda Guerra na Europa", "date": "1945-05-08", "description": "Capitulação do Terceiro Reich e divisão da Alemanha em zonas de ocupação aliada."},
        {"title": "Queda do Muro de Berlim", "date": "1989-11-09", "description": "Ruptura pacífica da fronteira da Guerra Fria e reunificação alemã sob stellium de Saturno, Urano e Netuno em Capricórnio."}
    ]
}

def get_country_historical_correlations(iso_code: str, country_chart: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Recupera eventos históricos do país e calcula os trânsitos exatos que operavam no dia/época.
    Combina eventos pré-catalogados com dados existentes no banco SQLite.
    """
    iso = iso_code.upper()
    events_to_evaluate = []

    # 1. Eventos canônicos documentados
    if iso in KEY_NATIONAL_HISTORICAL_EVENTS:
        events_to_evaluate.extend(KEY_NATIONAL_HISTORICAL_EVENTS[iso])

    # 2. Consultar banco de dados se houver eventos do país
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            country_name_pt = country_chart.get("country_name_pt", "")
            country_name_en = country_chart.get("country_name_en", "")

            # Buscar em events
            c.execute(
                """
                SELECT title, date, consequence FROM events
                WHERE country LIKE ? OR country LIKE ?
                ORDER BY date ASC LIMIT 5
                """,
                (f"%{country_name_pt}%", f"%{country_name_en}%")
            )
            for row in c.fetchall():
                if not any(e["date"] == row[1] for e in events_to_evaluate):
                    events_to_evaluate.append({
                        "title": row[0],
                        "date": row[1],
                        "description": row[2] or ""
                    })
            conn.close()
    except Exception:
        pass

    results = []
    for ev in events_to_evaluate:
        d_str = ev["date"]
        # Permitir eventos históricos cruciais de formação nacional (mesmo ligeiramente anteriores à fundação formal)
        is_key_event = any(e.get("title") == ev.get("title") for e in KEY_NATIONAL_HISTORICAL_EVENTS.get(iso, []))
        if d_str < country_chart["date"] and not is_key_event:
            continue

        try:
            trans_res = calculate_transits_for_date(country_chart, d_str)
            top_transits = trans_res["transits"][:4] # os 4 mais intensos
            results.append({
                "title": ev["title"],
                "date": d_str,
                "description": ev["description"],
                "activation_index_1000": trans_res["activation_index_1000"],
                "top_transits": top_transits
            })
        except Exception:
            continue

    return results

def get_country_future_outlook(country_chart: Dict[str, Any], start_year: int = 2026, end_year: int = 2050) -> Dict[str, Any]:
    """
    Analisa os trânsitos futuros dos grandes ciclos cósmicos (2026–2050)
    sobre os planetas da carta natal da nação e sintetiza prognósticos geopolíticos.
    """
    natal_planets = {p["id"]: p for p in country_chart["planets"]}
    sun_natal = natal_planets.get("sun")
    moon_natal = natal_planets.get("moon")
    mars_natal = natal_planets.get("mars")
    jupiter_natal = natal_planets.get("jupiter")
    saturn_natal = natal_planets.get("saturn")
    uranus_natal = natal_planets.get("uranus")
    pluto_natal = natal_planets.get("pluto")

    # Análise das Grandes Tendências Cósmicas 2026–2050:
    future_cycles = []

    # 1. Plutão em Aquário (2023–2044) - Transforma signos fixos (Aquário, Leão, Touro, Escorpião)
    fixed_activations = []
    for p_id, p in natal_planets.items():
        if p.get("modality") == "Fixo":
            fixed_activations.append(f"{p['name']} natal em {p['sign_name']} ({p['formatted']})")
    
    if fixed_activations:
        future_cycles.append({
            "cycle_name": "Era de Plutão em Aquário (2024–2044)",
            "archetype": "Revolução tecnológica, dissolução de hegemonias e empoderamento de redes sociais",
            "impact_on_country": f"Impacto de transformação direta e estrutural sobre os pontos natais em signos fixos da nação: {', '.join(fixed_activations)}. Exigirá reinvenção profunda das fontes de riqueza, energia e controle institucional."
        })
    else:
        future_cycles.append({
            "cycle_name": "Era de Plutão em Aquário (2024–2044)",
            "archetype": "Transição para sociedade digital e novas redes econômicas",
            "impact_on_country": f"A nação atuará de forma flexível ou indireta frente às grandes tensões globais de poder concentrado, apoiando-se na diplomacia e alianças tecnológicas."
        })

    # 2. Saturno e Netuno em Áries (2025–2028) - Ativa signos cardinais (Áries, Câncer, Libra, Capricórnio)
    cardinal_activations = [f"{p['name']} em {p['sign_name']}" for p in natal_planets.values() if p.get("modality") == "Cardinal"]
    future_cycles.append({
        "cycle_name": "Conjunção Saturno-Netuno em Áries (2025–2028)",
        "archetype": "Ressurgimento de novos mitos nacionais, dissolução de tratados antigos e reconstrução da autoridade",
        "impact_on_country": f"Com a passagem pelo Ponto Vernal (0° Áries), a nação enfrentará redefinições de soberania e liderança. Pontos cardinais sob pressão: {', '.join(cardinal_activations) if cardinal_activations else 'impacto global de transição ideológica'}."
    })

    # 3. Urano em Gêmeos (2025–2033) - Ativa signos mutáveis (Gêmeos, Virgem, Sagitário, Peixes)
    mutable_activations = [f"{p['name']} em {p['sign_name']}" for p in natal_planets.values() if p.get("modality") == "Mutável"]
    sun_in_virgo_or_mutable = sun_natal and sun_natal.get("modality") == "Mutável"
    
    urano_text = f"Ativação acelerada de inovação, mudanças na imprensa, comércio exterior e transportes. Pontos mutáveis tocados: {', '.join(mutable_activations)}."
    if sun_in_virgo_or_mutable:
        urano_text += f" ATENÇÃO: O Sol natal da nação está em signo mutável ({sun_natal['sign_name']}), sinalizando uma grande virada e renovação de liderança política entre 2027 e 2031."

    future_cycles.append({
        "cycle_name": "Urano em Gêmeos (2025–2033)",
        "archetype": "Revolução na inteligência artificial, aviação, comunicação e choques de narrativa",
        "impact_on_country": urano_text
    })

    # 4. Síntese dos 5 Pilares Estratégicos Nacionais (2026–2050)
    pillars = {
        "sovereignty_leadership": {
            "title": "Soberania & Liderança de Estado (Sol)",
            "assessment": f"O Sol nacional está posicionado a {sun_natal['formatted'] if sun_natal else 'N/D'} em {sun_natal['sign_name'] if sun_natal else ''}. Grandes ciclos nos próximos anos exigirão modernização dos governantes e redefinição do pacto de governabilidade."
        },
        "social_cohesion": {
            "title": "Humor Social & População (Lua)",
            "assessment": f"A Lua nacional em {moon_natal['sign_name'] if moon_natal else 'N/D'} reflete um sentimento popular exigente. Momentos de tensão de Saturno/Plutão podem desencadear mobilizações sociais em torno de bem-estar e custo de vida."
        },
        "economy_resources": {
            "title": "Economia, Finanças & Comércio (Júpiter & Vênus)",
            "assessment": f"Júpiter a {jupiter_natal['formatted'] if jupiter_natal else 'N/D'} em {jupiter_natal['sign_name'] if jupiter_natal else ''} indica a vocação produtiva nacional. O país tenderá a expandir parcerias comerciais estratégicas e se beneficiar da transição para novas matrizes produtivas."
        },
        "defense_security": {
            "title": "Segurança, Defesa & Fronteiras (Marte)",
            "assessment": f"Marte a {mars_natal['formatted'] if mars_natal else 'N/D'} em {mars_natal['sign_name'] if mars_natal else ''} denota a prontidão estratégica. Alerta para períodos de trânsitos tensos que estimulam posturas mais assertivas ou atritos geopolíticos regionais."
        },
        "institutions_laws": {
            "title": "Instituições & Ordem Constitucional (Saturno & Plutão)",
            "assessment": f"Saturno natal a {saturn_natal['formatted'] if saturn_natal else 'N/D'} sustenta o arcabouço legal. As décadas de 2020 e 2030 representam um teste de solidez institucional, demandando reformas que desburocratizem o Estado e reforcem a segurança jurídica."
        }
    }

    # Projeção de Anos Chave de Pico de Tensão Futura (2026 a 2040)
    key_future_years = []
    for yr in [2026, 2027, 2028, 2030, 2032, 2035, 2040]:
        t_res = calculate_transits_for_date(country_chart, f"{yr}-07-01")
        if t_res["activation_index_1000"] >= 500 or (t_res["transits"] and t_res["transits"][0]["is_exact"]):
            top = t_res["transits"][0] if t_res["transits"] else None
            key_future_years.append({
                "year": yr,
                "activation_score": t_res["activation_index_1000"],
                "highlight": f"{top['transit_symbol']} {top['transit_planet']} {top['aspect_symbol']} {top['natal_planet']}" if top else "Pico de ativação cíclica",
                "nature": top["aspect_nature"] if top else "neutro"
            })

    return {
        "country_iso": country_chart["country_iso"],
        "future_cycles": future_cycles,
        "pillars": pillars,
        "key_future_years": key_future_years
    }
