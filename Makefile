# Pipeline complet : make all. Chaque étape lit ses entrées sur disque et peut être relancée seule.
PY := python3
P := cd pipeline &&

all: export app

data/panel_rendements.csv:
	$(P) $(PY) 01_agreste.py
data/meteo_dept.csv: data/panel_rendements.csv
	$(P) $(PY) 02_weather.py
data/backtest.json: data/meteo_dept.csv data/hypotheses.yaml pipeline/model.py
	$(P) $(PY) 03_backtest.py
data/parcelles.json:
	$(P) $(PY) 04_parcels.py
export: data/backtest.json data/parcelles.json
	$(P) $(PY) 05_export.py

app:
	cd app && npm install && npm run build && npm run build:single

dev:
	cd app && npm run dev

.PHONY: all export app dev
