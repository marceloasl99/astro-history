"""
Gera o relatório formal consolidado em Markdown (reports/energy_peaks_2026_2060_report.md)
com base no catálogo expandido data/energy_peaks_2026_2060.json.
"""

import json
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
JSON_PATH = os.path.join(BASE_DIR, "data", "energy_peaks_2026_2060.json")
REPORT_PATH = os.path.join(BASE_DIR, "reports", "energy_peaks_2026_2060_report.md")

with open(JSON_PATH, "r", encoding="utf-8") as f:
    data = json.load(f)

kpis = data["kpis"]
milestones = data["milestone_years"]
dossiers = data["countries_dossiers"]
matrix = data["risk_matrix"]
peaks = data["peaks"]

lines = []
lines.append("# Relatório Prospectivo Estratégico: Picos de Energia Cósmica & Cenários por País (2026–2060)")
lines.append("")
lines.append("> **Plataforma**: AstroHistory v5.0.0 — Astrologia Mundana Computacional  ")
lines.append("> **Efemérides**: Swiss Ephemeris 2.10 (pyswisseph)  ")
lines.append("> **Horizonte Temporal**: 2026 a 2060 (35 anos)  ")
lines.append("> **Critério de Seleção**: Picos de Alta Energia (>= 720/1000 nacional e >= 960/1000 mundial)  ")
lines.append("> **Data de Emissão**: 02 de Novembro de 2026  ")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 1. Sumário Executivo & Panorama da Era")
lines.append("")
lines.append("Este dossiê de inteligência prospectiva consolida uma varredura cronológica de alta resolução das **maiores ativações astronômicas mundiais** e dos **trânsitos mundanos nas cartas oficiais de fundação das 12 principais potências soberanas** entre 2026 e 2060.")
lines.append("")
lines.append(f"- **Total de Picos de Energia Isolados**: **{kpis['total_peaks']}**")
lines.append(f"- **Picos Globais / Mundiais**: {kpis['world_peaks_count']}")
lines.append(f"- **Picos Nacionais em Nações Soberanas**: {kpis['country_peaks_count']}")
lines.append(f"- **Classificação de Intensidade**: **{kpis['critical_count']} Críticos** (>= 800/1000) e **{kpis['high_count']} Altos** (720–799/1000)")
lines.append("- **Distribuição por Cenário Geopolítico**:")
for s_key, s_meta in data["scenario_meta"].items():
    cnt = kpis["by_scenario"].get(s_key, 0)
    pct = round((cnt / kpis["total_peaks"]) * 100, 1)
    lines.append(f"  - {s_meta['icon']} **{s_meta['label_pt']}**: {cnt} picos ({pct}%)")
lines.append("")
lines.append("---")
lines.append("")
lines.append("## 2. Os 7 Grandes Anos de Inflexão da Humanidade")
lines.append("")
lines.append("A análise dos ciclos combinados dos planetas lentos (Plutão, Netuno, Urano e Saturno) identifica 7 marcos de convergência máxima onde múltiplos atores soberanos atingem pontos de estresse simultâneo:")
lines.append("")

for m in milestones:
    lines.append(f"### 🌟 {m['year']}: {m['title_pt']}")
    lines.append(f"- **Gatilho Astronômico Exato**: `{m['cosmic_signature']}`")
    lines.append(f"- **Índice de Tensão Global**: **{m['energy_score']}/1000** ({m['impact_level']})")
    lines.append(f"- **Potências no Epicentro**: " + ", ".join(m["key_actors"]))
    lines.append(f"- **Precedente Histórico Isomórfico**: *{m['historical_precedent']}*")
    lines.append(f"- **Síntese Prospectiva**: {m['summary']}")
    lines.append("")

lines.append("---")
lines.append("")
lines.append("## 3. Dossiês Estratégicos por Potência Soberana")
lines.append("")

for iso, dos in dossiers.items():
    lines.append(f"### {dos['flag']} {dos['name_pt']} ({dos['iso']})")
    lines.append(f"- **Capital**: {dos['capital']} | **Certidão**: {dos['foundation_event']} ({dos['foundation_date']})")
    lines.append(f"- **Ponto Natal Crítico**: `{dos['vulnerability']}`")
    lines.append(f"- **Total de Picos**: {dos['total_peaks_count']} (Críticos: {dos['critical_peaks_count']}) | **Pico Máximo**: {dos['max_score']}/1000")
    lines.append(f"- **Anos Mais Críticos**: " + ", ".join([f"**{y}**" for y in dos["critical_years"]]))
    lines.append(f"- **Diagnóstico Estratégico (2026–2060)**: {dos['strategic_summary']}")
    lines.append("")
    lines.append("**Picos Cronológicos no País**:")
    lines.append("")
    lines.append("| Ano | Data | Cenário | Score | Assinatura Cósmica | Precedente Histórico | Tendência Prospectiva |")
    lines.append("| :---: | :---: | :--- | :---: | :--- | :--- | :--- |")
    for p in dos["peaks"]:
        lines.append(f"| **{p['year']}** | {p['peak_date']} | {p['scenario_icon']} {p['scenario_label_pt']} | **{p['energy_score_1000']}** | `{p['cosmic_signature']}` | {p['historical_precedent_title']} | {p['prospective_synthesis']} |")
    lines.append("")

lines.append("---")
lines.append("")
lines.append("## 4. Matriz Comparativa de Risco Geopolítico (2026–2040)")
lines.append("")
lines.append("Cruzamento visual ano a ano das potências e âmbito mundial. Níveis de alerta: 🚨 **Crítico** (>= 800), ⚠️ **Alto** (>= 720), 🟢 **Estável** (< 720).")
lines.append("")

header = "| Ator | " + " | ".join([str(y) for y in matrix["years"]]) + " |"
sep = "| :--- | " + " | ".join([":---:" for _ in matrix["years"]]) + " |"
lines.append(header)
lines.append(sep)

for row in matrix["rows"]:
    row_cells = [f"{row['flag']} {row['name_pt']}"]
    for cell in row["cells"]:
        if cell["has_peak"]:
            badge = f"{cell['icon']}{int(round(cell['score']))}"
            row_cells.append(badge)
        else:
            row_cells.append("—")
    lines.append("| " + " | ".join(row_cells) + " |")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## 5. Cronologia Integral de Picos de Energia (2026–2060)")
lines.append("")
lines.append("| Ano | Âmbito / País | Cenário | Energia | Alerta | Assinatura Planetária Exata | Precedente Histórico | Tendência do Cenário |")
lines.append("| :---: | :--- | :--- | :---: | :---: | :--- | :--- | :--- |")

for p in peaks:
    lines.append(f"| **{p['year']}** | {p['country_flag']} {p['country_name_pt']} | {p['scenario_icon']} {p['scenario_label_pt']} | **{p['energy_score_1000']}** | {p['alert_level']} | `{p['cosmic_signature']}` | {p['historical_precedent_title']} | {p['prospective_synthesis']} |")

lines.append("")
lines.append("---")
lines.append("")
lines.append("## 6. Aviso Epistemológico & Metodologia")
lines.append("")
lines.append("Os scores de energia e alertas refletem a **geometria astronômica e trânsitos mundanos calculados pela Swiss Ephemeris**, não fatalismo histórico. Na validação out-of-sample por modelos nulos (fases v2 e v3), as correlações astrológicas isoladas não batem os baselines empíricos. Este relatório deve ser interpretado como um mapa de ressonância arquetípica e de sensibilidade dos sistemas soberanos.")

with open(REPORT_PATH, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

print("Relatório salvo em:", REPORT_PATH)
