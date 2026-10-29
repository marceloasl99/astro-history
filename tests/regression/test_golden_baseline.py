import json
import os
import pytest
from src.astro_engine import calculate_event_chart

GOLDEN_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "archive", "v0", "golden_reference.json")

@pytest.fixture
def golden_events():
    with open(GOLDEN_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def test_golden_astronomical_consistency(golden_events):
    """
    Verifica que as posições astronômicas fundamentais (signos dos planetas geracionais)
    são perfeitamente determinísticas e reproduzíveis pelo Swiss Ephemeris.
    """
    for g in golden_events:
        ev_payload = {
            "id": g["id"],
            "title": g["title"],
            "date": g["date"],
            "time": g["time"],
            "latitude": g["lat"],
            "longitude": g["lon"]
        }
        chart = calculate_event_chart(ev_payload)
        planets = {p["id"]: p for p in chart["planets"]}

        assert planets["pluto"]["sign_name"] == g["pluto_sign"], (
            f"Plutão divergente em {g['title']}: {planets['pluto']['sign_name']} vs {g['pluto_sign']}"
        )
        assert planets["saturn"]["sign_name"] == g["saturn_sign"], (
            f"Saturno divergente em {g['title']}: {planets['saturn']['sign_name']} vs {g['saturn_sign']}"
        )
