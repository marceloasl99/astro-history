import sqlite3
import pytest

DB_PATH = "db/history_astrology.db"

def test_events_v2_schema_and_integrity():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    rows = c.execute("""
        SELECT id, title_en, event_class, event_date, date_precision,
               country, region, source_name, source_url, inclusion_rule
        FROM events_v2
    """).fetchall()

    assert len(rows) >= 50, f"Dataset v2 deve conter pelo menos 50 eventos objetivos, encontrou {len(rows)}"

    country_counts = {}
    day_precision_count = 0

    valid_classes = {
        "war_interstate", "armed_conflict", "economic_recession",
        "pandemic", "coup_d_etat", "regime_change"
    }

    for r in rows:
        ev_id, title, ev_class, ev_date, precision, country, region, src, url, rule = r
        assert ev_class in valid_classes, f"Classe inválida: {ev_class}"
        assert src and url and rule, f"Metadados de inclusão ausentes no evento {title}"
        if precision == "day":
            day_precision_count += 1
        country_counts[country] = country_counts.get(country, 0) + 1

    total = len(rows)
    day_pct = (day_precision_count / total) * 100.0
    assert day_pct >= 80.0, f"Precisão diária esperada >= 80%, obteve {day_pct:.1f}%"

    max_c, max_count = max(country_counts.items(), key=lambda x: x[1])
    max_c_pct = (max_count / total) * 100.0
    assert max_c_pct <= 20.0, f"País {max_c} excedeu o limite máximo de 20% do dataset ({max_c_pct:.1f}%)"

    # Verificar tabela control_dates
    c_count = c.execute("SELECT count(*) FROM control_dates").fetchone()[0]
    assert c_count == 10000, f"Grupo de controle deve conter exatamente 10.000 datas, encontrou {c_count}"

    conn.close()
