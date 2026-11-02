"""
Renderizador SVG Bi-Wheel para Astrologia Mundana (Carta Natal da Nação + Trânsitos).
Gera visualização vetorial precisa, responsiva e esteticamente moderna.
Trata explicitamente:
- Mapas sem horário: Zodíaco Natural sem cúspides de casas (Carta Solar rigorosa).
- Mapas com horário: Cúspides Placidus com Ascendente e Meio-do-Céu.
"""

import math
from typing import Dict, List, Any

SIGN_COLORS = {
    "Fogo": "#ef4444",    # Vermelho
    "Terra": "#10b981",   # Verde
    "Ar": "#f59e0b",      # Âmbar
    "Água": "#0284c7"     # Ciano
}

ZODIAC_GLYPHS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]

def generate_biwheel_svg(
    country_chart: Dict[str, Any],
    transits_data: Dict[str, Any],
    width: int = 600,
    height: int = 600
) -> str:
    """Gera o código SVG para renderização Bi-Wheel: Nações (Interno) + Trânsitos (Externo)."""
    cx = width / 2.0
    cy = height / 2.0

    # Raios dos círculos concêntricos
    r_outer_border = 285.0
    r_transit_ring = 250.0
    r_transit_inner = 220.0
    r_signs_outer = 220.0
    r_signs_inner = 175.0
    r_natal_ring = 140.0
    r_center = 105.0

    # Rotação: Se houver casas e Ascendente, alinha o Ascendente a Leste (180°).
    # Se não houver casas (is_time_known = False), 0° Áries fica alinhado a 180° (horizonte natural esquerdo).
    rotation_offset = 180.0
    houses = country_chart.get("houses", {})
    if houses.get("houses_available") and houses.get("ascendant"):
        asc_deg = houses["ascendant"]["degree"]
        rotation_offset = 180.0 - asc_deg

    def deg_to_xy(deg: float, radius: float):
        angle_rad = math.radians(180.0 - (deg + rotation_offset))
        x = cx + radius * math.cos(angle_rad)
        y = cy + radius * math.sin(angle_rad)
        return x, y

    svg = []
    svg.append(f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="w-full h-full filter drop-shadow-2xl select-none">')

    # Fundo escuro circular
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_outer_border}" fill="#070b14" stroke="#1e293b" stroke-width="2"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_transit_ring}" fill="#0b1329" stroke="#334155" stroke-width="1.5"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_signs_outer}" fill="#0f172a" stroke="#475569" stroke-width="2"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_signs_inner}" fill="#0b1120" stroke="#334155" stroke-width="1.5"/>')
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="{r_center}" fill="#030712" stroke="#334155" stroke-width="1" stroke-dasharray="3,3"/>')

    # Desenho dos 12 Signos do Zodíaco
    for i in range(12):
        start_deg = i * 30.0
        mid_deg = start_deg + 15.0
        elem = ["Fogo", "Terra", "Ar", "Água"][i % 4]
        elem_color = SIGN_COLORS[elem]

        # Linhas divisórias dos signos
        x1, y1 = deg_to_xy(start_deg, r_signs_inner)
        x2, y2 = deg_to_xy(start_deg, r_signs_outer)
        svg.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#334155" stroke-width="1.2"/>')

        # Símbolo do Signo
        gx, gy = deg_to_xy(mid_deg, (r_signs_outer + r_signs_inner) / 2.0)
        glyph = ZODIAC_GLYPHS[i]
        svg.append(f'<text x="{gx:.1f}" y="{gy + 5:.1f}" font-size="16" font-family="sans-serif" text-anchor="middle" fill="{elem_color}" font-weight="bold">{glyph}</text>')

    # Linhas de Casas Astrológicas (SOMENTE se houver horário conhecido)
    if houses.get("houses_available") and houses.get("cusps"):
        for cusp in houses["cusps"]:
            h_deg = cusp["degree"]
            hx1, hy1 = deg_to_xy(h_deg, r_center)
            hx2, hy2 = deg_to_xy(h_deg, r_signs_inner)
            is_angle = cusp["house"] in [1, 4, 7, 10]
            s_width = "1.8" if is_angle else "0.8"
            s_color = "#fbbf24" if is_angle else "#475569"
            svg.append(f'<line x1="{hx1:.1f}" y1="{hy1:.1f}" x2="{hx2:.1f}" y2="{hy2:.1f}" stroke="{s_color}" stroke-width="{s_width}" stroke-dasharray="none"/>')

    # Linhas dos Aspectos de Trânsito no Centro da Mandala
    natal_map = {p["id"]: p for p in country_chart.get("planets", [])}
    transit_map = {p["id"]: p for p in transits_data.get("transit_bodies", [])}

    transits_list = transits_data.get("transits", [])
    for asp in transits_list:
        t_planet = transit_map.get(asp["transit_planet_id"])
        n_planet = natal_map.get(asp["natal_planet_id"])
        if t_planet and n_planet:
            tx, ty = deg_to_xy(t_planet["longitude"], r_center - 10)
            nx, ny = deg_to_xy(n_planet["longitude"], r_center - 10)

            # Cor do aspecto
            if asp["aspect_nature"] == "tenso":
                stroke_color = "#f43f5e" # Vermelho
                stroke_width = "1.8" if asp["is_exact"] else "1.1"
                opacity = "0.85" if asp["is_exact"] else "0.55"
            elif asp["aspect_nature"] == "transformação profunda":
                stroke_color = "#a855f7" # Roxo
                stroke_width = "2.0"
                opacity = "0.9"
            elif asp["aspect_name"] == "Conjunção":
                stroke_color = "#fbbf24" # Dourado
                stroke_width = "2.2"
                opacity = "0.9"
            else:
                stroke_color = "#38bdf8" # Azul claro
                stroke_width = "1.4" if asp["is_exact"] else "0.9"
                opacity = "0.7" if asp["is_exact"] else "0.4"

            svg.append(f'<line x1="{tx:.1f}" y1="{ty:.1f}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-opacity="{opacity}"/>')

    # Desenho dos Planetas Natais do País (Anel Interno)
    for p in country_chart.get("planets", []):
        px, py = deg_to_xy(p["longitude"], r_natal_ring)
        dot_x, dot_y = deg_to_xy(p["longitude"], r_signs_inner)

        svg.append(f'<circle cx="{dot_x:.1f}" cy="{dot_y:.1f}" r="2" fill="#fbbf24"/>')
        svg.append(f'<line x1="{dot_x:.1f}" y1="{dot_y:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="#475569" stroke-width="0.7" stroke-dasharray="2,2"/>')

        b_symbol = p["symbol"]
        retro = "℞" if p.get("is_retrograde") else ""

        # Cor do planeta natal
        if p["id"] == "sun":
            fill_col = "#fbbf24"
        elif p["id"] == "moon":
            fill_col = "#e2e8f0"
        elif p["id"] in ["pluto", "neptune", "uranus"]:
            fill_col = "#c084fc"
        elif p["id"] in ["mars", "saturn"]:
            fill_col = "#f87171"
        else:
            fill_col = "#38bdf8"

        svg.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="9" fill="#0f172a" stroke="{fill_col}" stroke-width="1.2"/>')
        svg.append(f'<text x="{px:.1f}" y="{py + 3.5:.1f}" font-size="10" font-family="sans-serif" text-anchor="middle" fill="{fill_col}" font-weight="bold">{b_symbol}</text>')
        if retro:
            svg.append(f'<text x="{px + 6:.1f}" y="{py - 4:.1f}" font-size="6" font-family="sans-serif" fill="#f43f5e" font-weight="bold">{retro}</text>')

    # Desenho dos Planetas em Trânsito (Anel Externo)
    for tp in transits_data.get("transit_bodies", []):
        tpx, tpy = deg_to_xy(tp["longitude"], (r_outer_border + r_transit_ring) / 2.0)
        tdot_x, tdot_y = deg_to_xy(tp["longitude"], r_signs_outer)

        svg.append(f'<circle cx="{tdot_x:.1f}" cy="{tdot_y:.1f}" r="2" fill="#38bdf8"/>')
        svg.append(f'<line x1="{tdot_x:.1f}" y1="{tdot_y:.1f}" x2="{tpx:.1f}" y2="{tpy:.1f}" stroke="#64748b" stroke-width="0.8" stroke-dasharray="2,2"/>')

        t_symbol = tp["symbol"]
        t_retro = "℞" if tp.get("is_retrograde") else ""

        svg.append(f'<circle cx="{tpx:.1f}" cy="{tpy:.1f}" r="10" fill="#1e293b" stroke="#38bdf8" stroke-width="1.4"/>')
        svg.append(f'<text x="{tpx:.1f}" y="{tpy + 3.8:.1f}" font-size="11" font-family="sans-serif" text-anchor="middle" fill="#38bdf8" font-weight="bold">{t_symbol}</text>')
        if t_retro:
            svg.append(f'<text x="{tpx + 7:.1f}" y="{tpy - 5:.1f}" font-size="7" font-family="sans-serif" fill="#f43f5e" font-weight="bold">{t_retro}</text>')

    # Centro com indicador visual da nação
    flag = country_chart.get("flag_emoji", "🌐")
    svg.append(f'<circle cx="{cx}" cy="{cy}" r="22" fill="#020617" stroke="#fbbf24" stroke-width="1.5"/>')
    svg.append(f'<text x="{cx:.1f}" y="{cy + 7:.1f}" font-size="18" text-anchor="middle">{flag}</text>')

    # Badge de tipo de mapa no canto superior
    if not country_chart.get("is_time_known"):
        badge_text = "Carta Solar / Sem Casas (Horário Desconhecido)"
        badge_color = "#94a3b8"
    else:
        badge_text = f"Casas Placidus ({country_chart.get('time', '')})"
        badge_color = "#38bdf8"

    svg.append(f'<text x="{cx:.1f}" y="24" font-size="10" font-family="monospace" text-anchor="middle" fill="{badge_color}">{badge_text}</text>')
    svg.append('</svg>')
    return "".join(svg)
