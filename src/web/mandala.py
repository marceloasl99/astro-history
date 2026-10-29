"""
Renderizador SVG para Mandala Astrológica (Roda Zodiacal e Carta Natal).
Versão Refinada com Asteroides e Aspectos Estritos.
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

def generate_mandala_svg(chart_data: Dict[str, Any], width: int = 500, height: int = 500) -> str:
    """Gera o código SVG para renderização da mandala astral com planetas e asteroides."""
    cx = width / 2.0
    cy = height / 2.0
    r_outer = 230.0
    r_signs_inner = 185.0
    r_planets = 145.0
    r_center = 115.0

    rotation_offset = 180.0
    if chart_data.get("houses", {}).get("houses_available") and chart_data["houses"].get("ascendant"):
        asc_deg = chart_data["houses"]["ascendant"]["degree"]
        rotation_offset = 180.0 - asc_deg

    def deg_to_xy(deg: float, radius: float):
        angle_rad = math.radians(180.0 - (deg + rotation_offset))
        x = cx + radius * math.cos(angle_rad)
        y = cy + radius * math.sin(angle_rad)
        return x, y

    svg_parts = []
    svg_parts.append(f'<svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" class="w-full h-full filter drop-shadow-xl select-none">')

    # Fundo escuro circular
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_outer}" fill="#0b1120" stroke="#334155" stroke-width="2"/>')
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_signs_inner}" fill="#070c18" stroke="#1e293b" stroke-width="1.5"/>')
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_center}" fill="#040711" stroke="#334155" stroke-width="1" stroke-dasharray="3,3"/>')

    # Desenho dos 12 Signos do Zodíaco
    for i in range(12):
        start_deg = i * 30.0
        mid_deg = start_deg + 15.0

        elem = ["Fogo", "Terra", "Ar", "Água"][i % 4]
        elem_color = SIGN_COLORS[elem]

        # Linhas divisórias dos signos
        x1, y1 = deg_to_xy(start_deg, r_signs_inner)
        x2, y2 = deg_to_xy(start_deg, r_outer)
        svg_parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#334155" stroke-width="1.2"/>')

        # Símbolo do Signo
        gx, gy = deg_to_xy(mid_deg, (r_outer + r_signs_inner) / 2.0)
        glyph = ZODIAC_GLYPHS[i]
        svg_parts.append(f'<text x="{gx:.1f}" y="{gy + 5:.1f}" font-size="16" font-family="sans-serif" text-anchor="middle" fill="{elem_color}" font-weight="bold">{glyph}</text>')

    # Linhas dos Aspectos Estritos no Centro da Mandala (orbe <= 3.0°)
    aspects = chart_data.get("aspects", [])
    bodies_map = {b["id"]: b for b in chart_data.get("planets", [])}

    for asp in aspects:
        b1 = bodies_map.get(asp["planet1_id"])
        b2 = bodies_map.get(asp["planet2_id"])
        if b1 and b2:
            x1, y1 = deg_to_xy(b1["longitude"], r_center - 10)
            x2, y2 = deg_to_xy(b2["longitude"], r_center - 10)

            stroke_color = "#38bdf8"
            stroke_width = "1.2"
            opacity = "0.6"

            if asp["nature"] == "tenso":
                stroke_color = "#f43f5e"
                stroke_width = "1.5"
                opacity = "0.75"
            elif asp["aspect_name"] == "Conjunção":
                stroke_color = "#fbbf24"
                stroke_width = "1.8"
                opacity = "0.85"

            svg_parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke_color}" stroke-width="{stroke_width}" stroke-opacity="{opacity}"/>')

    # Desenho dos Corpos Celestes (Planetas + Asteroides)
    bodies = chart_data.get("planets", [])
    for b in bodies:
        px, py = deg_to_xy(b["longitude"], r_planets)
        
        # Ponto de marcação na roda
        dot_x, dot_y = deg_to_xy(b["longitude"], r_signs_inner)
        svg_parts.append(f'<circle cx="{dot_x:.1f}" cy="{dot_y:.1f}" r="2" fill="#fbbf24"/>')
        svg_parts.append(f'<line x1="{dot_x:.1f}" y1="{dot_y:.1f}" x2="{px:.1f}" y2="{py:.1f}" stroke="#475569" stroke-width="0.7" stroke-dasharray="2,2"/>')

        b_symbol = b["symbol"]
        retro_mark = "℞" if b.get("is_retrograde") else ""
        
        # Cores por categoria
        b_cat = b.get("category", "planeta")
        if b_cat == "luminar":
            text_fill = "#fbbf24" # Dourado
        elif b_cat == "transpessoal":
            text_fill = "#a855f7" # Roxo
        elif b_cat == "asteroide":
            text_fill = "#34d399" # Verde Menta
        elif b_cat == "ponto" or b_cat == "centauro":
            text_fill = "#f43f5e" # Rosa/Rubi
        else:
            text_fill = "#f1f5f9" # Branco azulado

        svg_parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="10" fill="#0f172a" stroke="{text_fill}" stroke-width="1.1"/>')
        svg_parts.append(f'<text x="{px:.1f}" y="{py + 3.5:.1f}" font-size="11" font-family="sans-serif" text-anchor="middle" fill="{text_fill}">{b_symbol}</text>')
        if retro_mark:
            svg_parts.append(f'<text x="{px + 6:.1f}" y="{py - 5:.1f}" font-size="7" font-family="sans-serif" fill="#f43f5e" font-weight="bold">{retro_mark}</text>')

    # Centro com gradiente sutil
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="15" fill="#020617" stroke="#fbbf24" stroke-width="1.5"/>')
    svg_parts.append(f'<circle cx="{cx}" cy="{cy}" r="3" fill="#fbbf24"/>')

    svg_parts.append('</svg>')
    return "".join(svg_parts)
