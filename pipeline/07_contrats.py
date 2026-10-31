"""Comparer des formes de contrat sur les années simulées de la Seine-et-Marne, campagne 2026.

Mêmes 20 000 années que le prix plancher (05_export.py, graine 77). Pour chaque contrat :
- la part des années où la lentille sous contrat rapporte au moins autant que le blé ;
- le coût moyen d'achat par tonne acceptée (sommes versées / tonnes acceptées), hors
  collecte et tri ;
- le coût par tonne une année de faible rendement (rendement accepté du premier décile) ;
- la perte moyenne de l'agriculteur face au blé, les années où la lentille perd.
Les résultats du backtest 2019-2025 (03_backtest.py) sont joints. Sortie : contrats.json.
"""
import json

import numpy as np

from common import APP_DATA, DATA, VOISINS_LENTILLE, hypotheses
from contrats import calibres, existants
from model import Calibrated, hyp_values, levels, levels_lookup, load, marge_lentille, paiement, \
    p_star, pool_for, simulate_years, with_rel

TARGET_YEAR, POOL_YEARS, N_SIM, DEP = 2026, range(2010, 2026), 20000, "77"


def mesurer(c: dict, yL, yW, pB, h: dict) -> dict:
    y = yL * (1 - h["qualite"])
    verse = paiement(c, y)
    ecart = pB * yW - h["charges_ble"] - marge_lentille(c, yL, h)
    perd = ecart > 0
    y10 = float(np.quantile(y, 0.1))
    return {
        "protection": round(float(np.mean(~perd)), 3),
        "cout_moyen_t": round(float(verse.mean() / y.mean())),
        "cout_t_annee_faible": round(float(paiement(c, np.array([y10]))[0] / y10)),
        "verse_moyen_ha": round(float(verse.mean())),
        "perte_moyenne_ha": round(float(ecart[perd].mean())) if perd.any() else 0,
    }


def main():
    h = hyp_values(hypotheses())
    df, meteo = load()
    L, W = df[df.culture == "lentille"], df[df.culture == "ble"]
    mL = Calibrated("M1").fit(with_rel(L, levels(L)))
    mW = Calibrated("M1").fit(with_rel(W, levels(W)))
    levW_all, levL_all = levels_lookup("ble"), levels_lookup("lentille")
    lev_idf = float(levL_all[[d for d in VOISINS_LENTILLE if d in levL_all.index]].mean())
    pool = pool_for(meteo, DEP, POOL_YEARS, TARGET_YEAR)
    yL, yW, pB = simulate_years(pool, mL, mW, lev_idf, levW_all[DEP], h, n=N_SIM, seed=int(DEP))

    paid = yL * (1 - h["qualite"])
    R = (pB * yW - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) / paid
    ps = p_star(R, h["tau"])

    bt = json.loads((DATA / "backtest.json").read_text())["global"].get("contrats", {})
    out = {"dep": DEP, "campagne": TARGET_YEAR, "fiabilite_visee": h["tau"],
           "rendement_accepte_annee_faible_tha": round(float(np.quantile(paid, 0.1)), 2),
           "existants": [], "calibres": []}
    for groupe, liste in (("existants", existants()), ("calibres", calibres(yL, yW, pB, h, ps))):
        for c in liste:
            out[groupe].append(c | {"simulation": mesurer(c, yL, yW, pB, h), "backtest": bt.get(c["id"])})
            print(f"{c['id']:18s}", out[groupe][-1]["simulation"], "| backtest :", bt.get(c["id"]))

    (DATA / "contrats.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (APP_DATA / "contrats.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
