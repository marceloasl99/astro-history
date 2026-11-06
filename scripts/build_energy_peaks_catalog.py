"""
Script Avançado de Compilação do Catálogo de Picos de Energia Cósmica (2026–2060).
Gera dossiês estratégicos completos, inteligência prospectiva geopolítica detalhada,
matriz comparativa de risco (anos x países) e isolamento rigoroso dos picos de alta energia.
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
    {
        "iso": "BRA",
        "name_pt": "Brasil",
        "name_en": "Brazil",
        "flag": "🇧🇷",
        "capital": "Brasília",
        "foundation_event": "Independência do Brasil (Grito do Ipiranga)",
        "foundation_date": "1822-09-07",
        "strategic_summary": "O Brasil enfrenta uma década decisiva (2026–2035) com a ativação de Urano e Saturno sobre a carta de 1822. O país será pressionado pela governança ambiental global e soberania energética amazônica em 2026, passando por um choque fiscal e de dívida em 2028 (Retorno de Saturno), culminando em tensão institucional extrema entre os Três Poderes em 2029.",
        "critical_years": [2026, 2028, 2029, 2034],
        "vulnerability": "Urano natal (soberania/fronteiras) e Saturno natal (contas públicas e estabilidade federativa)",
        "main_scenario": "REGIME_CRISIS"
    },
    {
        "iso": "USA",
        "name_pt": "Estados Unidos",
        "name_en": "United States",
        "flag": "🇺🇸",
        "capital": "Washington D.C.",
        "foundation_event": "Declaração de Independência",
        "foundation_date": "1776-07-04",
        "strategic_summary": "Ao completar o 250º aniversário em 2026, os Estados Unidos atravessam um período de teste de liderança hegemônica global sob a oposição de Netuno e a passagem de Plutão em oposição ao Sol/Mercúrio natal. A década de 2020 exige redefinição de sua doutrina militar e superação de polarização partidária antes de liderar o salto tecnológico de 2028.",
        "critical_years": [2026, 2027, 2031, 2036],
        "vulnerability": "Eixo Sol-Saturno natal e Nodo Norte (liderança global e pacto de união civil)",
        "main_scenario": "WAR_CONFLICT"
    },
    {
        "iso": "CHN",
        "name_pt": "China",
        "name_en": "China",
        "flag": "🇨🇳",
        "capital": "Pequim",
        "foundation_event": "Proclamação da República Popular da China",
        "foundation_date": "1949-10-01",
        "strategic_summary": "A República Popular entra na fase de maior atrito geopolítico no Pacífico em 2026 (Netuno quadratura Urano natal), testando a soberania sobre Taiwan. Em 2034, o país completa o ciclo completo de 85 anos com Plutão em conjunção ao Plutão natal de 1949, sinalizando o esgotamento do modelo de hipercentralização do PCC e transição geracional compulsória.",
        "critical_years": [2026, 2031, 2034, 2042],
        "vulnerability": "Urano natal (fronteiras marítimas) e Plutão natal em Leão (poder absolutista do Partido)",
        "main_scenario": "REGIME_CRISIS"
    },
    {
        "iso": "RUS",
        "name_pt": "Rússia",
        "name_en": "Russia",
        "flag": "🇷🇺",
        "capital": "Moscou",
        "foundation_event": "Declaração de Soberania Estatal da Federação Russa",
        "foundation_date": "1990-06-12",
        "strategic_summary": "Sob a oposição de Plutão a Saturno natal em 2026 e oposição de Saturno a Plutão em 2029, a Federação Russa vive o fim do ciclo político pós-soviético. Espera-se reestruturação no núcleo duro do Kremlin, comoção social pelo custo de guerras prolongadas em 2028 e estresse cambial severo nas finanças do Estado análogo à crise de 1998.",
        "critical_years": [2026, 2028, 2029, 2033],
        "vulnerability": "Saturno natal (estabilidade do Kremlin) e Quíron natal (comoção popular por perdas bélicas)",
        "main_scenario": "REGIME_CRISIS"
    },
    {
        "iso": "ISR",
        "name_pt": "Israel",
        "name_en": "Israel",
        "flag": "🇮🇱",
        "capital": "Jerusalém",
        "foundation_event": "Declaração de Independência de Israel",
        "foundation_date": "1948-05-14",
        "strategic_summary": "A ativação continuada de Marte e dos eixos nodais natais em 2026–2029 coloca Israel sob risco máximo de conflagração regional em múltiplas frentes, com precedentes diretos na Guerra do Yom Kippur (1973). A soberania e a dissuasão militar são testadas em limites extremos antes de pactos de contenção na década de 2030.",
        "critical_years": [2026, 2027, 2029, 2035],
        "vulnerability": "Marte e Plutão natais (defesa existencial e fronteiras hostis)",
        "main_scenario": "WAR_CONFLICT"
    },
    {
        "iso": "IRN",
        "name_pt": "Irã",
        "name_en": "Iran",
        "flag": "🇮🇷",
        "capital": "Teerã",
        "foundation_event": "Proclamação da República Islâmica",
        "foundation_date": "1979-04-01",
        "strategic_summary": "A teocracia iraniana passa por seu momento de maior fragilidade entre 2027 e 2029 (Urano e Sol em quadratura com Saturno e Sol natal). O período coincide com a inevitável transição do Guia Supremo e sublevação de uma sociedade civil jovem e conectada por reformas laicas e abertura política.",
        "critical_years": [2027, 2028, 2029, 2034],
        "vulnerability": "Sol e Saturno natais de 1979 (legitimidade teocrática e controle clerical)",
        "main_scenario": "REGIME_CRISIS"
    },
    {
        "iso": "GBR",
        "name_pt": "Reino Unido",
        "name_en": "United Kingdom",
        "flag": "🇬🇧",
        "capital": "Londres",
        "foundation_event": "Ato de União da Grã-Bretanha e Irlanda",
        "foundation_date": "1801-01-01",
        "strategic_summary": "O Reino Unido enfrenta atrito militar expedicionário e demandas pesadas de defesa marítima em 2026 e 2030 (Plutão em quadratura com Marte natal, isomórfico à Guerra das Malvinas de 1982 e Crimeia de 1854). Ao mesmo tempo, a estabilidade interna é pressionada por debates sobre o futuro da monarquia e secessão escocesa.",
        "critical_years": [2026, 2029, 2030, 2037],
        "vulnerability": "Marte natal (engajamento militar expedicionário) e Sol natal (instituições monárquicas)",
        "main_scenario": "WAR_CONFLICT"
    },
    {
        "iso": "FRA",
        "name_pt": "França",
        "name_en": "France",
        "flag": "🇫🇷",
        "capital": "Paris",
        "foundation_event": "Proclamação da Quinta República",
        "foundation_date": "1958-10-04",
        "strategic_summary": "A Quinta República francesa chega a um ponto de inflexão constitucional entre 2026 e 2030 (Urano em quadratura com Plutão natal e Netuno sobre o Sol). A insatisfação popular com a centralização presidencial e a crise fiscal forçam discussões sobre dissolução institucional e transição para uma Sexta República.",
        "critical_years": [2026, 2029, 2030, 2035],
        "vulnerability": "Plutão natal em Leão (hiperpresidencialismo) e Sol natal (autoridade executiva)",
        "main_scenario": "REGIME_CRISIS"
    },
    {
        "iso": "DEU",
        "name_pt": "Alemanha",
        "name_en": "Germany",
        "flag": "🇩🇪",
        "capital": "Berlim",
        "foundation_event": "Reunificação Alemã",
        "foundation_date": "1990-10-03",
        "strategic_summary": "A locomotiva europeia atravessa choque industrial severo e fragmentação política crônica em 2027–2029 (Plutão em oposição a Júpiter natal e quadratura do Sol natal). O modelo econômico exportador baseado em energia barata e crédito abundante é reformulado sob forte tensão social e polarização partidária.",
        "critical_years": [2027, 2028, 2029, 2033],
        "vulnerability": "Júpiter natal (modelo industrial exportador) e Sol natal (capacidade de consenso de coalizão)",
        "main_scenario": "ECONOMIC_CRASH"
    },
    {
        "iso": "UKR",
        "name_pt": "Ucrânia",
        "name_en": "Ukraine",
        "flag": "🇺🇦",
        "capital": "Kiev",
        "foundation_event": "Declaração de Independência da Ucrânia",
        "foundation_date": "1991-08-24",
        "strategic_summary": "A soberania e a integridade territorial ucraniana atingem novos picos de tensão bélica em 2026 e 2038 sob ativações de Urano e Sol natal. A conjuntura aponta para momentos decisivos de acordos permanentes de limites territoriais e reconstrução financiada por consórcios ocidentais.",
        "critical_years": [2026, 2038, 2040, 2045],
        "vulnerability": "Sol e Urano natais (fronteiras soberanas e autodeterminação nacional)",
        "main_scenario": "WAR_CONFLICT"
    },
    {
        "iso": "JPN",
        "name_pt": "Japão",
        "name_en": "Japan",
        "flag": "🇯🇵",
        "capital": "Tóquio",
        "foundation_event": "Promulgação da Constituição do Pós-Guerra",
        "foundation_date": "1947-05-03",
        "strategic_summary": "O Japão passa pela mais profunda reforma de sua doutrina de segurança nacional desde 1945. Entre 2028 e 2030 (Plutão em quadratura ao Sol e Marte da Constituição de 1947), o país abandona o pacifismo estrito do Artigo 9, assume papel militar ativo no Pacífico Ocidental e reestrutura suas forças armadas para dissuasão avançada.",
        "critical_years": [2028, 2029, 2030, 2036],
        "vulnerability": "Marte natal em Peixes (restrição pacifista constitucional) e Sol natal (identidade imperial moderna)",
        "main_scenario": "WAR_CONFLICT"
    },
    {
        "iso": "IND",
        "name_pt": "Índia",
        "name_en": "India",
        "flag": "🇮🇳",
        "capital": "Nova Déli",
        "foundation_event": "Independência da Índia",
        "foundation_date": "1947-08-15",
        "strategic_summary": "A Índia consolida sua posição como terceira maior economia mundial, mas enfrenta atrito nas fronteiras do Himalaia com a China em 2027 e testes de coesão interna em 2031 (Plutão em conjunção ao Plutão natal de 1947). O desafio central é balancear o crescimento econômico acelerado com a autonomia dos estados federados.",
        "critical_years": [2027, 2031, 2035, 2041],
        "vulnerability": "Plutão natal em Câncer (segurança interna e autonomia regional) e Netuno natal (conflitos fronteiriços)",
        "main_scenario": "REGIME_CRISIS"
    }
]

MILESTONE_YEARS = [
    {
        "year": 2026,
        "title_pt": "O Ponto Vernal & A Redefinição das Fronteiras Globais",
        "title_en": "The Vernal Point & Global Border Redefinition",
        "cosmic_signature": "Saturno e Netuno a 0° de Áries • Plutão em Aquário • Urano em Touro/Gêmeos",
        "energy_score": 978.2,
        "impact_level": "🚨 Crítico",
        "key_actors": ["Global", "Brasil", "Estados Unidos", "China", "Rússia", "França", "Israel"],
        "summary": "Marco zero da ordem internacional do século XXI. O encontro de Saturno e Netuno no Ponto Vernal (0° Áries) inaugura um ciclo de 36 anos de desmantelamento de tratados obsoletos e tensão sobre soberania de recursos estratégicos e ciberdefesa quântica.",
        "historical_precedent": "Doutrina Truman / Início da Guerra Fria (1947) e Eclosão do Sputnik (1957)"
    },
    {
        "year": 2028,
        "title_pt": "O Grande Trígono de Ar & O Salto Tecnológico Civilizatório",
        "title_en": "The Grand Air Trine & The Civilizational Tech Leap",
        "cosmic_signature": "Urano em Gêmeos (4°) △ Plutão em Aquário (4°)",
        "energy_score": 992.1,
        "impact_level": "🚨 Crítico",
        "key_actors": ["Global", "Japão", "Alemanha", "Estados Unidos", "Brasil", "Irã"],
        "summary": "Momento ápice de inovação tecnológica do século. A harmonia nos signos de Ar desencadeia a fusão definitiva da inteligência artificial autônoma com redes quânticas e consolidação da presença humana permanente na Lua (Bases Artemis e Chang'e).",
        "historical_precedent": "Invenção do Telégrafo (1844) e Pouso do Homem na Lua (1969)"
    },
    {
        "year": 2029,
        "title_pt": "O Centenário do Crash & A Reorganização Monetária",
        "title_en": "The Crash Centenary & Monetary Reorganization",
        "cosmic_signature": "Saturno em Touro □ Plutão em Aquário",
        "energy_score": 989.7,
        "impact_level": "🚨 Crítico",
        "key_actors": ["Global", "Rússia", "Japão", "Alemanha", "França", "Israel", "Brasil"],
        "summary": "Exatamente 100 anos após o Crash de 1929, a quadratura entre Saturno e Plutão impõe uma desalavancagem compulsória da dívida pública mundial, forçando a substituição do petrodólar por sistemas multilaterais de liquidação em moedas digitais soberanas.",
        "historical_precedent": "Crash de Wall Street (1929) e Crise da Dívida Soberana / Subprime (2008)"
    },
    {
        "year": 2032,
        "title_pt": "A Batalha dos Recursos Vitais & Conflito Eletrônico",
        "title_en": "The Battle for Vital Resources & Electronic Warfare",
        "cosmic_signature": "Saturno e Urano em Gêmeos / Câncer □ Netuno em Áries",
        "energy_score": 985.8,
        "impact_level": "🚨 Crítico",
        "key_actors": ["Global", "Estados Unidos", "China", "Índia", "União Europeia"],
        "summary": "Início da janela de maior atrito sobre recursos vitais (água potável, minerais de transição energética e suprimento alimentar). Aceleração da militarização de satélites orbitais e guerra eletrônica que afeta a infraestrutura de dados global.",
        "historical_precedent": "Eclosão de Disputas Hegemônicas e Bloqueios Navais da Década de 1930"
    },
    {
        "year": 2034,
        "title_pt": "O Clímax Geopolítico da Década: Urano-Saturno ☍ Plutão",
        "title_en": "The Decade's Geopolitical Climax: Uranus-Saturn ☍ Pluto",
        "cosmic_signature": "Urano ☌ Saturno em Câncer ☍ Plutão em Aquário",
        "energy_score": 996.0,
        "impact_level": "🚨 Crítico Máximo",
        "key_actors": ["Global", "China", "Leste Europeu", "Oriente Médio", "Estados Unidos"],
        "summary": "O alinhamento mais tenso e potencialmente disruptivo da primeira metade do século XXI (análogo direto a 1914 e 1944). Risco máximo de confrontos armados de alta intensidade, colapso de organismos multilaterais tradicionais e redesenho forçado de fronteiras.",
        "historical_precedent": "Eclosão da Primeira Guerra Mundial (1914) e Ofensivas do Dia D / Bretton Woods (1944)"
    },
    {
        "year": 2036,
        "title_pt": "O Grande Trígono de Fogo & A Revolução da Fusão Nuclear",
        "title_en": "The Grand Fire Trine & The Nuclear Fusion Revolution",
        "cosmic_signature": "Netuno em Áries △ Saturno em Leão",
        "energy_score": 996.0,
        "impact_level": "🚨 Crítico",
        "key_actors": ["Global", "Estados Unidos", "China", "França", "Japão"],
        "summary": "Revolução na física aplicada e energia. Operacionalização comercial das primeiras usinas contínuas de fusão nuclear, encerrando gradualmente a geopolítica do petróleo fóssil e inaugurando a era da manufatura orbital pesada.",
        "historical_precedent": "Projeto Manhattan e Início da Era Atômica (1942–1945)"
    },
    {
        "year": 2040,
        "title_pt": "A Grande Mutação: O Novo Acordo Bretton Woods Digital",
        "title_en": "The Great Mutation: The New Digital Bretton Woods",
        "cosmic_signature": "Conjunção Júpiter-Saturno em Libra • Oposição com Netuno",
        "energy_score": 980.5,
        "impact_level": "🚨 Crítico",
        "key_actors": ["Global", "Todas as Potências do G20", "Ásia", "América Latina"],
        "summary": "Pacto diplomático e financeiro global sem precedentes para a segunda metade do século XXI. Institucionalização de um novo padrão monetário multilateral regulado por inteligência distribuída e cortes compulsórios de pegada ecológica.",
        "historical_precedent": "Acordos de Bretton Woods e Fundação da ONU / FMI (1944)"
    }
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

def generate_world_synthesis(year: int, scenario_key: str, peak_score: float, trigger: str) -> Dict[str, str]:
    """Gera sínteses detalhadas e precedentes históricos específicos para os picos mundiais."""
    # Verificação se o ano é um dos marcos cruciais
    for m in MILESTONE_YEARS:
        if m["year"] == year:
            return {
                "synthesis": f"Pico Crítico Global ({peak_score}/1000): {m['summary']}",
                "prec_title": m["historical_precedent"],
                "prec_year": str(year),
                "prec_summary": f"Configuração astrológica análoga a momentos de profunda transição de poder mundial e saltos tecnológicos registrados nos 3.406 fatos históricos."
            }

    # Anos gerais da era
    if year <= 2029:
        if scenario_key == "WAR_CONFLICT":
            return {
                "synthesis": f"Pressão de segurança internacional ({peak_score}/1000). A entrada dos planetas lentos em Áries e Gêmeos eleva o atrito nas fronteiras terrestres e marítimas, acelerando a corrida armamentista autônoma.",
                "prec_title": "Crise dos Mísseis de Cuba / Eclosão de Conflitos Regionais (1962)",
                "prec_year": "1962",
                "prec_summary": "Tensão geopolítica em escala global forçando linhas diretas de dissuasão nuclear e tratados de não-proliferação."
            }
        elif scenario_key == "ECONOMIC_CRASH":
            return {
                "synthesis": f"Estresse financeiro e reajuste de liquidez ({peak_score}/1000). Pressão inflacionária de matérias-primas e aperto das taxas de juros globais gerando inadimplência soberana.",
                "prec_title": "Choque do Petróleo e Estagflação Global (1973–1979)",
                "prec_year": "1973",
                "prec_summary": "Reorganização compulsória das cadeias de valor e emergência de novas moedas de liquidação comercial."
            }
        elif scenario_key == "TECH_INNOVATION":
            return {
                "synthesis": f"Salto quântico e aeroespacial ({peak_score}/1000). Consolidação dos modelos de inteligência artificial de fronteira e primeiras missões de infraestrutura lunar permanente.",
                "prec_title": "Lançamento da Missão Apollo 11 / Início da Era Espacial (1969)",
                "prec_year": "1969",
                "prec_summary": "Expansão da presença humana além da órbita baixa da Terra e revolução nos sistemas de telecomunicação."
            }
        else:
            return {
                "synthesis": f"Inflexão institucional global ({peak_score}/1000). Crise de representatividade das organizações multilaterais do pós-guerra e ascensão de novos blocos autárquicos continentais.",
                "prec_title": "Conferência de Potsdam / Reorganização do Pós-Segunda Guerra (1945)",
                "prec_year": "1945",
                "prec_summary": "Reformulação dos mandatos diplomáticos internacionais e criação de novos eixos de poder global."
            }
    elif year <= 2039:
        if scenario_key == "WAR_CONFLICT":
            return {
                "synthesis": f"Clímax de disputa por recursos estratégicos ({peak_score}/1000). A conjunção em Câncer e aspectos com Plutão provocam nacionalismos territoriais exacerbados sobre água potável, alimentos e energia.",
                "prec_title": "Eclosão de Conflitos de Soberania Territorial / Primeira Guerra Mundial (1914)",
                "prec_year": "1914",
                "prec_summary": "Escalada em cadeia de tratados de defesa mútua culminando em mobilização militar massiva."
            }
        elif scenario_key == "TECH_INNOVATION":
            return {
                "synthesis": f"Avanço em fusão nuclear e propulsão de plasma ({peak_score}/1000). O trígono de Fogo catalisa novas fontes de geração de energia limpa inesgotável.",
                "prec_title": "Projeto Manhattan / Revolução da Energia Atômica (1942)",
                "prec_year": "1942",
                "prec_summary": "Salto civilizatório que redefine as matrizes industriais de produção de energia elétrica e propulsão interplanetária."
            }
        else:
            return {
                "synthesis": f"Reorganização dos blocos regionais ({peak_score}/1000). Fragmentação do comércio mundial em redes confiáveis fechadas (friendshoring) sob nova governança digital.",
                "prec_title": "Conferência de Bandung e Criação dos Não-Alinhados (1955)",
                "prec_year": "1955",
                "prec_summary": "Emergência de um terceiro polo independente de potências médias reequilibrando a ordem bipolar."
            }
    else:
        return {
            "synthesis": f"Maturidade da Era do Ar ({peak_score}/1000). Consolidação da governança digital distribuída, transição energética concluída e expansão da exploração de asteroides e bases em Marte.",
            "prec_title": "Primavera dos Povos e Globalização Pós-Guerra Fria (1848 / 1991)",
            "prec_year": "1991",
            "prec_summary": "Dissolução pacífica de blocos obsoletos e integração de sistemas planetários em rede."
        }

def generate_country_synthesis(iso: str, country_name: str, year: int, scenario_key: str, score: float, top_transit: Dict[str, Any]) -> Dict[str, str]:
    """Gera análises prospectivas profundas e customizadas para cada país soberano."""
    t_planet = top_transit.get("transit_planet", "")
    n_planet = top_transit.get("natal_planet", "")
    asp_name = top_transit.get("aspect_name", "")

    # BRASIL
    if iso == "BRA":
        if year == 2026:
            return {
                "synthesis": f"Pico Crítico no Brasil ({score}/1000). Netuno em quadratura com Urano natal de 1822 pressiona a soberania nacional sobre recursos estratégicos (Amazônia, transição verde e petróleo da margem equatorial), gerando forte cobrança e sanções protecionistas de blocos internacionais.",
                "prec_title": "Crise da Cisplatina e Bloqueios Navais Estrangeiros (1825)",
                "prec_year": "1825",
                "prec_summary": "Atrito diplomático e militar exigindo defesa ativa das linhas costeiras e recursos da nação."
            }
        elif year == 2028:
            return {
                "synthesis": f"Choque Fiscal do Retorno de Saturno ({score}/1000). A oposição exata de Saturno a Saturno natal de 1822 (ciclo de 29 anos) impõe aperto severo nas contas públicas, rolagem crítica da dívida soberana e reformas previdenciárias e tributárias inadiáveis, similares aos ciclos de 1964 e 1994.",
                "prec_title": "Crise da Dívida Externa e Choques de Estabilização (1983 / 1994)",
                "prec_year": "1983",
                "prec_summary": "Esgotamento da capacidade fiscal forçando renegociação com credores internacionais e estabilização monetária."
            }
        elif year == 2029:
            return {
                "synthesis": f"Clímax de Tensão Institucional ({score}/1000). Plutão em quadratura com Saturno natal gera choque aberto entre o Supremo Tribunal Federal, o Congresso Nacional e as Forças Armadas sobre os limites da ordem constitucional, exigindo um novo pacto de governabilidade republicana.",
                "prec_title": "Fim do Estado Novo e Redemocratização (1945 / 1985)",
                "prec_year": "1985",
                "prec_summary": "Transição de regime político com ampla mobilização cívica e repactuação das prerrogativas dos Poderes."
            }
        elif year >= 2030:
            return {
                "synthesis": f"Reorganização do Modelo de Desenvolvimento ({score}/1000). O Brasil consolida liderança na produção de alimentos e energia renovável, mas enfrenta testes recorrentes de solvência fiscal sob os trânsitos de {t_planet} sobre {n_planet} natal.",
                "prec_title": "Plano Real e Inserção Global Brasileira (1994)",
                "prec_year": "1994",
                "prec_summary": "Modernização estrutural da economia brasileira com estabilidade cambial e expansão agroindustrial."
            }

    # ESTADOS UNIDOS
    elif iso == "USA":
        if year == 2026:
            return {
                "synthesis": f"Marco do 250º Aniversário da Independência ({score}/1000). Netuno em oposição a Netuno natal de 1776 atinge o ponto máximo de contestação da narrativa nacional americana, paralisia de consensos legislativos e reavaliação de compromissos hegemônicos globais.",
                "prec_title": "Pós-Guerra da Independência e Criação da Constituição (1787)",
                "prec_year": "1787",
                "prec_summary": "Momento de profunda introspecção e redefinição dos limites do pacto federativo dos Estados Unidos."
            }
        elif year == 2027:
            return {
                "synthesis": f"Desafio de Liderança Militar e Hegemonia ({score}/1000). Plutão em trânsito no Nodo Norte natal e oposição ao Sol/Mercúrio de 1776 provoca polarização interna máxima em ano pré-eleitoral e teste decisivo de dissuasão bélica no exterior.",
                "prec_title": "Eclosão da Guerra Civil Americana (1861) / Crise de Liderança de 1776",
                "prec_year": "1861",
                "prec_summary": "Choque existencial entre facções territoriais e políticas pela definição do futuro da União."
            }
        elif year == 2031:
            return {
                "synthesis": f"Retração Estratégica e Nova Doutrina ({score}/1000). Netuno sobre Saturno natal força o encerramento de intervenções militares custosas no ultramar, direcionando orçamentos para a segurança interna e reindustrialização tecnológica.",
                "prec_title": "Fim da Guerra do Vietnã e Queda de Saigon (1975)",
                "prec_year": "1975",
                "prec_summary": "Mudança radical na opinião pública americana contrária a intervenções bélicas prolongadas no exterior."
            }
        elif year >= 2032:
            return {
                "synthesis": f"Liderança na Fronteira Tecnológica ({score}/1000). Sob o impulso de {t_planet} em {asp_name} com {n_planet} natal, os EUA renovam a supremacia em inteligência artificial e defesa aeroespacial autônoma.",
                "prec_title": "Corrida Espacial e Vitória Tecnológica na Guerra Fria (1969–1989)",
                "prec_year": "1989",
                "prec_summary": "Superação de concorrentes mundiais pela inovação de ponta e capacidade de atração de cérebros globais."
            }

    # CHINA
    elif iso == "CHN":
        if year == 2026:
            return {
                "synthesis": f"Pico de Tensão de Soberania Marítima ({score}/1000). Netuno em quadratura ao Urano de 1949 coloca Pequim sob pressão máxima no Estreito de Taiwan e Mar do Sul da China, desafiando a dissuasão naval dos Estados Unidos e aliados asiáticos.",
                "prec_title": "Primeira Crise do Estreito de Taiwan (1954)",
                "prec_year": "1954",
                "prec_summary": "Bombardeios costeiros e mobilização naval gerando alerta de guerra aberta entre potências nucleares."
            }
        elif year == 2031:
            return {
                "synthesis": f"Atrito Ideológico e Hegemonia Regional ({score}/1000). Netuno em oposição ao Netuno natal de 1949 testa a coesão do modelo de financiamento público e das rotas de suprimento da Nova Rota da Seda.",
                "prec_title": "Guerra Sino-Vietnamita e Invasão de Fronteira (1979)",
                "prec_year": "1979",
                "prec_summary": "Conflito militar de fronteira para testar a influência soviética no Sudeste Asiático."
            }
        elif year == 2034:
            return {
                "synthesis": f"O Grande Ciclo de 85 Anos: Plutão Conjunção Plutão ({score}/1000). O retorno exato de Plutão ao grau da Proclamação de 1949 marca a maior transição geracional no Partido Comunista Chinês, esgotamento do modelo autoritário e reconfiguração do contrato social.",
                "prec_title": "Fim da Revolução Cultural e Morte de Mao Tsé-Tung (1976)",
                "prec_year": "1976",
                "prec_summary": "Expurgo da Camarilha dos Quatro e início das reformas de abertura lideradas por Deng Xiaoping."
            }
        elif year >= 2035:
            return {
                "synthesis": f"Consolidação da Potência Multipolar ({score}/1000). Sob trânsitos de {t_planet} com {n_planet} natal, a China equilibra desaceleração demográfica com autossuficiência robótica e espacial.",
                "prec_title": "Ingresso da China na Organização Mundial do Comércio (2001)",
                "prec_year": "2001",
                "prec_summary": "Transformação da China na fábrica do mundo e ascensão definitiva à condição de superpotência fabril."
            }

    # RÚSSIA
    elif iso == "RUS":
        if year == 2026:
            return {
                "synthesis": f"Transição no Núcleo do Kremlin ({score}/1000). Plutão em oposição a Saturno natal de 1990 precipita a substituição de lideranças da era pós-soviética e reestruturação do aparato militar e dos serviços de inteligência.",
                "prec_title": "Tentativa de Golpe de Estado Soviético (1991)",
                "prec_year": "1991",
                "prec_summary": "Tentativa desesperada da linha-dura de frear a dissolução das estruturas estatais centrais."
            }
        elif year == 2028:
            return {
                "synthesis": f"Comoção Social e Fadiga de Guerra ({score}/1000). Plutão sobre Quíron natal desperta manifestações de mães de combatentes e insatisfação coletiva com o custo humano de conflitos prolongados de atrito.",
                "prec_title": "Revolução Russa de 1905 e Domingo Sangrento (1905)",
                "prec_year": "1905",
                "prec_summary": "Eclosão de revolta popular em massa contra a autocracia após derrotas militares humilhantes."
            }
        elif year == 2029:
            return {
                "synthesis": f"Choque Financeiro e Colapso Cambial ({score}/1000). Saturno em oposição a Plutão natal esgota os fundos soberanos de reserva cambial, forçando moratória da dívida e desvalorização aguda do rublo, análogo a 1998.",
                "prec_title": "Moratória e Crise Financeira do Rublo (1998)",
                "prec_year": "1998",
                "prec_summary": "Colapso do sistema bancário russo forçando intervenção do FMI e renúncia de gabinete."
            }
        elif year >= 2030:
            return {
                "synthesis": f"Reconstrução da Segurança Eurasiática ({score}/1000). Sob {t_planet} em {asp_name} com {n_planet} natal, a Rússia redefine seu espaço de influência na Ásia Central e Cáucaso.",
                "prec_title": "Tratado de Criação da União Eurasiática (2014)",
                "prec_year": "2014",
                "prec_summary": "Tentativa de consolidação de bloco econômico independente na Eurásia."
            }

    # JAPÃO
    elif iso == "JPN":
        if year in [2028, 2029, 2030]:
            return {
                "synthesis": f"Reforma do Pacifismo e Rearme Pleno ({score}/1000). Plutão em quadratura com Sol e Marte da Constituição de 1947 força a revogação definitiva do Artigo 9, transformando as Forças de Autodefesa em forças armadas convencionais ativas no Pacífico.",
                "prec_title": "Fim do Xogunato Tokugawa e Restauração Meiji (1868)",
                "prec_year": "1868",
                "prec_summary": "Abertura forçada ao Ocidente e rápida modernização militar para garantir a soberania nacional."
            }
        else:
            return {
                "synthesis": f"Pico Estratégico no Japão ({score}/1000). A ativação de {t_planet} em {asp_name} com {n_planet} natal impulsiona cooperação com aliados na defesa de rotas no Mar do Japão e Estreito de Malaca.",
                "prec_title": "Tratado de Segurança EUA-Japão (1951)",
                "prec_year": "1951",
                "prec_summary": "Pacto militar garantindo a defesa do arquipélago sob o guarda-chuva nuclear aliado."
            }

    # ALEMANHA
    elif iso == "DEU":
        if year in [2027, 2028, 2029]:
            return {
                "synthesis": f"Crise do Modelo Industrial Europeu ({score}/1000). Plutão em oposição a Júpiter natal e quadratura do Sol de 1990 impõe desalavancagem bancária, contração no setor automotivo/químico e paralisia de coalizões partidárias em Berlim.",
                "prec_title": "Crises de Coalizão e Fragmentação da República de Weimar (1930)",
                "prec_year": "1930",
                "prec_summary": "Incapacidade de formar maiorias parlamentares estáveis em meio à recessão econômica profunda."
            }
        else:
            return {
                "synthesis": f"Reestruturação Industrial e Energética ({score}/1000). {t_planet} em {asp_name} com {n_planet} natal obriga a Alemanha a liderar a união fiscal e a modernização de defesa da União Europeia.",
                "prec_title": "Criação do Euro e Tratado de Maastricht (1992)",
                "prec_year": "1992",
                "prec_summary": "Unificação monetária europeia para selar a paz continental e fortalecer a moeda comum."
            }

    # FRANÇA
    elif iso == "FRA":
        if year in [2026, 2029, 2030]:
            return {
                "synthesis": f"Crise da Quinta República ({score}/1000). Urano em quadratura a Plutão natal de 1958 e Netuno sobre o Sol desestabilizam o presidencialismo de De Gaulle, com greves gerais e clamor popular por uma Sexta República parlamentarista.",
                "prec_title": "Maio de 1968 / Queda da Quarta República Francesa (1958)",
                "prec_year": "1958",
                "prec_summary": "Colapso do sistema partidário em meio a crises coloniais e ascensão de nova constituição."
            }
        else:
            return {
                "synthesis": f"Defesa e Autonomia Estratégica Europeia ({score}/1000). Sob {t_planet} em {asp_name} com {n_planet} natal, a França lidera propostas de exército europeu unificado e diplomacia autônoma.",
                "prec_title": "Saída da França do Comando Integrado da OTAN por De Gaulle (1966)",
                "prec_year": "1966",
                "prec_summary": "Afirmação de soberania militar independente com desenvolvimento de força de dissuasão nuclear própria."
            }

    # REINO UNIDO
    elif iso == "GBR":
        if year in [2026, 2029, 2030]:
            return {
                "synthesis": f"Mobilização Militar e Coesão do Reino ({score}/1000). Marte e Plutão em quadratura com a carta de 1801 exigem envio de forças navais e aéreas expedicionárias, enquanto o Parlamento enfrenta novo plebiscito de secessão escocesa.",
                "prec_title": "Guerra das Malvinas (1982) / Entrada na Guerra da Crimeia (1854)",
                "prec_year": "1982",
                "prec_summary": "Mobilização de frota naval em defesa de território soberano e resgate da moral militar nacional."
            }
        else:
            return {
                "synthesis": f"Readequação Comercial Global ({score}/1000). {t_planet} em {asp_name} com {n_planet} natal estimula acordos do Reino Unido com o Commonwealth e bacia do Indo-Pacífico.",
                "prec_title": "Criação da Comunidade Britânica de Nações / Commonwealth (1931)",
                "prec_year": "1931",
                "prec_summary": "Transformação do império em comunidade de nações autônomas unidas por laços comerciais e culturais."
            }

    # SÍNTESE PADRÃO ELEVADA PARA DEMAIS CASOS
    scenario_desc = SCENARIO_META.get(scenario_key, {}).get("label_pt", "Ativação Geopolítica")
    return {
        "synthesis": f"Pico de Ativação Soberana em {country_name} ({score}/1000). O trânsito de {t_planet} em {asp_name} com {n_planet} natal tensiona o cenário '{scenario_desc}', exigindo prontidão estratégica governamental e diplomática.",
        "prec_title": f"Ciclo Histórico de Transição Nacional ({year-30})",
        "prec_year": str(year-30),
        "prec_summary": f"Fase pregressa em que aspectos planetários comparáveis precipitaram reorganização institucional e defesa territorial."
    }

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

        scenarios_scores = [
            ("WAR_CONFLICT", c_risk),
            ("ECONOMIC_CRASH", cr_risk),
            ("TECH_INNOVATION", t_risk),
            ("SOCIAL_UPHEAVAL", s_risk)
        ]
        best_scenario, best_val = max(scenarios_scores, key=lambda x: x[1])

        trigger = item.get("cosmic_trigger", "")
        if "♄" in trigger and "♇" in trigger:
            best_scenario = "REGIME_CRISIS"
        elif "♅" in trigger and "Gêmeos" in trigger and t_risk > 500:
            best_scenario = "TECH_INNOVATION"
        elif year in [2026, 2028]:
            best_scenario = "TECH_INNOVATION"
        elif year in [2029, 2052]:
            best_scenario = "ECONOMIC_CRASH"
        elif year in [2034, 2032]:
            best_scenario = "WAR_CONFLICT"

        meta = SCENARIO_META[best_scenario]
        gen_data = generate_world_synthesis(year, best_scenario, round(peak_score, 1), trigger)

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
            "cosmic_signature": trigger[:85] + ("..." if len(trigger) > 85 else ""),
            "cosmic_signature_detail": trigger,
            "historical_precedent_title": gen_data["prec_title"],
            "historical_precedent_year": gen_data["prec_year"],
            "historical_precedent_summary": gen_data["prec_summary"],
            "prospective_synthesis": gen_data["synthesis"],
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
        yearly_activations = []
        for yr in range(2026, 2061):
            t_res = calculate_transits_for_date(chart, f"{yr}-07-01")
            score = t_res["activation_index_1000"]
            slow_transits = [t for t in t_res.get("transits", []) if t["transit_planet_id"] in ["pluto", "neptune", "uranus", "saturn", "jupiter", "mars"]]
            yearly_activations.append((yr, score, t_res, slow_transits))

        # Encontra picos locais ou anos com score >= 720
        for i, (yr, score, t_res, slow_transits) in enumerate(yearly_activations):
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

            headline = f"{top_t['transit_symbol']} {top_t['transit_planet']} {top_t['aspect_symbol']} {top_t['natal_planet']} natal ({top_t['formatted_orb']})"
            detail = f"{top_t['transit_planet']} em trânsito forma {top_t['aspect_name']} com {top_t['natal_planet']} na carta de fundação do país."

            gen_data = generate_country_synthesis(iso, c_info["name_pt"], yr, cat_key, score, top_t)

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
                "historical_precedent_title": gen_data["prec_title"],
                "historical_precedent_year": gen_data["prec_year"],
                "historical_precedent_summary": gen_data["prec_summary"],
                "prospective_synthesis": gen_data["synthesis"],
                "decade": get_decade(yr)
            })

    return country_peaks

def build_risk_matrix(peaks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Constrói matriz de risco comparada por ano (2026-2040) x país para o heatmap executivo."""
    years = list(range(2026, 2041))
    matrix_rows = []

    # Linha Global
    world_cells = []
    for y in years:
        w_p = [p for p in peaks if p["scope_type"] == "world" and p["year"] == y]
        if w_p:
            top_p = max(w_p, key=lambda x: x["energy_score_1000"])
            world_cells.append({
                "year": y,
                "score": top_p["energy_score_1000"],
                "level": top_p["alert_level"],
                "scenario": top_p["scenario_key"],
                "icon": top_p["scenario_icon"],
                "has_peak": True
            })
        else:
            world_cells.append({"year": y, "score": 0, "level": "Estável", "has_peak": False})

    matrix_rows.append({
        "iso": "WLD",
        "name_pt": "Global / Mundial",
        "flag": "🌐",
        "cells": world_cells
    })

    # Linhas dos Países
    for c in KEY_COUNTRIES:
        c_cells = []
        for y in years:
            c_p = [p for p in peaks if p.get("country_iso") == c["iso"] and p["year"] == y]
            if c_p:
                top_p = max(c_p, key=lambda x: x["energy_score_1000"])
                c_cells.append({
                    "year": y,
                    "score": top_p["energy_score_1000"],
                    "level": top_p["alert_level"],
                    "scenario": top_p["scenario_key"],
                    "icon": top_p["scenario_icon"],
                    "has_peak": True
                })
            else:
                c_cells.append({"year": y, "score": 0, "level": "Estável", "has_peak": False})

        matrix_rows.append({
            "iso": c["iso"],
            "name_pt": c["name_pt"],
            "flag": c["flag"],
            "cells": c_cells
        })

    return {
        "years": years,
        "rows": matrix_rows
    }

def build_full_peaks_catalog():
    print("1. Extraindo picos mundiais (2026–2060)...")
    world_peaks = extract_world_peaks()
    print(f"Picos mundiais extraídos: {len(world_peaks)}")

    print("2. Extraindo picos por país (2026–2060)...")
    country_peaks = extract_country_peaks()
    print(f"Picos por país extraídos: {len(country_peaks)}")

    all_peaks = world_peaks + country_peaks
    all_peaks.sort(key=lambda x: (x["year"], -x["energy_score_1000"]))

    # Dossiês por país
    countries_dossiers = {}
    for c in KEY_COUNTRIES:
        c_p = [p for p in all_peaks if p.get("country_iso") == c["iso"]]
        max_score = max([p["energy_score_1000"] for p in c_p]) if c_p else 0
        crit_count = sum(1 for p in c_p if p["alert_level"] == "Crítico")
        countries_dossiers[c["iso"]] = {
            **c,
            "total_peaks_count": len(c_p),
            "critical_peaks_count": crit_count,
            "max_score": max_score,
            "peaks": c_p
        }

    # Matriz comparativa de risco (anos x países)
    risk_matrix = build_risk_matrix(all_peaks)

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
        "generated_at": "2026-11-02T05:30:00Z",
        "horizon": "2026–2060",
        "kpis": kpis,
        "scenario_meta": SCENARIO_META,
        "countries_meta": KEY_COUNTRIES,
        "milestone_years": MILESTONE_YEARS,
        "countries_dossiers": countries_dossiers,
        "risk_matrix": risk_matrix,
        "peaks": all_peaks
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"Catálogo de Picos de Energia salvo com sucesso em: {OUTPUT_FILE}")
    print(f"Total de Picos Catalogados: {len(all_peaks)} (Mundiais: {len(world_peaks)}, Países: {len(country_peaks)})")

if __name__ == "__main__":
    build_full_peaks_catalog()
