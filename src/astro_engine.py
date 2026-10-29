"""
Motor de Cálculo Astrológico Moderno baseado no Swiss Ephemeris (pyswisseph).
Versão Refinada:
- Aspectos estritos: Conjunção (0°), Oposição (180°), Quadratura (90°) e Trígono (120°).
- Orbe padrão de 3.0° para planetas e asteroides.
- Asteroides clássicos: Ceres, Pallas, Juno, Vesta, Quíron e Lilith.
- 30 Principais Estrelas Fixas com orbe estrito de 0.3° (18 minutos de arco).
"""

import math
import os
from typing import Dict, List, Optional, Tuple, Any
import swisseph as swe

# Configuração do caminho das efemérides suíças
EPHE_PATHS = [
    "/usr/share/libswe/ephe",
    "/usr/share/swisseph",
    "/usr/local/share/swisseph"
]
for p in EPHE_PATHS:
    if os.path.exists(p):
        swe.set_ephe_path(p)
        break

# Definição dos 12 Signos do Zodíaco Tropical
ZODIAC_SIGNS = [
    {"name": "Áries", "symbol": "♈", "element": "Fogo", "modality": "Cardinal", "ruler": "Marte"},
    {"name": "Touro", "symbol": "♉", "element": "Terra", "modality": "Fixo", "ruler": "Vênus"},
    {"name": "Gêmeos", "symbol": "♊", "element": "Ar", "modality": "Mutável", "ruler": "Mercúrio"},
    {"name": "Câncer", "symbol": "♋", "element": "Água", "modality": "Cardinal", "ruler": "Lua"},
    {"name": "Leão", "symbol": "♌", "element": "Fogo", "modality": "Fixo", "ruler": "Sol"},
    {"name": "Virgem", "symbol": "♍", "element": "Terra", "modality": "Mutável", "ruler": "Mercúrio"},
    {"name": "Libra", "symbol": "♎", "element": "Ar", "modality": "Cardinal", "ruler": "Vênus"},
    {"name": "Escorpião", "symbol": "♏", "element": "Água", "modality": "Fixo", "ruler": "Plutão"},
    {"name": "Sagitário", "symbol": "♐", "element": "Fogo", "modality": "Mutável", "ruler": "Júpiter"},
    {"name": "Capricórnio", "symbol": "♑", "element": "Terra", "modality": "Cardinal", "ruler": "Saturno"},
    {"name": "Aquário", "symbol": "♒", "element": "Ar", "modality": "Fixo", "ruler": "Urano"},
    {"name": "Peixes", "symbol": "♓", "element": "Água", "modality": "Mutável", "ruler": "Netuno"}
]

# Planetas, Asteroides e Pontos da Astrologia Moderna
BODIES_DEFINITIONS = [
    # Luminares
    {"id": "sun", "name": "Sol", "symbol": "☉", "swe_id": swe.SUN, "category": "luminar", "weight": 2.0},
    {"id": "moon", "name": "Lua", "symbol": "☽", "swe_id": swe.MOON, "category": "luminar", "weight": 2.0},
    # Planetas Pessoais
    {"id": "mercury", "name": "Mercúrio", "symbol": "☿", "swe_id": swe.MERCURY, "category": "pessoal", "weight": 1.2},
    {"id": "venus", "name": "Vênus", "symbol": "♀", "swe_id": swe.VENUS, "category": "pessoal", "weight": 1.2},
    {"id": "mars", "name": "Marte", "symbol": "♂", "swe_id": swe.MARS, "category": "pessoal", "weight": 1.5},
    # Planetas Sociais
    {"id": "jupiter", "name": "Júpiter", "symbol": "♃", "swe_id": swe.JUPITER, "category": "social", "weight": 1.5},
    {"id": "saturn", "name": "Saturno", "symbol": "♄", "swe_id": swe.SATURN, "category": "social", "weight": 1.8},
    # Planetas Transpessoais
    {"id": "uranus", "name": "Urano", "symbol": "♅", "swe_id": swe.URANUS, "category": "transpessoal", "weight": 2.0},
    {"id": "neptune", "name": "Netuno", "symbol": "♆", "swe_id": swe.NEPTUNE, "category": "transpessoal", "weight": 1.8},
    {"id": "pluto", "name": "Plutão", "symbol": "♇", "swe_id": swe.PLUTO, "category": "transpessoal", "weight": 2.2},
    # Asteroides Clássicos
    {"id": "ceres", "name": "Ceres", "symbol": "⚳", "swe_id": swe.CERES, "category": "asteroide", "weight": 1.0},
    {"id": "pallas", "name": "Pallas", "symbol": "⚴", "swe_id": swe.PALLAS, "category": "asteroide", "weight": 1.0},
    {"id": "juno", "name": "Juno", "symbol": "⚵", "swe_id": swe.JUNO, "category": "asteroide", "weight": 1.0},
    {"id": "vesta", "name": "Vesta", "symbol": "⚶", "swe_id": swe.VESTA, "category": "asteroide", "weight": 1.0},
    # Pontos Especiais
    {"id": "chiron", "name": "Quíron", "symbol": "⚷", "swe_id": swe.CHIRON, "category": "centauro", "weight": 1.0},
    {"id": "lilith", "name": "Lilith (Lua Negra)", "symbol": "⚸", "swe_id": swe.MEAN_APOG, "category": "ponto", "weight": 1.0},
    {"id": "north_node", "name": "Nodo Norte", "symbol": "☊", "swe_id": swe.TRUE_NODE, "category": "nodo", "weight": 1.0}
]

# Aspectos Maiores Estritos com Orbe de 3.0 Graus
STRICT_ASPECT_DEFINITIONS = [
    {"name": "Conjunção", "angle": 0.0, "orb": 3.0, "symbol": "☌", "nature": "intenso", "tension": 1.0},
    {"name": "Quadratura", "angle": 90.0, "orb": 3.0, "symbol": "□", "nature": "tenso", "tension": 2.0},
    {"name": "Trígono", "angle": 120.0, "orb": 3.0, "symbol": "△", "nature": "harmonico", "tension": -1.5},
    {"name": "Oposição", "angle": 180.0, "orb": 3.0, "symbol": "☍", "nature": "tenso", "tension": 2.5}
]

# Catálogo das 30 Principais Estrelas Fixas (Swiss Ephemeris Fixstar)
FIXED_STARS_CATALOG = [
    {
        "key": "Algol",
        "search_name": "Algol",
        "bayer": "Beta Persei",
        "constellation": "Perseu",
        "magnitude": 2.1,
        "nature": "Saturno / Júpiter",
        "significance": "A Cabeça da Medusa. Considerada a estrela mais intensa e perigosa do firmamento; associada a crises súbitas, violência histórica e destruição radical de ordens antigas."
    },
    {
        "key": "Alcyone",
        "search_name": "Alcyone",
        "bayer": "Eta Tauri",
        "constellation": "Touro (Plêiades)",
        "magnitude": 2.9,
        "nature": "Lua / Marte",
        "significance": "A estrela central das Plêiades. Conectada a destinos coletivos marcantes, lamentação histórica, visão mística e eventos de comoção de massa."
    },
    {
        "key": "Aldebaran",
        "search_name": "Aldebaran",
        "bayer": "Alpha Tauri",
        "constellation": "Touro",
        "magnitude": 0.85,
        "nature": "Marte",
        "significance": "O Olho do Touro / Sentinela do Oriente da Pérsia. Liderança militar firme, honra marcial inabalável, coragem cívica e capacidade de liderar exércitos."
    },
    {
        "key": "Rigel",
        "search_name": "Rigel",
        "bayer": "Beta Orionis",
        "constellation": "Órion",
        "magnitude": 0.18,
        "nature": "Júpiter / Marte",
        "significance": "O Pé de Órion. Expansão mercantil global, sabedoria inventiva, glória mecânica e grandes saltos científicos e de navegação."
    },
    {
        "key": "Bellatrix",
        "search_name": "Bellatrix",
        "bayer": "Gamma Orionis",
        "constellation": "Órion",
        "magnitude": 1.64,
        "nature": "Marte / Mercúrio",
        "significance": "A Amazona de Órion. Combatividade veloz, audácia estratégica, espírito de vanguarda e decisões rápidas sob extrema pressão."
    },
    {
        "key": "Capella",
        "search_name": "Capella",
        "bayer": "Alpha Aurigae",
        "constellation": "Cocheiro",
        "magnitude": 0.08,
        "nature": "Marte / Mercúrio",
        "significance": "A Cabra Nutridora. Curiosidade técnica refinada, amor ferrenho à independência, liberdade cívica e avanços intelectuais pioneiros."
    },
    {
        "key": "Polaris",
        "search_name": "Polaris",
        "bayer": "Alpha Ursae Minoris",
        "constellation": "Ursa Menor",
        "magnitude": 1.97,
        "nature": "Saturno / Vênus",
        "significance": "A Estrela Polar. Guia universal de navegantes, centralidade imutável, bússola geopolítica e determinação de destino histórico inflexível."
    },
    {
        "key": "Betelgeuse",
        "search_name": "Betelgeuse",
        "bayer": "Alpha Orionis",
        "constellation": "Órion",
        "magnitude": 0.50,
        "nature": "Marte / Mercúrio",
        "significance": "O Ombro Direito de Órion. Sucesso marcial fulminante, grandes honrarias, avanços em armas e tecnologias bélicas de impacto global."
    },
    {
        "key": "Menkar",
        "search_name": "Menkar",
        "bayer": "Alpha Ceti",
        "constellation": "Baleia (Cetus)",
        "magnitude": 2.54,
        "nature": "Saturno",
        "significance": "O Monstro do Mar. Erupção de forças inconscientes gigantescas, perigos de calamidades coletivas e tempestades sociais."
    },
    {
        "key": "Sirius",
        "search_name": "Sirius",
        "bayer": "Alpha Canis Majoris",
        "constellation": "Cão Maior",
        "magnitude": -1.46,
        "nature": "Júpiter / Marte",
        "significance": "A Estrela Mais Brilhante do Céu / Estrela de Ísis. Fama imensa, liderança carismática de massas, triunfos transcendentais e renome mundial duradouro."
    },
    {
        "key": "Castor",
        "search_name": "Castor",
        "bayer": "Alpha Geminorum",
        "constellation": "Gêmeos",
        "magnitude": 1.58,
        "nature": "Mercúrio",
        "significance": "O Gêmeo Mortal. Intelecto brilhante e veloz, literatura, invenção da imprensa, tratados diplomáticos e dualidade política."
    },
    {
        "key": "Pollux",
        "search_name": "Pollux",
        "bayer": "Beta Geminorum",
        "constellation": "Gêmeos",
        "magnitude": 1.16,
        "nature": "Marte",
        "significance": "O Gêmeo Imortal. Força combativa indomável, determinação inquebrantável, coragem militar e audácia perante adversidades colossais."
    },
    {
        "key": "Procyon",
        "search_name": "Procyon",
        "bayer": "Alpha Canis Minoris",
        "constellation": "Cão Menor",
        "magnitude": 0.34,
        "nature": "Mercúrio / Marte",
        "significance": "Aquele que antecede o Cão. Ação rápida que precede grandes acontecimentos, ascensão prematura, pioneirismo fulgurante."
    },
    {
        "key": "Regulus",
        "search_name": "Regulus",
        "bayer": "Alpha Leonis",
        "constellation": "Leão",
        "magnitude": 1.36,
        "nature": "Marte / Júpiter",
        "significance": "O Coração do Leão / Sentinela do Norte da Pérsia. Soberania régia suprema, autoridade de Estado máxima, mas risco de queda abrupta caso haja soberba."
    },
    {
        "key": "Alphard",
        "search_name": "Alphard",
        "bayer": "Alpha Hydrae",
        "constellation": "Hidra",
        "magnitude": 1.99,
        "nature": "Saturno / Vênus",
        "significance": "O Coração da Serpente Solitária. Sabedoria oculta, passionalidade intensa, controle de segredos de Estado, venenos e antídotos sociais."
    },
    {
        "key": "Vindemiatrix",
        "search_name": "Vindemiatrix",
        "bayer": "Epsilon Virginis",
        "constellation": "Virgem",
        "magnitude": 2.85,
        "nature": "Saturno / Mercúrio",
        "significance": "A Vindimadora. Colheita de resultados após longos ciclos, auditoria analítica severa, prestação de contas históricas ou perdas de liderança."
    },
    {
        "key": "Spica",
        "search_name": "Spica",
        "bayer": "Alpha Virginis",
        "constellation": "Virgem",
        "magnitude": 0.98,
        "nature": "Vênus / Marte",
        "significance": "A Espiga Sagrada de Virgem. O maior símbolo benéfico de proteção, colheita fecunda, dons científicos, paz e elevação cultural."
    },
    {
        "key": "Arcturus",
        "search_name": "Arcturus",
        "bayer": "Alpha Boötis",
        "constellation": "Boieiro",
        "magnitude": -0.05,
        "nature": "Marte / Júpiter",
        "significance": "O Guardião do Urso. Pioneirismo audacioso, liderança protetora dos vulneráveis, abertura de rotas desconhecidas e viagens civilizatórias."
    },
    {
        "key": "Zubenelgenubi",
        "search_name": "Zubenelgenubi",
        "bayer": "Alpha Librae",
        "constellation": "Balança",
        "magnitude": 2.75,
        "nature": "Saturno / Marte",
        "significance": "A Garra Sul da Balança. Julgamentos implacáveis, desequilíbrio social exigindo reformas de justiça profundas, sanções e rupturas legais."
    },
    {
        "key": "Zubeneschamali",
        "search_name": "Zubeneschamali",
        "bayer": "Beta Librae",
        "constellation": "Balança",
        "magnitude": 2.61,
        "nature": "Júpiter / Mercúrio",
        "significance": "A Garra Norte da Balança. Ascensão por vias diplomáticas, honra institucional, prestígio legislativo e pacificação de conflitos."
    },
    {
        "key": "Agena",
        "search_name": "Agena",
        "bayer": "Beta Centauri",
        "constellation": "Centauro (Hadar)",
        "magnitude": 0.61,
        "nature": "Vênus / Júpiter",
        "significance": "Hadar. Moralidade refinada, capacidade curativa coletiva, alianças estratégicas nobres e integridade de propósito histórico."
    },
    {
        "key": "Antares",
        "search_name": "Antares",
        "bayer": "Alpha Scorpii",
        "constellation": "Escorpião",
        "magnitude": 1.06,
        "nature": "Marte / Júpiter",
        "significance": "O Coração do Escorpião / Sentinela do Ocidente da Pérsia. O Rival de Marte; obstinação bélica extrema, choque frontal histórico e coragem inflexível."
    },
    {
        "key": "Ras Alhague",
        "search_name": "Ras Alhague",
        "bayer": "Alpha Ophiuchi",
        "constellation": "Ofiúco",
        "magnitude": 2.08,
        "nature": "Saturno / Vênus",
        "significance": "A Cabeça do Encantador de Serpentes. Medicina, erradicação de pestes e epidemias, biotecnologia e fármacos que transformam a saúde humana."
    },
    {
        "key": "Vega",
        "search_name": "Vega",
        "bayer": "Alpha Lyrae",
        "constellation": "Lira",
        "magnitude": 0.03,
        "nature": "Vênus / Mercúrio",
        "significance": "A Harpa Celeste. Magnetismo artístico prodigioso, eloquência inspiradora perante massas, criatividade e idealismo que move povos."
    },
    {
        "key": "Altair",
        "search_name": "Altair",
        "bayer": "Alpha Aquilae",
        "constellation": "Águia",
        "magnitude": 0.77,
        "nature": "Marte / Júpiter",
        "significance": "A Águia Alada. Audácia visionária, conquista militar aérea e espacial, ambição resoluta e visão panorâmica das conjunturas geopolíticas."
    },
    {
        "key": "Fomalhaut",
        "search_name": "Fomalhaut",
        "bayer": "Alpha Piscis Austrini",
        "constellation": "Peixe Austral",
        "magnitude": 1.17,
        "nature": "Vênus / Mercúrio",
        "significance": "A Boca do Peixe / Sentinela do Sul da Pérsia. Idealismo espiritual elevado, transmutações morais, nobreza humanitária e grandes visões utópicas."
    },
    {
        "key": "Deneb",
        "search_name": "Deneb",
        "bayer": "Alpha Cygni",
        "constellation": "Cisne",
        "magnitude": 1.25,
        "nature": "Mercúrio / Vênus",
        "significance": "A Cauda do Cisne. Discernimento analítico supremo, pensamento científico rigoroso, raciocínio lógico claro e liberdade intelectual."
    },
    {
        "key": "Achernar",
        "search_name": "Achernar",
        "bayer": "Alpha Eridani",
        "constellation": "Erídano",
        "magnitude": 0.45,
        "nature": "Júpiter",
        "significance": "A Foz do Rio Sagrado. Ética superior, expedições transoceânicas, reformas religiosas e passagens definitivas de ciclos civilizatórios."
    },
    {
        "key": "Markab",
        "search_name": "Markab",
        "bayer": "Alpha Pegasi",
        "constellation": "Pégaso",
        "magnitude": 2.49,
        "nature": "Marte / Mercúrio",
        "significance": "A Sela de Pégaso. Honra militar austera, perseverança estoica perante reveses, perigo de explosões e incêndios catastróficos."
    },
    {
        "key": "Scheat",
        "search_name": "Scheat",
        "bayer": "Beta Pegasi",
        "constellation": "Pégaso",
        "magnitude": 2.44,
        "nature": "Marte / Mercúrio",
        "significance": "A Perna de Pégaso. Intelecto original profundo, desastres marítimos, inundações, rupturas de barragens e revoluções mentais extremas."
    }
]

def parse_date_to_julian_day(date_str: str, time_str: str = "desconhecido", longitude: float = 0.0) -> Tuple[float, bool]:
    """Converte data e hora em Dia Juliano UT com calendário Gregoriano ou Juliano."""
    parts = date_str.strip().split("-")
    if len(parts) == 4 and date_str.startswith("-"):
        year = -int(parts[1])
        month = int(parts[2])
        day = int(parts[3])
    elif len(parts) == 3:
        year = int(parts[0])
        month = int(parts[1])
        day = int(parts[2])
    else:
        raise ValueError(f"Formato de data inválido: {date_str}")

    is_time_known = False
    hour_decimal = 12.0

    if time_str and time_str.lower() != "desconhecido" and ":" in time_str:
        try:
            h, m = time_str.strip().split(":")
            local_hour = int(h) + int(m) / 60.0
            tz_offset_hours = round(longitude / 15.0)
            ut_hour = local_hour - tz_offset_hours
            while ut_hour < 0:
                ut_hour += 24
            while ut_hour >= 24:
                ut_hour -= 24
            hour_decimal = ut_hour
            is_time_known = True
        except Exception:
            hour_decimal = 12.0
            is_time_known = False

    if year > 1582 or (year == 1582 and (month > 10 or (month == 10 and day >= 15))):
        cal_flag = swe.GREG_CAL
    else:
        cal_flag = swe.JUL_CAL

    tjd_ut = swe.julday(year, month, day, hour_decimal, cal_flag)
    return tjd_ut, is_time_known

def degree_to_sign_info(abs_deg: float) -> Dict[str, Any]:
    """Converte graus absolutos (0..360) em dados zodiacais formatados."""
    norm_deg = abs_deg % 360.0
    sign_idx = int(norm_deg // 30)
    sign_obj = ZODIAC_SIGNS[sign_idx]
    deg_in_sign = norm_deg % 30.0
    deg_int = int(deg_in_sign)
    minutes = int((deg_in_sign - deg_int) * 60)
    seconds = int(round((((deg_in_sign - deg_int) * 60) - minutes) * 60))
    if seconds >= 60:
        minutes += 1
        seconds = 0
    if minutes >= 60:
        deg_int += 1
        minutes = 0

    formatted = f"{deg_int}°{minutes:02d}' {sign_obj['name']}"
    short_formatted = f"{deg_int}°{sign_obj['symbol']}{minutes:02d}'"

    return {
        "abs_degree": round(norm_deg, 4),
        "sign_name": sign_obj["name"],
        "sign_symbol": sign_obj["symbol"],
        "sign_index": sign_idx,
        "degree_in_sign": round(deg_in_sign, 4),
        "formatted": formatted,
        "short_formatted": short_formatted,
        "element": sign_obj["element"],
        "modality": sign_obj["modality"],
        "ruler": sign_obj["ruler"]
    }

def calculate_natal_bodies(tjd_ut: float) -> List[Dict[str, Any]]:
    """Calcula planetas, luminares, asteroides e pontos especiais."""
    bodies_data = []

    for b in BODIES_DEFINITIONS:
        try:
            res, _ = swe.calc_ut(tjd_ut, b["swe_id"])
            lon = res[0]
            lat = res[1]
            dist = res[2]
            speed = res[3]
            is_retrograde = speed < 0.0

            sign_info = degree_to_sign_info(lon)

            bodies_data.append({
                "id": b["id"],
                "name": b["name"],
                "symbol": b["symbol"],
                "category": b["category"],
                "weight": b["weight"],
                "longitude": round(lon, 4),
                "latitude": round(lat, 4),
                "distance": round(dist, 5),
                "speed": round(speed, 5),
                "is_retrograde": is_retrograde,
                "sign_name": sign_info["sign_name"],
                "sign_symbol": sign_info["sign_symbol"],
                "sign_index": sign_info["sign_index"],
                "degree_in_sign": sign_info["degree_in_sign"],
                "formatted": sign_info["formatted"],
                "short_formatted": sign_info["short_formatted"],
                "element": sign_info["element"],
                "modality": sign_info["modality"],
                "ruler": sign_info["ruler"]
            })
        except Exception:
            pass

    return bodies_data

def calculate_strict_aspects(bodies: List[Dict[str, Any]], max_orb: float = 3.0) -> List[Dict[str, Any]]:
    """
    Calcula aspectos maiores estritos (Conjunção, Oposição, Quadratura, Trígono)
    com orbe máximo estrito de 3.0 graus.
    """
    aspects = []
    n = len(bodies)

    for i in range(n):
        b1 = bodies[i]
        for j in range(i + 1, n):
            b2 = bodies[j]

            diff = abs(b1["longitude"] - b2["longitude"])
            if diff > 180.0:
                diff = 360.0 - diff

            for asp in STRICT_ASPECT_DEFINITIONS:
                orb_diff = abs(diff - asp["angle"])
                if orb_diff <= max_orb:
                    exactness = round(100.0 * (1.0 - (orb_diff / max_orb)), 1)
                    
                    outer_planets = {"jupiter", "saturn", "uranus", "neptune", "pluto"}
                    is_outer_cycle = (b1["id"] in outer_planets) and (b2["id"] in outer_planets)

                    aspects.append({
                        "planet1_id": b1["id"],
                        "planet1_name": b1["name"],
                        "planet1_symbol": b1["symbol"],
                        "planet2_id": b2["id"],
                        "planet2_name": b2["name"],
                        "planet2_symbol": b2["symbol"],
                        "aspect_name": asp["name"],
                        "aspect_symbol": asp["symbol"],
                        "target_angle": asp["angle"],
                        "exact_angle": round(diff, 2),
                        "orb": round(orb_diff, 2),
                        "exactness_percent": exactness,
                        "nature": asp["nature"],
                        "tension_value": asp["tension"],
                        "is_outer_cycle": is_outer_cycle
                    })
                    break

    return aspects

def calculate_fixed_stars(tjd_ut: float) -> List[Dict[str, Any]]:
    """
    Calcula as posições astronômicas exatas das 30 principais estrelas fixas
    para o instante juliano do evento (considerando precessão e movimento próprio).
    """
    stars_data = []

    for s in FIXED_STARS_CATALOG:
        try:
            res, _, _ = swe.fixstar2_ut(s["search_name"], tjd_ut)
            lon = res[0]
            lat = res[1]
            sign_info = degree_to_sign_info(lon)

            stars_data.append({
                "key": s["key"],
                "name": s["key"],
                "bayer": s["bayer"],
                "constellation": s["constellation"],
                "magnitude": s["magnitude"],
                "nature": s["nature"],
                "significance": s["significance"],
                "longitude": round(lon, 4),
                "latitude": round(lat, 4),
                "sign_name": sign_info["sign_name"],
                "sign_symbol": sign_info["sign_symbol"],
                "degree_in_sign": sign_info["degree_in_sign"],
                "formatted": sign_info["formatted"]
            })
        except Exception:
            pass

    return stars_data

def calculate_fixed_star_aspects(bodies: List[Dict[str, Any]], fixed_stars: List[Dict[str, Any]], max_orb: float = 0.3) -> List[Dict[str, Any]]:
    """
    Identifica contatos por Conjunção estrita (0° ± 0.3° / 18 minutos) entre corpos
    celestes e as estrelas fixas.
    Restringe estritamente a conjunções para eliminar a taxa de aspectos falsos ao acaso.
    """
    star_contacts = []

    for b in bodies:
        for s in fixed_stars:
            diff = abs(b["longitude"] - s["longitude"])
            if diff > 180.0:
                diff = 360.0 - diff

            if diff <= max_orb:
                exactness = round(100.0 * (1.0 - (diff / max_orb)), 1)
                star_contacts.append({
                    "body_id": b["id"],
                    "body_name": b["name"],
                    "body_symbol": b["symbol"],
                    "star_key": s["key"],
                    "star_name": s["key"],
                    "star_bayer": s["bayer"],
                    "star_significance": s["significance"],
                    "aspect_name": "Conjunção",
                    "aspect_symbol": "☌",
                    "target_angle": 0.0,
                    "exact_angle": round(diff, 3),
                    "orb": round(diff, 3),
                    "exactness_percent": exactness,
                    "nature": "intenso"
                })

    return star_contacts

def calculate_houses(tjd_ut: float, latitude: float, longitude: float, is_time_known: bool) -> Dict[str, Any]:
    """Calcula as casas astrológicas (Placidus ou Carta Solar)."""
    if not is_time_known:
        return {
            "houses_available": False,
            "system": "Solar (Horário Desconhecido)",
            "ascendant": None,
            "midheaven": None,
            "cusps": []
        }

    try:
        cusps_tuple, ascmc_tuple = swe.houses(tjd_ut, latitude, longitude, b'P')
        asc_deg = ascmc_tuple[0]
        mc_deg = ascmc_tuple[1]
        
        asc_info = degree_to_sign_info(asc_deg)
        mc_info = degree_to_sign_info(mc_deg)
        
        cusps_list = []
        for idx, c_deg in enumerate(cusps_tuple):
            house_num = idx + 1
            c_info = degree_to_sign_info(c_deg)
            cusps_list.append({
                "house": house_num,
                "degree": round(c_deg, 4),
                "sign_name": c_info["sign_name"],
                "sign_symbol": c_info["sign_symbol"],
                "formatted": c_info["formatted"]
            })

        return {
            "houses_available": True,
            "system": "Placidus",
            "ascendant": {
                "degree": round(asc_deg, 4),
                "formatted": asc_info["formatted"],
                "sign_name": asc_info["sign_name"],
                "sign_symbol": asc_info["sign_symbol"]
            },
            "midheaven": {
                "degree": round(mc_deg, 4),
                "formatted": mc_info["formatted"],
                "sign_name": mc_info["sign_name"],
                "sign_symbol": mc_info["sign_symbol"]
            },
            "cusps": cusps_list
        }
    except Exception as e:
        return {
            "houses_available": False,
            "system": f"Erro de cálculo: {str(e)}",
            "ascendant": None,
            "midheaven": None,
            "cusps": []
        }

def calculate_chart_summary(bodies: List[Dict[str, Any]], aspects: List[Dict[str, Any]], star_contacts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calcula balanço elementar, ritmos e score de tensão com estrelas fixas."""
    elements = {"Fogo": 0, "Terra": 0, "Ar": 0, "Água": 0}
    modalities = {"Cardinal": 0, "Fixo": 0, "Mutável": 0}

    weighted_tension = 0.0

    for b in bodies:
        elem = b["element"]
        mode = b["modality"]
        if elem in elements:
            elements[elem] += 1
        if mode in modalities:
            modalities[mode] += 1

    tense_count = 0
    harmonious_count = 0
    outer_cycle_count = 0

    for a in aspects:
        w_asp = a["tension_value"]
        if a["is_outer_cycle"]:
            w_asp *= 1.5
            outer_cycle_count += 1
        
        weighted_tension += w_asp
        if a["nature"] == "tenso":
            tense_count += 1
        elif a["nature"] == "harmonico":
            harmonious_count += 1

    # Contatos com estrelas fixas intensas aumentam peso
    for sc in star_contacts:
        if sc["star_key"] in ["Algol", "Antares", "Menkar", "Scheat"]:
            weighted_tension += 2.0
        elif sc["star_key"] in ["Sirius", "Spica", "Regulus"]:
            weighted_tension += 0.5

    raw_score = 50.0 + (weighted_tension * 4.0)
    tension_index = max(10.0, min(100.0, round(raw_score, 1)))

    dominant_element = max(elements, key=elements.get)
    dominant_modality = max(modalities, key=modalities.get)

    # Calcular versão de alta resolução 0-1000 pontos
    score_1000_data = calculate_chart_tension_1000({"aspects": aspects, "star_contacts": star_contacts})

    return {
        "elements": elements,
        "modalities": modalities,
        "dominant_element": dominant_element,
        "dominant_modality": dominant_modality,
        "tense_aspects_count": tense_count,
        "harmonious_aspects_count": harmonious_count,
        "outer_cycles_count": outer_cycle_count,
        "star_contacts_count": len(star_contacts),
        "tension_index": tension_index,
        "tension_index_1000": score_1000_data["tension_index_1000"],
        "sub_indices_1000": score_1000_data
    }

OUTER_BODIES = {"pluto", "neptune", "uranus", "saturn"}
WAR_DESTRUCTIVE_STARS = {"Algol", "Antares", "Bellatrix", "Scheat", "Menkar"}
ROYAL_STARS = {"Sirius", "Regulus", "Aldebaran", "Spica", "Vega", "Arcturus"}

def calculate_chart_tension_1000(chart: Dict[str, Any]) -> Dict[str, float]:
    """
    Calcula a Tensão Cósmica e Sub-índices na Escala de Alta Resolução (0 a 1000 pontos).
    Elimina o piso e teto artificiais, aplicando decaimento de orbe proporcional,
    hierarquia arquetípica moderna e contraste dinâmico calibrado.
    """
    aspects = chart.get("aspects", [])
    star_contacts = chart.get("star_contacts", [])

    base_score = 60.0
    tension_pts = 0.0
    harmony_pts = 0.0

    conflict_accum = 0.0
    economic_accum = 0.0
    tech_accum = 0.0
    social_accum = 0.0

    for a in aspects:
        orb = a.get("orb", 3.0)
        orb_factor = max(0.0, (3.0 - orb) / 3.0)

        p1 = a.get("planet1_id", "")
        p2 = a.get("planet2_id", "")
        nature = a.get("nature", "neutro")
        asp_name = a.get("aspect_name", "")

        is_outer_outer = (p1 in OUTER_BODIES and p2 in OUTER_BODIES)
        is_saturn_pluto = (p1 == "saturn" and p2 == "pluto") or (p2 == "saturn" and p1 == "pluto")
        is_uranus_pluto = (p1 == "uranus" and p2 == "pluto") or (p2 == "uranus" and p1 == "pluto")
        is_saturn_uranus = (p1 == "saturn" and p2 == "uranus") or (p2 == "saturn" and p1 == "uranus")
        is_saturn_neptune = (p1 == "saturn" and p2 == "neptune") or (p2 == "saturn" and p1 == "neptune")

        has_mars = ("mars" in (p1, p2))
        mars_outer = has_mars and (p1 in OUTER_BODIES or p2 in OUTER_BODIES)
        has_luminary_outer = ("sun" in (p1, p2) or "moon" in (p1, p2)) and (p1 in OUTER_BODIES or p2 in OUTER_BODIES)

        if nature == "tenso":  # Quadratura (90°) ou Oposição (180°)
            if is_saturn_pluto:
                val = 260.0
                conflict_accum += 200.0 * orb_factor
                social_accum += 180.0 * orb_factor
            elif is_uranus_pluto or is_saturn_uranus:
                val = 220.0
                social_accum += 200.0 * orb_factor
                economic_accum += 180.0 * orb_factor
            elif is_saturn_neptune:
                val = 200.0
                social_accum += 170.0 * orb_factor
                conflict_accum += 150.0 * orb_factor
            elif is_outer_outer:
                val = 170.0
                social_accum += 140.0 * orb_factor
            elif mars_outer:
                val = 130.0
                conflict_accum += 220.0 * orb_factor
            elif has_luminary_outer:
                val = 75.0
                conflict_accum += 70.0 * orb_factor
            else:
                val = 40.0

            tension_pts += val * orb_factor
            economic_accum += val * 0.6 * orb_factor

        elif asp_name == "Conjunção":  # 0°
            if is_saturn_pluto:
                val = 250.0
                conflict_accum += 190.0 * orb_factor
                social_accum += 180.0 * orb_factor
            elif is_saturn_neptune:
                val = 220.0
                social_accum += 180.0 * orb_factor
            elif is_uranus_pluto:
                val = 200.0
                tech_accum += 180.0 * orb_factor
                social_accum += 170.0 * orb_factor
            elif is_outer_outer:
                val = 160.0
                social_accum += 140.0 * orb_factor
            elif mars_outer:
                val = 110.0
                conflict_accum += 180.0 * orb_factor
            elif has_luminary_outer:
                val = 60.0
            else:
                val = 30.0

            tension_pts += val * orb_factor

        elif nature == "harmonico":  # Trígono (120°)
            val = 35.0 if is_outer_outer else 15.0
            harmony_pts += val * orb_factor
            tech_accum += (val * 2.5) * orb_factor

    # Estrelas Fixas (orbe estrito 0.3°)
    star_pts = 0.0
    for s in star_contacts:
        orb = s.get("orb", 0.3)
        star_factor = max(0.0, (0.3 - orb) / 0.3)
        sk = s.get("star_key")
        body_id = s.get("body_id")

        if sk in WAR_DESTRUCTIVE_STARS:
            m = 160.0 if (body_id in OUTER_BODIES or body_id in ("mars", "sun")) else 80.0
            star_pts += m * star_factor
            conflict_accum += m * 1.2 * star_factor
        elif sk in ROYAL_STARS:
            star_pts += 50.0 * star_factor
            social_accum += 50.0 * star_factor
        else:
            star_pts += 20.0 * star_factor

    raw_total = base_score + tension_pts + star_pts - (harmony_pts * 0.2)

    # Conversão para Percentil Empírico (sem saturação em 990)
    try:
        from src.core.ephemeris_grid import raw_score_to_percentile_1000
        tension_1000 = raw_score_to_percentile_1000(raw_total)
    except Exception:
        # Fallback se a grade ainda não estiver carregada
        tension_1000 = round(min(1000.0, max(1.0, raw_total * 1.5)), 1)

    conflict_1000 = round(min(1000.0, max(10.0, ((conflict_accum + star_pts * 0.8) / 550.0) * 1000.0)), 1)
    crisis_1000 = round(min(1000.0, max(10.0, ((economic_accum + tension_pts * 0.5) / 520.0) * 1000.0)), 1)
    tech_1000 = round(min(1000.0, max(10.0, ((tech_accum + harmony_pts * 1.5) / 480.0) * 1000.0)), 1)
    social_1000 = round(min(1000.0, max(10.0, ((social_accum + tension_pts * 0.6) / 520.0) * 1000.0)), 1)

    return {
        "tension_index_1000": tension_1000,
        "conflict_risk_index_1000": conflict_1000,
        "crisis_risk_index_1000": crisis_1000,
        "tech_innovation_index_1000": tech_1000,
        "social_transformation_index_1000": social_1000
    }

def calculate_event_chart(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Processa a carta natal completa com planetas, asteroides,
    aspectos estritos (orbe 3.0°), 30 estrelas fixas (orbe 0.3°) e casas.
    """
    date_str = event["date"]
    time_str = event.get("time", "desconhecido")
    lat = float(event.get("latitude", 0.0))
    lon = float(event.get("longitude", 0.0))

    tjd_ut, is_time_known = parse_date_to_julian_day(date_str, time_str, lon)
    
    # 1. Planetas, Luminares, Asteroides e Pontos
    bodies = calculate_natal_bodies(tjd_ut)
    for b in bodies:
        b["is_time_uncertain"] = (not is_time_known and b["id"] == "moon")
    
    # Para eventos sem hora exata, excluir a Lua do score e dos aspectos (P1-1: ~13°/dia = ruído)
    scoring_bodies = [b for b in bodies if not (not is_time_known and b["id"] == "moon")]
    
    # 2. Aspectos estritos entre corpos (orbe 3.0°)
    aspects = calculate_strict_aspects(scoring_bodies, max_orb=3.0)
    
    # 3. 30 Principais Estrelas Fixas
    fixed_stars = calculate_fixed_stars(tjd_ut)
    
    # 4. Aspectos e Conjunções com Estrelas Fixas (orbe 0.3° estrito)
    star_contacts = calculate_fixed_star_aspects(scoring_bodies, fixed_stars, max_orb=0.3)
    
    # 5. Casas e Eixos
    houses = calculate_houses(tjd_ut, lat, lon, is_time_known)
    
    # 6. Sumário Analítico
    summary = calculate_chart_summary(scoring_bodies, aspects, star_contacts)

    return {
        "event_id": event.get("id"),
        "tjd_ut": round(tjd_ut, 5),
        "is_time_known": is_time_known,
        "planets": bodies,             # Contém os 17 corpos celestes (planetas + asteroides)
        "aspects": aspects,             # Aspectos maiores estritos com orbe 3.0°
        "fixed_stars": fixed_stars,     # Posições das 30 estrelas fixas
        "star_contacts": star_contacts, # Alinhamentos com estrelas fixas (orbe <= 0.3°)
        "houses": houses,
        "summary": summary
    }
