"""
Script para recálculo integral em lote das cartas natais dos 200 eventos históricos
utilizando os aspectos estritos (orbe 3.0°), asteroides clássicos (Ceres, Pallas, Juno, Vesta, Quíron, Lilith)
e alinhamentos com as 30 principais estrelas fixas (orbe 0.3°).
"""

import json
import time
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.astro_engine import calculate_event_chart
from src.db import init_db, save_calculated_event, get_events_stats, get_connection

DATA_FILE = "/home/astro/data/historical_events.json"

def populate():
    print("=" * 75)
    print("RECÁLCULO INTEGRAL DOS 200 FATOS HISTÓRICOS COM ASTEROIDES E 30 ESTRELAS FIXAS")
    print("Regras: Orbe de 3.0° para aspectos planetários e 0.3° para estrelas fixas")
    print("=" * 75)

    if not os.path.exists(DATA_FILE):
        print(f"Erro: Arquivo {DATA_FILE} não encontrado!")
        sys.exit(1)

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        events = json.load(f)

    print(f"Total de eventos a recalcular: {len(events)}")
    print("Atualizando estrutura do banco SQLite (adicionando tabela event_star_aspects)...")
    init_db()

    start_time = time.time()
    count = 0
    total_star_hits = 0

    for idx, ev in enumerate(events, 1):
        # Calcular mapa astral refinado
        chart = calculate_event_chart(ev)
        
        # Salvar no SQLite
        save_calculated_event(ev, chart)
        count += 1
        total_star_hits += len(chart.get("star_contacts", []))

        if count % 20 == 0 or count == len(events):
            elapsed = time.time() - start_time
            print(f"[{count:03d}/{len(events):03d}] Recalculados em {elapsed:.2f}s - Último: {ev['title'][:32]}... ({len(chart['aspects'])} asp, {len(chart['star_contacts'])} estrelas)")

    total_time = time.time() - start_time
    stats = get_events_stats()

    # Checar destaques de estrelas ativadas
    conn = get_connection()
    top_stars = conn.execute("""
        SELECT star_name, COUNT(*) as cnt
        FROM event_star_aspects
        GROUP BY star_name
        ORDER BY cnt DESC
        LIMIT 6
    """).fetchall()
    conn.close()

    print("=" * 75)
    print(f"RECÁLCULO CONCLUÍDO COM SUCESSO EM {total_time:.2f}s!")
    print(f"Total de Eventos: {stats['total_events']} (100% calculados)")
    print(f"Total de Alinhamentos com Estrelas Fixas (orbe <= 0.3°): {stats['total_star_contacts']}")
    print(f"Índice Médio de Tensão Astrológica: {stats['average_tension']}")
    print("Estrelas Mais Ativadas nos 200 Fatos Históricos:")
    for ts in top_stars:
        print(f"  ★ {ts['star_name']}: {ts['cnt']} ativações diretas")
    print("=" * 75)

if __name__ == "__main__":
    populate()
