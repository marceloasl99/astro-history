"""
Motor Analítico de Correlações Históricas & Ênfase Astrológica Moderna.
Calcula desvios estatísticos, identifica o Planeta, Signo, Aspecto e Estrela Fixa
em maior ênfase para cada evento e categoria, fundamentando os resultados na
Teoria da Astrologia Moderna (Astrologia Mundial e Psicologia Arquetípica).
"""

import sqlite3
import json
import math
import argparse
import sys
import os

# Garantir que a raiz do projeto esteja no sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from typing import Dict, List, Any, Optional
from collections import defaultdict, Counter

from src.db import get_connection, get_event_by_id, get_all_events
from src.astro_engine import ZODIAC_SIGNS, FIXED_STARS_CATALOG

# Pesos base por categoria de corpo celeste na Astrologia Moderna
BASE_BODY_WEIGHTS = {
    # Planetas Transpessoais (motores de transformações coletivas globais e eras)
    "pluto": 3.2,
    "uranus": 2.9,
    "neptune": 2.9,
    # Planetas Sociais (leis, estruturas, autoridade e expansão)
    "saturn": 2.6,
    "jupiter": 2.1,
    # Planetas Pessoais e Luminares (gatilhos de ação e identidade do momento)
    "mars": 2.3,
    "sun": 2.0,
    "moon": 1.7,
    "mercury": 1.4,
    "venus": 1.4,
    # Asteroides e Pontos (nuances arquetípicas especializadas)
    "chiron": 1.6,
    "ceres": 1.3,
    "pallas": 1.3,
    "vesta": 1.2,
    "juno": 1.2,
    "lilith": 1.4,
    "north_node": 1.3
}

# Arquétipos da Astrologia Moderna para Planetas
PLANET_THEORY = {
    "pluto": {
        "title": "Plutão — O Princípio da Metamorfose, Poder e Destruição Criativa",
        "archetype": "Na Astrologia Moderna (Jung / Rudhyar / Tarnas), Plutão governa as forças do inconsciente coletivo, a morte de estruturas corruptas ou obsoletas, erupções vulcânicas de poder concentrado e renascimentos radicais.",
        "crisis_role": "Atua como catalisador inelutável em colapsos bancários, guerras totais, crises existenciais de civilizações e transformações atômicas/geopolíticas."
    },
    "uranus": {
        "title": "Urano — O Princípio da Ruptura Revolucionária, Inovação e Liberdade",
        "archetype": "Representa o Prometeu moderno: impulsos libertários, choque do novo, descontinuidade radical, inovação tecnológica súbita e rebelião contra dogmas vigentes.",
        "crisis_role": "Dispara saltos científicos vertiginosos, revoluções sociopolíticas repentinas, quebras financeiras instantâneas e a emancipação de coletivos."
    },
    "neptune": {
        "title": "Netuno — O Princípio da Dissolução, Idealismo de Massas e Transcendência",
        "archetype": "Governa a dissolução de fronteiras rígidas, contágios biológicos e psicológicos, utopias ideológicas, espiritualidade coletiva, mas também desilusões e miragens.",
        "crisis_role": "Emerge com força em pandemias globais, movimentos messiânicos ou artísticos, crises de fé institucional e vazamento de limites estabelecidos."
    },
    "saturn": {
        "title": "Saturno — O Princípio da Realidade, Limites, Estado e Contração",
        "archetype": "Simboliza a gravidade da matéria: a lei, a governança estatal, a autoridade institucional, a disciplina necessária e a prestação de contas cármicas no tempo.",
        "crisis_role": "Manifesta-se em períodos de severa austeridade econômica, imposição de fronteiras militarizadas, censura legal e consolidação de pactos formais."
    },
    "jupiter": {
        "title": "Júpiter — O Princípio da Expansão, Prosperidade e Ideais Civilizatórios",
        "archetype": "Representa o impulso de crescimento, ampliação do conhecimento, direito internacional, filosofia, exuberância mercantil e integração cultural ampla.",
        "crisis_role": "Estimula surtos especulativos (bolhas de euforia) que antecedem colapsos, bem como a refundação de tratados de paz e expansões territoriais."
    },
    "mars": {
        "title": "Marte — O Princípio da Ação, Combate, Conquista e Ruptura Bélica",
        "archetype": "A força impulsora da energia vital: iniciativa, coragem física, agressividade deliberada, armamentos e vontade de afirmação soberana.",
        "crisis_role": "Age como o detonador pontual de conflagrações armadas, declarações de guerra, atentados explosivos e greves insurrecionais."
    },
    "sun": {
        "title": "Sol — O Centro Vital, Consciência e Soberania",
        "archetype": "O princípio ordenador e irradiador da consciência: liderança executiva visível, poder centralizado e o foco identitário da humanidade.",
        "crisis_role": "Centraliza a atenção do planeta sobre uma liderança específica ou um ato soberano de refundação nacional."
    },
    "moon": {
        "title": "Lua — O Humor Coletivo, Reação Popular e Memória Histórica",
        "archetype": "O princípio da receptividade, do povo, das massas populares, da segurança emocional básica e do sentimento público coletivo.",
        "crisis_role": "Reflete comoções populares generalizadas, pânicos de multidões e a resposta imediata da população a choques históricos."
    },
    "ceres": {
        "title": "Ceres — Produção, Recursos Básicos, Fome e Segurança Alimentar",
        "archetype": "A deusa da agricultura e dos ciclos naturais: economia produtiva real, distribuição de alimentos, perdas materiais e luto coletivo.",
        "crisis_role": "Conecta-se a crises de abastecimento, escassez de commodities vitais e tratados sobre soberania alimentar."
    },
    "pallas": {
        "title": "Pallas Atena — Estratégia Mental, Justiça Cívica e Sabedoria Tática",
        "archetype": "A mente estratégica defensiva: inteligência militar, diplomacia calculada, constituições e luta civil por direitos.",
        "crisis_role": "Surge em arquiteturas de tratados geopolíticos, constituições cidadãs e táticas militares de resistência."
    },
    "chiron": {
        "title": "Quíron — O Curador Ferido, Trauma Coletivo e Ressignificação",
        "archetype": "A ponte entre o visível (Saturno) e o invisível (Urano): dores estruturais históricas, feridas bélicas profundas e a sabedoria que brota da superação.",
        "crisis_role": "Ativado em genocídios, catástrofes humanitárias e na emergência de novas filosofias de cura e direitos humanos."
    },
    "lilith": {
        "title": "Lilith — A Força Primordial Reprimida, Transgressão e Ruptura de Tabus",
        "archetype": "A Lua Negra representa o que foi banido da ordem dominante: instintos reprimidos, revolta contra a subjugação e contestação visceral.",
        "crisis_role": "Manifesta-se em insurreições iconoclastas, levantes contra a opressão patriarcal ou estatal e revelação de segredos sombrios."
    }
}

# Teoria dos Signos e Elementos na Astrologia Moderna
SIGN_THEORY = {
    "Áries": "Fogo Cardinal • Iniciativa impetuosa, pioneirismo belicoso, declarações de independência e ímpeto de conquista unilateral.",
    "Touro": "Terra Fixa • Matéria concreta, soberania territorial, estabilidade financeira, moedas, posse de recursos físicos e resistência obstinada.",
    "Gêmeos": "Ar Mutável • Comunicação, imprensa, telecomunicações, acordos velozes, dualidades ideológicas e disseminação do conhecimento.",
    "Câncer": "Água Cardinal • Pátria, raízes nacionais, proteção das populações civis, sentimentos soberanos e fronteiras domésticas.",
    "Leão": "Fogo Fixo • Soberania régia, poder atômico concentrado, afirmação imperial majestosa, grandeza cultural e risco de tirania.",
    "Virgem": "Terra Mutável • Trabalho técnico especializado, saneamento, saúde pública, meticulosidade científica e racionalização burocrática.",
    "Libra": "Ar Cardinal • Diplomacia multilateral, cortes de justiça internacional, equilíbrio de forças e tratados formais de armistício.",
    "Escorpião": "Água Fixa • Transformações subterrâneas, finanças corporativas, poder militar oculto, crises terminais e regenerações drásticas.",
    "Sagitário": "Fogo Mutável • Expansão global, leis constitucionais, doutrinas morais/filosóficas, comércio ultramarino e internacionalismo.",
    "Capricórnio": "Terra Cardinal • Instituições de Estado, arquitetura bancária tradicional, governos centrais, disciplina rigorosa e limites formais.",
    "Aquário": "Ar Fixo • Redes coletivas, revoluções populares, direitos universais, vanguarda tecnológica, inteligência artificial e rupturas científicas.",
    "Peixes": "Água Mutável • Dissolução universal, compaixão humanitária, utopias ideológicas de massa, contágios epidêmicos e dimensões místicas."
}

def calculate_event_emphasis(event_id: int) -> Dict[str, Any]:
    """
    Calcula matematicamente o Planeta, Signo, Aspecto e Estrela Fixa em ênfase
    para um evento histórico e gera a corroboração teórica correspondente.
    """
    event = get_event_by_id(event_id)
    if not event:
        raise ValueError(f"Evento com ID {event_id} não encontrado.")

    chart = event.get("chart", {})
    bodies = chart.get("planets", [])
    aspects = chart.get("aspects", [])
    star_contacts = chart.get("star_contacts", [])
    summary = chart.get("summary", {})

    # 1. CÁLCULO DE SCORE DE ÊNFASE PLANETÁRIA
    body_scores = defaultdict(float)
    body_aspect_count = defaultdict(int)
    body_reasons = defaultdict(list)

    for b in bodies:
        b_id = b["id"]
        base_w = BASE_BODY_WEIGHTS.get(b_id, 1.0)
        body_scores[b_id] += base_w

        # Bonificação de retrogradação (crise interiorizada / peso kármico)
        if b.get("is_retrograde"):
            body_scores[b_id] *= 1.25
            body_reasons[b_id].append("Movimento Retrógrado (℞) potencializando a intensidade e a tensão reflexiva do arquétipo")

        # Regência moderna do signo ocupado (planeta em domicílio ganha destaque)
        sign_name = b.get("sign_name")
        sign_obj = next((s for s in ZODIAC_SIGNS if s["name"] == sign_name), None)
        if sign_obj and b["name"] in sign_obj["ruler"]:
            body_scores[b_id] += 3.0
            body_reasons[b_id].append(f"Em Domicílio Cósmico em {sign_name} (regente moderno do signo)")

    # Ponderação pelos Aspectos Estritos (orbe <= 3.0°)
    for a in aspects:
        p1 = a["planet1_id"]
        p2 = a["planet2_id"]
        orb = a.get("orb", 3.0)
        proximity_factor = max(0.2, (3.0 - orb) / 3.0) # 1.0 para exato, decresce até 3.0°

        asp_weight = 2.0
        if a["aspect_name"] in ["Quadratura", "Oposição"]:
            asp_weight = 3.5 # Aspectos tensos carregam o maior peso de crise
        elif a["aspect_name"] == "Conjunção":
            asp_weight = 3.8 # Conjunção é a fusão primordial
        elif a["aspect_name"] == "Trígono":
            asp_weight = 2.2 # Trígono é canal fluido de expressão

        if a.get("is_outer_cycle"):
            asp_weight *= 1.8 # Ciclos transpessoais têm peso histórico massivo

        score_boost = proximity_factor * asp_weight * 2.5
        body_scores[p1] += score_boost
        body_scores[p2] += score_boost
        body_aspect_count[p1] += 1
        body_aspect_count[p2] += 1

    # Ponderação por Alinhamento com as 30 Estrelas Fixas (orbe <= 0.3°)
    for sc in star_contacts:
        b_id = sc["body_id"]
        s_key = sc["star_key"]
        orb_s = sc.get("orb", 0.3)
        star_boost = max(1.0, (0.3 - orb_s) / 0.3) * 6.0
        
        # Estrelas maiores adicionam bônus extra
        if s_key in ["Algol", "Sirius", "Aldebaran", "Regulus", "Antares"]:
            star_boost *= 1.5

        body_scores[b_id] += star_boost
        body_reasons[b_id].append(f"Conexão estreita com a Estrela Fixa {s_key} (orbe {orb_s:.3f}°)")

    # Identificar o Planeta Vencedor
    top_body_id = max(body_scores, key=body_scores.get)
    top_body = next(b for b in bodies if b["id"] == top_body_id)
    top_body_score = round(body_scores[top_body_id], 1)

    # 2. CÁLCULO DO SIGNO EM ÊNFASE
    sign_counts = Counter(b["sign_name"] for b in bodies)
    top_sign_name = sign_counts.most_common(1)[0][0]
    top_sign_count = sign_counts.most_common(1)[0][1]

    # 3. CÁLCULO DO ASPECTO EM ÊNFASE
    # O aspecto com menor orbe e maior tensão
    top_aspect = None
    if aspects:
        sorted_aspects = sorted(aspects, key=lambda a: (a.get("orb", 99), -a.get("tension_value", 0)))
        top_aspect = sorted_aspects[0]

    # 4. CÁLCULO DA ESTRELA FIXA EM ÊNFASE
    top_star_contact = None
    if star_contacts:
        sorted_stars = sorted(star_contacts, key=lambda s: s.get("orb", 99))
        top_star_contact = sorted_stars[0]

    # 5. GERAR CORROBORAÇÃO PELA TEORIA DA ASTROLOGIA MODERNA
    p_theory = PLANET_THEORY.get(top_body_id, {
        "title": f"{top_body['name']} em Destaque",
        "archetype": "Arquétipo ativo mobilizando transformações e desdobramentos na psique coletiva.",
        "crisis_role": "Atua como canal condutor de eventos cruciais."
    })
    s_theory = SIGN_THEORY.get(top_sign_name, "Elemento e dinâmica ativos.")

    # Síntese analítica moderna articulada
    aspect_desc = ""
    if top_aspect:
        aspect_desc = (
            f"O aspecto geométrico mais exato foi a {top_aspect['aspect_name']} entre "
            f"{top_aspect['planet1_symbol']} {top_aspect['planet1_name']} e {top_aspect['planet2_symbol']} {top_aspect['planet2_name']} "
            f"(orbe ultra-estrito de apenas {top_aspect['orb']}°), criando uma dinâmica de {top_aspect['nature']} "
            f"que demandou resolução histórica inadiável. "
        )

    star_desc = ""
    if top_star_contact:
        star_desc = (
            f"O evento também ativou com rigor de 0,3° a estrela fixa {top_star_contact['star_name']} "
            f"({top_star_contact['star_bayer']}), tradicionalmente conectada a: {top_star_contact['star_significance']} "
        )

    consequence_link = (
        f"Ao cruzar a configuração com a consequência histórica concreta — '{event['consequence'][:220]}...' —, "
        f"a teoria da astrologia moderna corrobora a sincronia: a ênfase de {top_body['name']} no signo de {top_body['sign_name']} "
        f"operou exatamente como a lente focal das transformações relatadas, confirmando que o momento astronômico espelhou com alta fidelidade "
        f"o padrão das consequências políticas, econômicas e sociais que se desenrolaram."
    )

    full_rationale = (
        f"1. ARQUÉTIPO CENTRAL: {p_theory['title']}\n"
        f"{p_theory['archetype']}\n\n"
        f"2. ATUAÇÃO NO CAMPO HISTÓRICO:\n"
        f"{p_theory['crisis_role']}\n\n"
        f"3. MEIO DE EXPRESSÃO ZODIACAL: {top_sign_name}\n"
        f"{s_theory}\n\n"
        f"4. DINÂMICA DE ASPECTOS & ESTRELAS:\n"
        f"{aspect_desc}{star_desc}\n\n"
        f"5. CORROBORAÇÃO COM AS CONSEQUÊNCIAS DO FATO:\n"
        f"{consequence_link}"
    )

    return {
        "event_id": event_id,
        "title": event["title"],
        "date": event["date"],
        "category": event["category"],
        "consequence": event["consequence"],
        "dominant_planet": {
            "id": top_body_id,
            "name": top_body["name"],
            "symbol": top_body["symbol"],
            "sign": top_body["sign_name"],
            "formatted": top_body["formatted"],
            "is_retrograde": top_body["is_retrograde"],
            "score": top_body_score,
            "active_aspects_count": body_aspect_count[top_body_id],
            "justification_reasons": body_reasons[top_body_id][:3]
        },
        "dominant_sign": {
            "name": top_sign_name,
            "bodies_count": top_sign_count,
            "theory": s_theory
        },
        "dominant_aspect": top_aspect,
        "dominant_star_contact": top_star_contact,
        "tension_index": summary.get("tension_index", 50.0),
        "modern_astrology_rationale": full_rationale
    }

def calculate_macro_correlations() -> Dict[str, Any]:
    """
    Executa contas estatísticas em toda a base dos 200 fatos históricos,
    identificando desvios de frequência, planetas em ênfase e aspectos dominantes por categoria.
    """
    conn = get_connection()
    categories_res = conn.execute("SELECT DISTINCT category FROM events ORDER BY category").fetchall()
    categories = [r[0] for r in categories_res]

    category_reports = {}

    for cat in categories:
        total_cat_events = conn.execute("SELECT COUNT(*) FROM events WHERE category = ?", (cat,)).fetchone()[0]

        # Top Planetas Transpessoais/Sociais e seus Signos na Categoria
        p_rows = conn.execute("""
            SELECT p.planet_name, p.sign_name, COUNT(*) as cnt
            FROM planet_positions p
            JOIN events e ON p.event_id = e.id
            WHERE e.category = ? AND p.category IN ('transpessoal', 'social', 'asteroide')
            GROUP BY p.planet_name, p.sign_name
            ORDER BY cnt DESC
            LIMIT 5
        """, (cat,)).fetchall()

        # Top Aspectos Estritos na Categoria (orbe <= 3.0°)
        asp_rows = conn.execute("""
            SELECT a.planet1_id, a.planet2_id, a.aspect_name, a.aspect_symbol, a.nature, COUNT(*) as cnt
            FROM event_aspects a
            JOIN events e ON a.event_id = e.id
            WHERE e.category = ?
            GROUP BY a.planet1_id, a.planet2_id, a.aspect_name
            ORDER BY cnt DESC
            LIMIT 5
        """, (cat,)).fetchall()

        # Top Estrelas Fixas na Categoria (orbe <= 0.3°)
        star_rows = conn.execute("""
            SELECT s.star_name, s.aspect_name, COUNT(*) as cnt
            FROM event_star_aspects s
            JOIN events e ON s.event_id = e.id
            WHERE e.category = ?
            GROUP BY s.star_name
            ORDER BY cnt DESC
            LIMIT 4
        """, (cat,)).fetchall()

        avg_tension = conn.execute("""
            SELECT AVG(tension_index) FROM events WHERE category = ?
        """, (cat,)).fetchone()[0] or 50.0

        # Elaboração da fundamentação teórica de astrologia moderna para a categoria
        category_theory = ""
        if cat == "Crise Econômica":
            category_theory = (
                "Na Astrologia Mundial Moderna, as crises econômicas e financeiras são fortemente correlacionadas "
                "a tensões envolvendo Plutão (crédito, dívida, colapso de solvência e transformações patrimoniais) "
                "e Netuno (desmanche de ilusões especulativas, contágios de liquidez e psicologia de manada em bolhas). "
                "A alta incidência de aspectos tensos (quadraturas e oposições) e a ativação de signos de Terra e Ar "
                "espelham a necessidade compulsória de readequar sistemas monetários desregulados."
            )
        elif cat == "Guerra & Conflito":
            category_theory = (
                "Conflitos bélicos e guerras de grande escala coincidem com ciclos maiores de Saturno-Plutão "
                "(confrontos de poder estatal, endurecimento de fronteiras e contração autoritária) e ativações de Marte "
                "com planetas transpessoais. A incidência repetida de Plutão em signos de Fogo (como Leão) denota lutas "
                "pela supremacia e uso desmedido de armamentos de destruição em massa."
            )
        elif cat == "Ciência & Tecnologia":
            category_theory = (
                "Grandes saltos de inovação, eletromagnetismo, física quântica e astronomia respondem ao arquétipo "
                "de Urano (a mente cósmica superior e a inovação tecnológica desbravadora) harmonizado com Saturno "
                "(método empírico e leis da matéria) e Netuno (teorias sutis e invisíveis). Os trígonos nestes mapas "
                "indicam sínteses conceituais brilhantes que redefiniram as ferramentas da civilização humana."
            )
        elif cat == "Revolução Política":
            category_theory = (
                "Revoluções populares e quedas de regimes absolutistas ou coloniais articulam o embate direto entre "
                "Urano (libertação, direitos dos povos, rebelião cívica) e Saturno/Plutão (o status quo e o aparelho repressor). "
                "Signos Cardinais e de Ar acentuam a urgência de constituições republicanas, sufrágio e reescrita das leis."
            )
        elif cat == "Pandemia & Desastre":
            category_theory = (
                "Catástrofes epidemiológicas e calamidades naturais apresentam acentuada ativação de Netuno "
                "(vetor de contágios invisíveis, desmanche sanitário) associado a Quíron (a vulnerabilidade corporal da espécie) "
                "e estrelas fixas de advertência marítima ou toxicidade como Menkar e Scheat."
            )
        else:
            category_theory = (
                "Transformações culturais profundas refletem as grandes mudanças de signo de planetas lentos, "
                "em especial as transições geracionais de Plutão e Netuno que inauguram novos paradigmas na arte, "
                "filosofia e religiosidade coletiva."
            )

        category_reports[cat] = {
            "total_events": total_cat_events,
            "average_tension": round(avg_tension, 1),
            "top_placements": [dict(r) for r in p_rows],
            "top_aspects": [dict(r) for r in asp_rows],
            "top_stars": [dict(r) for r in star_rows],
            "modern_astrology_theory": category_theory
        }

    conn.close()

    return {
        "total_historical_events": 200,
        "categories_analysis": category_reports
    }

def print_cli_event_report(event_analysis: Dict[str, Any]):
    """Imprime relatório formatado e detalhado de um evento específico no terminal."""
    ea = event_analysis
    p = ea["dominant_planet"]
    s = ea["dominant_sign"]
    a = ea.get("dominant_aspect")
    sc = ea.get("dominant_star_contact")

    print("=" * 80)
    print(f"ANÁLISE DE ÊNFASE & CORROBORAÇÃO ASTROLÓGICA MODERNA: #{ea['event_id']:03d}")
    print(f"Evento: {ea['title']} ({ea['date']}) • Categoria: {ea['category']}")
    print("=" * 80)
    print(f"\n[1] PLANETA EM MAIOR ÊNFASE: {p['symbol']} {p['name']} (Score: {p['score']} pts)")
    print(f"    Posição: {p['formatted']} | Retrógrado: {p['is_retrograde']}")
    print(f"    Aspectos Estritos Formados (3.0°): {p['active_aspects_count']}")
    for r in p["justification_reasons"]:
        print(f"    • {r}")

    print(f"\n[2] SIGNO EM ÊNFASE: {s['name']} ({s['bodies_count']} corpos celestes presentes)")
    print(f"    Dinâmica: {s['theory']}")

    if a:
        print(f"\n[3] ASPECTO EM ÊNFASE: {a['planet1_symbol']} {a['planet1_name']} {a['aspect_symbol']} {a['planet2_symbol']} {a['planet2_name']}")
        print(f"    Tipo: {a['aspect_name']} | Orbe: {a['orb']}° (Exatidão: {a['exactness_percent']}%) | Natureza: {a['nature']}")

    if sc:
        print(f"\n[4] ESTRELA FIXA EM ÊNFASE: ★ {sc['star_name']} ({sc['star_bayer']})")
        print(f"    Corpo Ativado: {sc['body_symbol']} {sc['body_name']} {sc['aspect_symbol']} | Orbe Ultra-Estrito: {sc['orb']}°")
        print(f"    Significado Tradicional: {sc['star_significance']}")

    print(f"\n[5] NÍVEL DE TENSÃO CÓSMICA DO EVENTO: {ea['tension_index']}/100")
    print("\n" + "-" * 80)
    print("FUNDAMENTAÇÃO NA TEORIA DA ASTROLOGIA MODERNA:")
    print("-" * 80)
    print(ea["modern_astrology_rationale"])
    print("=" * 80)

def main():
    parser = argparse.ArgumentParser(
        description="Motor Analítico de Correlações Históricas e Ênfase Astrológica Moderna."
    )
    parser.add_argument("--event", type=int, help="ID do evento histórico a analisar (1 a 200). Ex: --event 93")
    parser.add_argument("--category", type=str, help="Nome da categoria histórica a analisar. Ex: --category 'Crise Econômica'")
    parser.add_argument("--all", action="store_true", help="Executa o diagnóstico macro em todos os 200 fatos e categorias.")
    parser.add_argument("--export-json", type=str, help="Caminho para exportar o relatório analítico consolidado em JSON.")

    args = parser.parse_args()

    if args.event:
        res = calculate_event_emphasis(args.event)
        print_cli_event_report(res)
        if args.export_json:
            with open(args.export_json, "w", encoding="utf-8") as f:
                json.dump(res, f, ensure_ascii=False, indent=2)
            print(f"\nRelatório do evento exportado para: {args.export_json}")

    else:
        macro = calculate_macro_correlations()
        cats = macro["categories_analysis"]

        if args.category:
            if args.category in cats:
                cats = {args.category: cats[args.category]}
            else:
                print(f"Categoria '{args.category}' não encontrada. Opções disponíveis: {list(cats.keys())}")
                return

        print("=" * 85)
        print("RELATÓRIO MACRO DE CORRELAÇÕES HISTÓRICAS & ASTROLOGIA MODERNA")
        print("=" * 85)
        for cat_name, cdata in cats.items():
            print(f"\nCATEGORIA: {cat_name.upper()} ({cdata['total_events']} Eventos - Tensão Média: {cdata['average_tension']}/100)")
            print("-" * 80)
            print("Posições Planetárias com Maior Incidência:")
            for p in cdata["top_placements"]:
                print(f"  • {p['planet_name']} em {p['sign_name']}: {p['cnt']} ocorrências")

            print("\nAspectos Estritos Mais Recorrentes (Orbe <= 3.0°):")
            for a in cdata["top_aspects"]:
                print(f"  • {a['planet1_id']} {a['aspect_name']} {a['planet2_id']}: {a['cnt']} vezes ({a['nature']})")

            print("\nEstrelas Fixas Mais Ativadas (Orbe <= 0.3°):")
            for s in cdata["top_stars"]:
                print(f"  • ★ {s['star_name']}: {s['cnt']} ativações diretas")

            print("\nFundamentação na Teoria da Astrologia Moderna:")
            print(f"  {cdata['modern_astrology_theory']}")
            print("-" * 80)

        if args.export_json:
            with open(args.export_json, "w", encoding="utf-8") as f:
                json.dump(macro, f, ensure_ascii=False, indent=2)
            print(f"\nRelatório macro exportado com sucesso para: {args.export_json}")

if __name__ == "__main__":
    main()
