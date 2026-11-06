.PHONY: setup test lint format ingest validate report run docker-up features hindcast forecast timeline v3 v6 ephemeris gazetteer natal-grid calibrate-natal migrate-catalog expand-data audit-data

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

# ---------------------------------------------------------------- v6
ephemeris:          ## baixa/verifica os arquivos completos do Swiss Ephemeris (sepl/seplm/semom)
	$(PYTHON) scripts/install_ephemeris.py

gazetteer:          ## constrói data/gazetteer/cities.sqlite a partir dos dumps GeoNames em data/external/geonames
	$(PYTHON) scripts/build_gazetteer.py

natal-grid:         ## grade diária 1850–2150 dos corpos em trânsito (módulo pessoal)
	$(PYTHON) scripts/build_natal_grid.py

calibrate-natal:    ## calibração 0–1000 dos domínios de vida (população sintética)
	$(PYTHON) scripts/calibrate_natal_domains.py

migrate-catalog:    ## esquema v3, datas a.C., deduplicação e recálculo das cartas
	$(PYTHON) scripts/migrate_catalog_v3.py

expand-data:        ## importa fontes externas e curadas para o catálogo (Track A)
	$(PYTHON) scripts/importers/import_curated.py --merge
	$(PYTHON) scripts/importers/import_ncei_earthquakes.py --merge
	$(PYTHON) scripts/importers/import_gvp_eruptions.py --merge
	$(PYTHON) scripts/importers/import_wikidata.py --merge
	$(PYTHON) scripts/sync_catalog_json.py

audit-data:         ## relatório reports/catalog_audit_v6.md (falha se metas obrigatórias não forem atingidas)
	$(PYTHON) scripts/audit_catalog.py

v6: ephemeris natal-grid migrate-catalog expand-data audit-data hindcast forecast timeline

run:
	$(UVICORN) src.web.app:app --host 127.0.0.1 --port 8000

docker-up:
	docker compose up -d --build
