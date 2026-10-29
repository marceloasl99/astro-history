.PHONY: setup test lint format ingest validate report run docker-up

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

run:
	$(UVICORN) src.web.app:app --host 127.0.0.1 --port 8000

docker-up:
	docker compose up -d --build
