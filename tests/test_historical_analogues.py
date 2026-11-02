"""
Testes unitários e de integração para o motor Cosmic History Search / Historical Analogues Engine.
"""

import pytest
from fastapi.testclient import TestClient
from src.analysis.historical_analogues import find_historical_analogues, HistoricalAnaloguesEngine
from src.web.app import app

def test_engine_finds_analogues():
    res = find_historical_analogues("2026-07-04", top_k=5)
    assert res["query_date"] == "2026-07-04"
    assert res["evaluated_historical_events"] >= 1100
    assert len(res["top_analogues"]) == 5

    # Verificar que os scores estão em ordem decrescente
    scores = [m["score_pct"] for m in res["top_analogues"]]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 100.0 for s in scores)

    # Primeiro evento deve conter metadados completos
    first = res["top_analogues"][0]
    assert "event_id" in first
    assert "title" in first
    assert "category" in first
    assert "date" in first
    assert "shared_cycles" in first

def test_engine_category_filter():
    res = find_historical_analogues("2030-01-01", category_filter="Guerra & Conflito", top_k=3)
    assert len(res["top_analogues"]) == 3
    for m in res["top_analogues"]:
        assert m["category"] == "Guerra & Conflito"

def test_web_api_endpoints():
    client = TestClient(app)

    # 1. API Historical Analogues
    r1 = client.get("/api/historical-analogues?date=2026-07-04&top_k=3")
    assert r1.status_code == 200
    d1 = r1.json()
    assert "top_analogues" in d1
    assert len(d1["top_analogues"]) == 3

    # 2. API Oshop Features
    r2 = client.get("/api/features/oshop?date=2026-07-04")
    assert r2.status_code == 200
    d2 = r2.json()
    assert "geo_outer_5" in d2

    # 3. API Barbault Comparison
    r3 = client.get("/api/features/barbault?date=2026-07-04")
    assert r3.status_code == 200
    d3 = r3.json()
    assert "ci5" in d3
    assert "ci4" in d3

    # 4. API Stats
    r4 = client.get("/api/stats")
    assert r4.status_code == 200
    assert r4.json()["total_events"] >= 1100
