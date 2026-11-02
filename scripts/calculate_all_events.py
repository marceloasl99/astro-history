#!/usr/bin/env python3
"""
calculate_all_events.py
Calcula as posições planetárias, aspectos, estrelas fixas e índices astrológicos
para todos os eventos históricos da tabela 'events' que ainda não foram calculados.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import sqlite3
import time
from src.astro_engine import calculate_event_chart
from src.db import save_calculated_event

DB_PATH = "db/history_astrology.db"

def calculate_pending_events(batch_size: int = 100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM events WHERE calculated = 0 ORDER BY id ASC;")
    pending = [dict(r) for r in cur.fetchall()]
    conn.close()

    total = len(pending)
    print(f"Iniciando cálculo astrológico para {total} eventos pendentes...")
    if total == 0:
        print("Nenhum evento pendente.")
        return

    t0 = time.time()
    success = 0
    errors = 0

    for i, ev in enumerate(pending, 1):
        try:
            chart = calculate_event_chart(ev)
            save_calculated_event(ev, chart)
            success += 1
        except Exception as e:
            print(f"Erro no evento #{ev['id']} ({ev['title']}): {e}")
            errors += 1

        if i % batch_size == 0 or i == total:
            elapsed = time.time() - t0
            rate = i / elapsed if elapsed > 0 else 1
            print(f"Progresso: {i}/{total} ({i/total*100:.1f}%) | {rate:.1f} ev/s | Sucessos: {success}, Falhas: {errors}")

    print(f"\nFinalizado em {time.time()-t0:.2f}s. Sucesso: {success}/{total}, Falhas: {errors}.")

if __name__ == "__main__":
    calculate_pending_events()
