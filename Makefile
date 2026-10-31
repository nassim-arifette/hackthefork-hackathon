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
data/backtest.json: data/meteo_dept.csv data/meteo_dept_cultures.csv data/prix_ble.csv data/hypotheses.yaml pipeline/model.py pipeline/contrats.py data/pilote_300t/contrats.json
	$(P) $(PY) 03_backtest.py
data/parcelles.json:
	$(P) $(PY) 04_parcels.py
data/meteo_dept_cultures.csv: data/panel_rendements.csv
	$(P) $(PY) 02_weather.py --cultures
export: data/backtest.json data/parcelles.json data/meteo_dept_cultures.csv
	$(P) $(PY) 05_export.py
	$(P) $(PY) 07_contrats.py
	$(P) $(PY) 09_cultures.py
	$(P) $(PY) 06_lettre_llm.py

# Suivi en saison (prototype) : lit environ 150 images Sentinel-2 en ligne, quelques minutes.
sentinel:
	$(P) $(PY) 08_sentinel.py

app:
	cd app && npm install && npm run build && npm run build:single

dev:
	cd app && npm run dev

test:
	$(PY) -m pytest -q tests

.PHONY: all export sentinel app dev test
