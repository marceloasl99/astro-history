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

# Garantir que a raiz do projeto esteja no sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.astro_engine import calculate_event_chart, calculate_chart_tension_1000
from src.correlation_engine import find_similar_events

CACHE_FILE = "/home/astro/data/timeline_1800_2100.json"
OLD_CACHE_FILE = "/home/astro/data/future_simulation_2026_2060.json"
DB_PATH = "/home/astro/db/history_astrology.db"

# Contexto arquetípico dos trânsitos geracionais conhecidos da Astrologia Moderna (1800-2100)
TRANSIT_CONTEXT = {
    # Marcos do Século XIX
    1805: "Batalha de Trafalgar: Plutão e Saturno em tensão marcando o ápice das Guerras Napoleônicas marítimas.",
    1815: "Batalha de Waterloo: Fim da hegemonia napoleônica e estabelecimento da Santa Aliança na Europa.",
    1822: "Independência do Brasil: Conjunção Urano-Netuno em Capricórnio definindo a soberania das novas nações americanas.",
    1848: "A Primavera dos Povos: Urano e Saturno em conjunção detonando revoluções democráticas simultâneas na Europa.",
    1861: "Início da Guerra Civil Americana: Quadratura Urano-Netuno em signos mutáveis, ruptura institucional interna.",
    1889: "Proclamação da República no Brasil: Conjunção Netuno-Plutão em Gêmeos, transição da monarquia agrária para modernidade militar.",
    # Marcos do Século XX
    1914: "Início da Primeira Guerra Mundial: Saturno conjunto a Plutão em Câncer, colapso de impérios centrais.",
    1918: "Gripe Espanhola e Fim da Primeira Guerra: Saturno em Leão com quadratura a Urano em Aquário.",
    1929: "Crash de Wall Street: T-square cardinal envolvendo Saturno, Urano e Plutão, colapso financeiro mundial.",
    1933: "Incêndio do Reichstag e Ascensão Nazista: Quadratura Urano-Plutão em Áries e Câncer, efervescência totalitária.",
    1939: "Início da Segunda Guerra Mundial: Saturno conjunto a Urano em Touro, avanço militar mecanizado sobre a Europa.",
    1945: "Fim da Segunda Guerra e Bomba Atômica: Plutão em Leão ativado por Marte e Saturno em Câncer, inauguração da Era Nuclear.",
    1969: "Pouso na Lua (Apollo 11): Conjunção Júpiter-Urano em Libra e Plutão em Virgem, ápice da corrida espacial.",
    1989: "Queda do Muro de Berlim: Grande Stellium em Capricórnio (Saturno, Urano, Netuno) em oposição a Júpiter.",
    2001: "11 de Setembro: Oposição exata Saturno em Gêmeos a Plutão em Sagitário, início da Guerra ao Terror global.",
    2008: "Colapso do Lehman Brothers: Ingresso de Plutão em Capricórnio e oposição a Marte, implosão do crédito hipotecário.",
    2020: "Pandemia de COVID-19: Conjunção histórica Saturno-Plutão em Capricórnio com Júpiter conjunto.",
    # Horizonte Futuro Século XXI (2026-2100)
    2026: "Conjunção Saturno-Netuno no ponto vernal (0° Áries) e Grande Trígono de Ar Urano em Gêmeos - Plutão em Aquário. Início de um novo megaciclo civilizatório.",
    2027: "Plutão consolida seu trânsito em Aquário com trígono a Urano em Gêmeos. Aceleração extrema da IA, redes descentralizadas e reconfiguração do direito digital.",
    2028: "Saturno entra em Touro em quadratura com Plutão em Aquário. Ajuste e contração de sistemas monetários digitais, commodities e segurança alimentar.",
    2029: "Urano atinge o meio de Gêmeos em oposição ao centro galáctico. Rupturas drásticas em telecomunicações globais, computação quântica e aviação hipersônica.",
    2030: "Netuno avança nos primeiros graus de Áries. Surgimento de novas doutrinas de defesa, idealismo militarizado e corrida por novos recursos energéticos.",
    2031: "Júpiter e Saturno formam aspectos tensos com planetas transpessoais. Revisão de tratados geopolíticos mundiais e reformas na governança da ONU.",
    2032: "Urano ingressa em Câncer. Choques e redefinições em torno de soberania nacional, fronteiras territoriais e autossuficiência de recursos domésticos.",
    2033: "Saturno em Gêmeos forma quadratura com Netuno em Áries. Batalhas de narrativas informacionais, regulação draconiana da internet e cibersegurança estatal.",
    2034: "Plutão no segundo decanato de Aquário. Amadurecimento de novas formas de democracia digital direta e automação integral da produção industrial.",
    2035: "Saturno forma oposição a Plutão (Eixo Leão-Aquário). Tensão geopolítica bipolar aguda, blocos de poder antagônicos e crises de legitimidade executiva.",
    2036: "Pico da tensão da oposição Saturno-Plutão. Reformas radicais nas arquiteturas de alianças militares globais e redivisão de esferas de influência.",
    2037: "Júpiter em trígono com Plutão. Grande expansão de novas matrizes energéticas limpas (fusão nuclear comercial) e reorganização comercial entre continentes.",
    2038: "Urano em Leão. Disrupções em fontes de energia primária, soberania de lideranças fortes e novas formas de autoridade tecnocrática.",
    2039: "Netuno atinge o meio de Áries. Efervescência de movimentos de renovação cultural, ética pioneira e novos conceitos de identidade individual.",
    2040: "Conjunção Júpiter-Saturno. Novo ciclo de 20 anos inaugurando diretrizes de planejamento econômico e metas globais de desenvolvimento pós-carbono.",
    2041: "Plutão no terceiro decanato de Aquário. Consolidação definitiva de redes autônomas descentralizadas e fim do modelo burocrático do século XX.",
    2042: "Saturno em Escorpião. Auditoria profunda de passivos ambientais globais, dívidas soberanas acumuladas e reestruturação de fundos soberanos.",
    2043: "Plutão inicia transição para o signo de Peixes. Deslocamento do foco tecnológico para o desenvolvimento da consciência, bioética e espiritualidade quântica.",
    2044: "Ingresso definitivo de Plutão em Peixes. Dissolução de dogmas materialistas rígidos, avanço nas ciências da mente e reconfiguração das religiões globais.",
    2045: "Urano em Virgem. Revolução biotecnológica radical, reengenharia do trabalho humano pela automação biológica e medicina molecular de precisão.",
    2046: "Urano em Virgem em oposição a Netuno em Peixes. Tensões éticas extremas entre manipulação genética avançada e limites morais da espécie humana.",
    2047: "Saturno em Capricórnio. Retorno institucional severo: códigos jurídicos globais para bioengenharia e reordenação de pactos interestatais rígidos.",
    2048: "Auge da quadratura Urano-Plutão. Rupturas nos paradigmas médicos e farmacêuticos e novos modelos de propriedade intelectual.",
    2049: "Júpiter conjunto a Netuno em Peixes. Renascimento humanitário, grandes tratados de proteção aos oceanos e cooperação ecológica planetária.",
    2050: "Marco do meio do século: Netuno ingressa em Touro e Plutão consolida Peixes. Transição histórica da economia de escassez para economia de abundância circular.",
    2055: "Urano em Escorpião. Saltos drásticos em tecnologias de regeneração celular, fusão homem-máquina e segurança contra bioameaças.",
    2060: "Netuno consolidado em Touro e Plutão no meio de Peixes. Síntese ecológica e harmonização tecnológica global.",
    2065: "Urano em Sagitário em trígono com planetas em Fogo. Nova onda de exploração espacial comercial e expansão lunar/marciana.",
    2070: "Grande alinhamento transpessoal em signos de Ar e Terra. Padronização de governança para inteligências pós-humanas e inteligência artificial geral.",
    2075: "Netuno ingressa em Gêmeos. Revolução na transmissão mental de dados, interfaces neurais de banda larga e reformulação da linguagem humana.",
    2080: "Ingresso histórico de Plutão em Áries (ciclo de 248 anos). Início de uma era de novos pioneirismos bélicos e refundação radical de impérios interestelares.",
    2090: "Saturno e Urano em conjunção polar. Reconfiguração definitiva da ordem geopolítica planetária para a transição do século XXII.",
    2100: "Marco de encerramento do Século XXI: Integração cosmológica de civilização planetária Tipo 1 na Escala Kardashev."
}

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
    """Amostra os 4 pontos sazonais cardinais do ano (Equinócios e Solstícios) + datas específicas de eventos."""
    dates = [
        f"{year}-03-20",  # Equinócio de Outono (Hemisfério Sul) / Primavera (Norte)
        f"{year}-06-21",  # Solstício de Inverno / Verão
        f"{year}-09-22",  # Equinócio de Primavera / Outono
        f"{year}-12-21",  # Solstício de Verão / Inverno
    ]
    if specific_event_dates:
        for ed in specific_event_dates:
            if ed not in dates:
                dates.append(ed)

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

    event_dates = [ev["date"] for ev in hist_events if ev.get("date")]
    charts = sample_year_charts(year, specific_event_dates=event_dates)

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

    # Avaliar todos os gráficos amostrados no ano na escala de 0 a 1000
    scores_1000 = []
    sub_scores_list = []
    for ch in charts:
        s_data = calculate_chart_tension_1000(ch)
        scores_1000.append(s_data["tension_index_1000"])
        sub_scores_list.append(s_data)

    peak_tension = max(scores_1000)
    avg_tension = round(sum(scores_1000) / len(scores_1000), 1)

    # Pegar o gráfico mais intenso para extrair os gatilhos arquetípicos
    peak_idx = scores_1000.index(peak_tension)
    peak_chart = charts[peak_idx]
    peak_sub = sub_scores_list[peak_idx]

    conflict_risk = peak_sub["conflict_risk_index_1000"]
    crisis_risk = peak_sub["crisis_risk_index_1000"]
    tech_innovation = peak_sub["tech_innovation_index_1000"]
    social_transformation = peak_sub["social_transformation_index_1000"]

    # Identificar nível de alerta com base na nova escala 0-1000
    if peak_tension >= 750.0 or conflict_risk >= 780.0:
        alert_level = "Crítico / Ruptura Histórica"
        alert_color = "red"
    elif peak_tension >= 550.0 or conflict_risk >= 600.0:
        alert_level = "Alto / Tensão Intensa"
        alert_color = "orange"
    elif peak_tension >= 350.0:
        alert_level = "Moderado / Transição"
        alert_color = "yellow"
    else:
        alert_level = "Estável / Céu Calmo"
        alert_color = "green"

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

    # Similaridade com a base dos 200 eventos
    sim_data = find_similar_events(peak_chart, top_k=3)
    top_matches = sim_data.get("top_matches", [])
    dom_cat = sim_data.get("dominant_matching_category", "Transformação Cultural")
    resonance = sim_data.get("avg_match_percent", 50.0)

    # Determinar texto explicativo / histórico
    context_note = TRANSIT_CONTEXT.get(year, "")
    
    if has_history:
        # Se for um ano do passado com eventos históricos cadastrados
        main_hist = hist_events[0]
        titles_str = " | ".join([e["title"] for e in hist_events])
        scenario_text = (
            f"FATO HISTÓRICO REAL: {titles_str}. "
            f"Tensão de Pico Cósmico calculada: {peak_tension:.1f}/1000 (Média Anual: {avg_tension:.1f}/1000). "
            f"{context_note} "
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
        # Ano do passado sem evento cadastrado na base dos 200
        top_past_title = top_matches[0]["title"] if top_matches else "Marcos da História"
        scenario_text = (
            f"Ano histórico sem fato específico no catálogo dos 200 marcos. "
            f"Tensão Cósmica de fundo: {peak_tension:.1f}/1000 (Média: {avg_tension:.1f}/1000). "
            f"{context_note or 'Período de continuidade dos ciclos geracionais vigentes.'} "
            f"Padrão celeste mais próximo correlacionado a '{top_past_title}'."
        )
        historical_summary = []
    else:
        # Ano do horizonte futuro (2026–2100)
        top_past_title = top_matches[0]["title"] if top_matches else "Marcos da modernidade"
        top_past_consequence = top_matches[0]["consequence"][:160] if top_matches else ""
        scenario_text = (
            f"Horizonte prospectivo para {year}: Tensão Projetada de {peak_tension:.1f}/1000 "
            f"com {resonance:.1f}% de similaridade com '{dom_cat}'. "
            f"{context_note or 'Ciclos de consolidação evolutiva.'} "
            f"Precedente correlato: '{top_past_title}' (onde ocorreu: \"{top_past_consequence}...\"). "
            f"Desdobramentos potenciais orientados pela atuação de Plutão em {pluto_sign} e Urano em {uranus_sign}."
        )
        historical_summary = []

    # Compatibilidade com campo anterior de 0-100 para evitar quebra em templates legados
    legacy_tension_100 = round(peak_tension / 10.0, 1)

    return {
        "year": year,
        "is_historical": has_history,
        "historical_events": historical_summary,
        "tension_index": legacy_tension_100,  # 0-100 compatível
        "tension_index_1000": peak_tension,  # 0-1000 alta resolução
        "avg_tension_1000": avg_tension,
        "conflict_risk_index": round(conflict_risk / 10.0, 1),
        "conflict_risk_index_1000": conflict_risk,
        "crisis_risk_index": round(crisis_risk / 10.0, 1),
        "crisis_risk_index_1000": crisis_risk,
        "tech_innovation_index": round(tech_innovation / 10.0, 1),
        "tech_innovation_index_1000": tech_innovation,
        "social_transformation_index_1000": social_transformation,
        "resonance_index": round(resonance, 1),
        "alert_level": alert_level,
        "alert_color": alert_color,
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
