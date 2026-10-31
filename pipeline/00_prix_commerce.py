"""Prix et commerce mesurés : prix du blé tendre, prix observés de la lentille, commerce extérieur.

- Prix du blé : indice Eurostat des prix à la production, France, blé tendre (apri_pi_outa,
  AM011100, nominal), chaîné sur la base 2015 = 100 puis calé en niveau sur le prix du blé
  rendu Rouen publié par Agreste pour la campagne 2019-2020 (178,8 €/t).
- Prix de la lentille : prix de vente absolus Eurostat (apri_ap_crpouta, 02991000), France.
- Commerce : Eurostat Comext (DS-045409), code NC8 07134000 (lentilles sèches), France ; importations
  de 2025 par pays partenaire (origine hors UE, expédition dans l'UE) ; prix des importations
  (valeur statistique / tonnes), toutes origines et Canada.
Sorties : data/prix_ble.csv, data/prix_lentille_observes.csv, data/commerce_lentilles.csv.
"""
import json

import pandas as pd
import requests

from common import DATA, RAW

EUROSTAT = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
COMEXT = "https://ec.europa.eu/eurostat/api/comext/dissemination/statistics/1.0/data/DS-045409"
ANCRAGE_ANNEE, ANCRAGE_PRIX = 2019, 178.8  # Agreste, blé tendre rendu Rouen, campagne 2019-2020


def fetch(name: str, url: str, params: dict) -> dict:
    path = RAW / "eurostat" / f"{name}.json"
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(url, params=params, timeout=180)
        r.raise_for_status()
        path.write_text(r.text)
    return json.loads(path.read_text())


def cube(d: dict) -> pd.DataFrame:
    """Aplatit un jeu JSON-stat Eurostat en table longue."""
    ids, size, dims = d["id"], d["size"], d["dimension"]
    inv = {k: {v: c for c, v in dims[k]["category"]["index"].items()} for k in ids}
    rows = []
    for flat, v in d["value"].items():
        flat, coord = int(flat), {}
        for k, s in zip(reversed(ids), reversed(size)):
            coord[k] = inv[k][flat % s]
            flat //= s
        rows.append(coord | {"value": v})
    return pd.DataFrame(rows)


def prix_ble() -> pd.DataFrame:
    d = cube(fetch("indice_ble", EUROSTAT + "apri_pi_outa",
                   {"format": "JSON", "lang": "EN", "geo": "FR", "am_item": "AM011100", "p_adj": "NI"}))
    d["annee"] = d.time.astype(int)
    base = {u: d[d.unit == u].set_index("annee").value for u in ("I10", "I15", "I20")}
    # Chaînage sur la base 2015 = 100.
    i10 = base["I10"] * 100 / base["I10"][2015]
    i20 = base["I20"] * base["I15"][2020] / 100
    idx = {}
    for y in range(2010, 2026):
        if y in base["I15"].index:
            idx[y] = base["I15"][y]
        elif y < 2015 and y in i10.index:
            idx[y] = i10[y]
        elif y in i20.index:
            idx[y] = i20[y]
    s = pd.Series(idx).sort_index()
    prix = s / s[ANCRAGE_ANNEE] * ANCRAGE_PRIX
    return pd.DataFrame({"annee": s.index, "indice_2015_100": s.round(2).values,
                         "prix_eur_t": prix.round(1).values})


def prix_lentille() -> pd.DataFrame:
    d = cube(fetch("prix_absolus", EUROSTAT + "apri_ap_crpouta",
                   {"format": "JSON", "lang": "EN", "geo": "FR"}))
    d = d[(d.prod_veg == "02991000") & (d.currency == "EUR")]
    d = d.assign(annee=d.time.astype(int), prix_eur_t=d.value * 10)[["annee", "prix_eur_t"]]
    # 2010 et 2011 (140 €/t) sont incohérents avec la suite (650 à 780 €/t) : écartés.
    d["retenu"] = d.annee >= 2012
    return d.sort_values("annee")


def commerce() -> pd.DataFrame:
    out = []
    for flow, name in ((1, "importations_t"), (2, "exportations_t")):
        d = cube(fetch(f"comext_lentilles_{flow}", COMEXT,
                       {"format": "JSON", "lang": "EN", "freq": "A", "reporter": "FR",
                        "product": "07134000", "flow": flow, "partner": "WORLD",
                        "indicators": "QUANTITY_IN_100KG"}))
        out.append(d.assign(annee=d.time.astype(int), **{name: (d.value / 10).round()})
                   .set_index("annee")[[name]])
    return pd.concat(out, axis=1).reset_index()


def prix_import() -> pd.DataFrame:
    """Prix des lentilles importées (€/t) : valeur statistique à la frontière / tonnes, toutes origines et Canada."""
    d = cube(fetch("comext_lentilles_valeur", COMEXT,
                   {"format": "JSON", "lang": "EN", "freq": "A", "reporter": "FR", "product": "07134000", "flow": 1,
                    "partner": ["WORLD", "CA"], "indicators": ["VALUE_IN_EUROS", "QUANTITY_IN_100KG"]}))
    w = d.pivot_table(index=["time", "partner"], columns="indicators", values="value").reset_index()
    w["prix"] = (w.VALUE_IN_EUROS / (w.QUANTITY_IN_100KG / 10)).round()
    out = w.pivot(index="time", columns="partner", values="prix").reset_index()
    out = out.rename(columns={"time": "annee", "WORLD": "prix_import_eur_t", "CA": "prix_import_canada_eur_t"})
    out["annee"] = out.annee.astype(int)
    out = out[out.annee >= 2010].astype({"prix_import_eur_t": int, "prix_import_canada_eur_t": int})
    return out[["annee", "prix_import_eur_t", "prix_import_canada_eur_t"]].sort_values("annee")


def origines(annee: int = 2025) -> pd.DataFrame:
    """Importations de lentilles par pays partenaire : pays d'origine hors UE, pays d'expédition dans l'UE."""
    d = cube(fetch(f"comext_lentilles_origines_{annee}", COMEXT,
                   {"format": "JSON", "lang": "EN", "freq": "A", "reporter": "FR", "product": "07134000",
                    "flow": 1, "indicators": "QUANTITY_IN_100KG", "time": str(annee)}))
    total = float(d[d.partner == "WORLD"].value.iloc[0]) / 10
    pays = d[d.partner.str.fullmatch(r"[A-Z]{2}")].assign(tonnes=lambda x: (x.value / 10).round().astype(int))
    pays = pays.sort_values("tonnes", ascending=False)[["partner", "tonnes"]].rename(columns={"partner": "pays"})
    pays["part"] = (pays.tonnes / total).round(3)
    pays.insert(0, "annee", annee)
    return pays


def main():
    origines().to_csv(DATA / "commerce_lentilles_origines.csv", index=False)
    prix_import().to_csv(DATA / "prix_import_lentilles.csv", index=False)
    pb = prix_ble()
    pb.to_csv(DATA / "prix_ble.csv", index=False)
    pl = prix_lentille()
    pl.to_csv(DATA / "prix_lentille_observes.csv", index=False)
    co = commerce()
    co.to_csv(DATA / "commerce_lentilles.csv", index=False)
    print(pb.to_string(index=False))
    print(pl.to_string(index=False))
    print(co.tail(6).to_string(index=False))


if __name__ == "__main__":
    main()
