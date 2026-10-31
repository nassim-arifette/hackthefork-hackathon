# Pipeline complet : make all. Chaque étape lit ses entrées sur disque et peut être relancée seule.
PY := python3
P := cd pipeline &&

all: export app

data/prix_ble.csv:
	$(P) $(PY) 00_prix_commerce.py
data/panel_rendements.csv:
	$(P) $(PY) 01_agreste.py
data/meteo_dept.csv: data/panel_rendements.csv
	$(P) $(PY) 02_weather.py
data/backtest.json: data/meteo_dept.csv data/panel_rendements.csv data/prix_ble.csv data/hypotheses.yaml pipeline/model.py pipeline/03_backtest.py
	$(P) $(PY) 03_backtest.py
data/parcelles.json:
	$(P) $(PY) 04_parcels.py
export: data/backtest.json data/parcelles.json
	$(P) $(PY) 05_export.py
	$(P) $(PY) 06_lettre_llm.py

app:
	cd app && npm install && npm run build && npm run build:single

dev:
	cd app && npm run dev

# Réutilise les données traitées et géométries déjà versionnées : aucun téléchargement.
recalculate:
	$(P) $(PY) 03_backtest.py
	$(P) $(PY) 05_export.py
	$(P) $(PY) 06_lettre_llm.py

test:
	$(PY) -m pytest -q tests

.PHONY: all export app dev test recalculate
