"""Comparer des formes de contrat sur les années simulées de la Seine-et-Marne, campagne 2026.

Mêmes 20 000 années que le prix plancher (05_export.py, graine 77). Pour chaque contrat :
- la part des années où la lentille sous contrat rapporte au moins autant que le blé ;
- le coût moyen d'achat par tonne acceptée (sommes versées / tonnes acceptées), hors
  collecte et tri ;
- le coût par tonne une année de faible rendement (rendement accepté du premier décile) ;
- la perte moyenne de l'agriculteur face au blé, les années où la lentille perd, et son gain moyen
  les années où elle gagne : « 8 années sur 10 » est un plancher, pas le résultat moyen.
Les résultats du backtest 2019-2025 (03_backtest.py) sont joints.
Contrat indexé : plancher = m × prix du blé de la récolte, m calibré sur les mêmes années ; son
plancher est donné pour quelques prix du blé (le prix fixe équivalent est dans thresholds.json).
Assurance rendement de la lentille, pour l'offre assureurs : fréquence de sinistre et prime pure
(hors chargements) à 60, 70 et 80 % du rendement moyen, valorisés au prix plancher.
Coûts de l'acheteur hors achat (tri, collecte, séchage) : conventions du contrat synthétique de
data/pilote_300t/contrats.json, reprises telles quelles. Sortie : contrats.json.
"""
import json

import numpy as np

from common import APP_DATA, DATA, ROOT, VOISINS_LENTILLE, hypotheses
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
        # Ce que gagne l'agriculteur face au blé de la même année : « 8 années sur 10 » est un plancher,
        # pas le résultat moyen.
        "gain_moyen_ha": round(float(-ecart[~perd].mean())) if (~perd).any() else 0,
        "ecart_moyen_ha": round(float(-ecart.mean())),
        "marge_ble_moyenne_ha": round(float((pB * yW - h["charges_ble"]).mean())),
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

    # Contrat indexé sur le blé : payé m × prix du blé de l'année par tonne acceptée.
    m_star = float(p_star(R / pB, h["tau"]))
    faible = paid <= np.quantile(paid, 0.1)
    ecart_i = m_star * pB * paid - h["charges_lentille"] + h["bonus"] - (pB * yW - h["charges_ble"])
    gagne_i = ecart_i >= 0
    out["indexe"] = {
        "id": "indexe", "m": round(m_star, 2),
        "simulation": {
            "protection": round(float(np.mean(m_star * pB >= R)), 3),
            "cout_moyen_t": round(float((m_star * pB * paid).mean() / paid.mean())),
            "cout_t_annee_faible": round(float((m_star * pB[faible] * paid[faible]).sum() / paid[faible].sum())),
            "gain_moyen_ha": round(float(ecart_i[gagne_i].mean())),
            "perte_moyenne_ha": round(float(-ecart_i[~gagne_i].mean())),
            "ecart_moyen_ha": round(float(ecart_i.mean())),
        },
        # Plancher indexé pour quelques prix du blé ; le prix fixe équivalent est dans thresholds.json.
        "plancher_par_prix_ble": [{"prix_ble": p, "plancher": round(m_star * p)} for p in (160, 200, 240, 280)],
    }
    print("indexe            ", out["indexe"])
    # Assurance rendement, même distribution : indemnité = (seuil × rendement moyen − récolte) × prix assuré.
    prix_assure = float(round(ps))
    moy = float(yL.mean())
    out["assurance"] = {"prix_assure_eur_t": prix_assure, "rendement_moyen_tha": round(moy, 2), "niveaux": []}
    for seuil in (0.6, 0.7, 0.8):
        perte = np.maximum(0, seuil * moy - yL)
        out["assurance"]["niveaux"].append({
            "seuil": seuil, "frequence_sinistre": round(float(np.mean(perte > 0)), 3),
            "prime_pure_eur_ha": round(float(perte.mean() * prix_assure)),
            "capital_eur_ha": round(seuil * moy * prix_assure),
        })
    print("assurance         ", out["assurance"])
    syn = json.loads((ROOT / "data" / "pilote_300t" / "contrats.json").read_text())["synthetique_2027"]
    out["couts_acheteur"] = {
        "tri_eur_t_brute": syn["tri_eur_t_brute_recue"], "statut_tri": syn["statut_cout_tri"], "source_tri": syn["source_cout_tri_url"],
        "collecte_fixe_eur_t_brute": syn["transport"]["fixe_eur_t_brute_recue"],
        "collecte_eur_t_brute_km": syn["transport"]["variable_eur_t_brute_recue_km_route"],
        "sechage_eur_t_point": syn["sechage"]["eur_t_recue_point_humidite"], "statut": "hypothese_non_devis",
    }

    (DATA / "contrats.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    (APP_DATA / "contrats.json").write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
