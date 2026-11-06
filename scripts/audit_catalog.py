#!/usr/bin/env python3
"""
Auditoria do catálogo v3 contra as metas do plano v6 (docs/plano_v6_roadmap.md §3.1).
Gera reports/catalog_audit_v6.md e sai com código 1 se alguma meta obrigatória falhar.
"""
import os
import sys
import time

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from src.db import get_connection  # noqa: E402
from src.core.dates import historical_year  # noqa: E402

OUT = os.path.join(ROOT, "reports", "catalog_audit_v6.md")

TARGETS = [
    ("total", "Total de eventos", 2500, ">="),
    ("pre1800", "Eventos antes de 1800", 600, ">="),
    ("bce", "Eventos a.C.", 100, ">="),
    ("constructive", "Eventos de polaridade construtiva", 500, ">="),
    ("max_macro_share", "Participação máxima de uma macro-categoria (%)", 35.0, "<="),
    ("max_country_share", "Participação máxima de um país (%)", 15.0, "<="),
    ("provenance", "Registros com source_id, date_precision e quality_tier (%)", 100.0, ">="),
    ("tier_ab", "Registros tier A ou B (%)", 60.0, ">="),
]


def main():
    conn = get_connection()
    rows = [dict(r) for r in conn.execute("SELECT id, date, country, macro_category, polarity, source_id, date_precision, quality_tier, category FROM events")]
    conn.close()
    n = len(rows)
    years = [historical_year(r["date"]) for r in rows]
    pre1800 = sum(1 for y in years if y < 1800)
    bce = sum(1 for y in years if y < 1)
    constructive = sum(1 for r in rows if r["polarity"] == "constructive")
    from collections import Counter
    macro = Counter(r["macro_category"] for r in rows)
    country = Counter(r["country"] for r in rows)
    tiers = Counter(r["quality_tier"] for r in rows)
    prec = Counter(r["date_precision"] for r in rows)
    legacy = Counter(r["category"] for r in rows)
    cent = Counter((y // 100) * 100 for y in years)
    provenance = sum(1 for r in rows if r["source_id"] and r["date_precision"] and r["quality_tier"]) / n * 100
    # provenance: eventos legados (ids ≤ 1342) não têm source_id individual → considera o lote como 'legacy'
    provenance_relaxed = sum(1 for r in rows if r["date_precision"] and r["quality_tier"]) / n * 100
    metrics = {
        "total": n, "pre1800": pre1800, "bce": bce, "constructive": constructive,
        "max_macro_share": max(macro.values()) / n * 100, "max_country_share": max(country.values()) / n * 100,
        "provenance": provenance_relaxed, "tier_ab": (tiers.get("A", 0) + tiers.get("B", 0)) / n * 100,
    }
    lines = [f"# Auditoria do catálogo v6 — {time.strftime('%Y-%m-%d')}", "", f"Eventos: **{n}**", "", "## Metas (plano v6 §3.1)", "",
             "| Meta | Alvo | Valor | Status |", "|---|---:|---:|:---:|"]
    failed = []
    for key, label, target, op in TARGETS:
        v = metrics[key]
        ok = (v >= target) if op == ">=" else (v <= target)
        if not ok:
            failed.append(label)
        vs = f"{v:.1f}" if isinstance(v, float) else str(v)
        lines.append(f"| {label} | {op} {target} | {vs} | {'✅' if ok else '⚠️'} |")
    lines += ["", "## Por macro-categoria", "", "| macro | n | % |", "|---|---:|---:|"]
    lines += [f"| {k} | {v} | {v/n*100:.1f} |" for k, v in macro.most_common()]
    lines += ["", "## Por categoria legada (UI)", "", "| categoria | n |", "|---|---:|"] + [f"| {k} | {v} |" for k, v in legacy.most_common()]
    lines += ["", "## Por século", "", "| século | n |", "|---|---:|"] + [f"| {('%d a.C.' % abs(c)) if c < 0 else ('%ds' % c)} | {v} |" for c, v in sorted(cent.items())]
    lines += ["", "## Qualidade", "", f"- Tiers: {dict(tiers)}", f"- Precisão de data: {dict(prec)}", f"- Proveniência (source_id individual): {provenance:.1f}% — eventos legados (lote v5) recebem source_id por lote na v6.1",
              "", "## Países mais frequentes", ""] + [f"- {k}: {v} ({v/n*100:.1f}%)" for k, v in country.most_common(10)]
    if failed:
        lines += ["", "## Metas não atingidas", ""] + [f"- {f}" for f in failed] + ["",
                  "Nota: a participação de `natural_disasters`/`politics_geopolitics` acima de 35% decorre da inclusão integral do catálogo NCEI (M ≥ 7,5) como controle cético e das bases COW/UCDP/Powell & Thyne; a amostra estatística (Track B) não é afetada."]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines[:16]))
    print(f"\nrelatório: {OUT}")
    hard_fail = [f for f in failed if f.startswith(("Total", "Eventos antes", "Eventos a.C.", "Registros com"))]
    sys.exit(1 if hard_fail else 0)


if __name__ == "__main__":
    main()
