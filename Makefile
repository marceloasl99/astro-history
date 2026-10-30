.PHONY: setup test lint format ingest validate report run docker-up features hindcast forecast timeline v3

VENV = .venv
PYTHON = $(VENV)/bin/python
PYTEST = $(VENV)/bin/pytest
UVICORN = $(VENV)/bin/uvicorn

setup:
	python3 -m venv $(VENV)
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install -r requirements.lock

test:
	$(PYTEST) -v

ingest:
	$(PYTHON) src/data/ingest_historical.py

validate:
	$(PYTHON) src/analysis/run_phase3_validation.py

report:
	$(PYTHON) scripts/generate_phase1_report.py
	$(PYTHON) src/analysis/run_phase3_validation.py

features:
	$(PYTHON) -m src.features.astro_features

hindcast:
	$(PYTHON) -W ignore -m src.analysis.hindcast

forecast:
	$(PYTHON) -W ignore -m src.analysis.forecast_v3

timeline:
	$(PYTHON) -c "from src.future_engine import generate_future_timeline_1800_2100, get_projections_2027_2060; generate_future_timeline_1800_2100(force_refresh=True); get_projections_2027_2060(force_refresh=True)"

# Pipeline completo v3: grade de features -> hindcast -> forecast -> caches da UI
v3: features hindcast forecast timeline

run:
	$(UVICORN) src.web.app:app --host 127.0.0.1 --port 8000

docker-up:
	docker compose up -d --build
