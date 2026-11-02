"""
Testes de integridade da expansão histórica e isolamento da amostra pré-registrada.
"""

import json
import sqlite3
import os
import pytest

DB_PATH = "db/history_astrology.db"
JSON_PATH = "data/historical_events.json"

def test_expanded_events_json_exists_and_count():
    assert os.path.exists(JSON_PATH), f"Arquivo {JSON_PATH} não encontrado."
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        events = json.load(f)
    assert len(events) >= 1100, f"Esperava-se mais de 1.100 eventos, obtido {len(events)}"
    
    # Verificar que todas as categorias pertencem exatamente às 6 categorias canônicas
    canonical_categories = {
        'Guerra & Conflito',
        'Revolução & Conflito Interno',
        'Desastre & Saúde Pública',
        'Crise Financeira & Econômica',
        'Ciência & Tecnologia',
        'Política, Tratados & Cultura'
    }
    present_categories = {e["category"] for e in events}
    assert present_categories == canonical_categories, f"Divergência de categorias canônicas: {present_categories}"

    # Verificar integridade dos campos do primeiro e último evento
    for ev in [events[0], events[-1]]:
        assert "id" in ev
        assert "title" in ev and len(ev["title"]) > 0
        assert "category" in ev and len(ev["category"]) > 0
        assert "date" in ev and len(ev["date"]) >= 8
        assert "latitude" in ev and isinstance(ev["latitude"], (int, float))
        assert "longitude" in ev and isinstance(ev["longitude"], (int, float))
        assert "consequence" in ev and len(ev["consequence"]) > 0

def test_sqlite_events_table_populated_and_calculated():
    assert os.path.exists(DB_PATH), f"Banco SQLite {DB_PATH} não encontrado."
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM events;")
    total_events = cur.fetchone()[0]
    assert total_events >= 1100, f"Total de eventos no SQLite insuficiente: {total_events}"

    cur.execute("SELECT COUNT(*) FROM events WHERE calculated = 1;")
    calculated_events = cur.fetchone()[0]
    assert calculated_events == total_events, f"Nem todos os eventos foram calculados: {calculated_events}/{total_events}"

    # Verificar que as tabelas planet_positions e event_aspects têm dados correspondentes
    cur.execute("SELECT COUNT(*) FROM planet_positions;")
    total_positions = cur.fetchone()[0]
    assert total_positions > 10000, f"Posições planetárias insuficientes: {total_positions}"

    cur.execute("SELECT COUNT(*) FROM event_aspects;")
    total_aspects = cur.fetchone()[0]
    assert total_aspects > 10000, f"Aspectos insuficientes: {total_aspects}"

    conn.close()

def test_isolation_of_events_v2_and_control_dates():
    """Garante que a expansão histórica NÃO tocou no dataset pré-registrado de teste."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM events_v2;")
    v2_count = cur.fetchone()[0]
    assert v2_count == 61, f"Amostra analítica events_v2 foi violada! Esperava 61, obtido {v2_count}"

    cur.execute("SELECT COUNT(*) FROM control_dates;")
    ctrl_count = cur.fetchone()[0]
    assert ctrl_count == 10000, f"Grupo de controle control_dates foi violado! Esperava 10000, obtido {ctrl_count}"

    conn.close()
