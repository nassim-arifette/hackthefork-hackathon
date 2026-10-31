"""Backtest glissant 2019-2025, sans fuite.

Pour chaque année test t : niveaux, modèles et calibration sont estimés sur les années
< t uniquement ; P* est calculé avec la météo des années < t ; puis on regarde
l'année t réelle. Le protocole est figé : il n'est jamais modifié après coup.
Sortie : data/backtest.json (copiée dans l'application par 05_export.py).
"""
import json

import numpy as np
import pandas as pd

from common import DATA, TEST_YEARS, hypotheses
from model import Calibrated, hyp_values, levels, load, break_even_prices, p_star, pinball, \
    pool_for, with_rel

MIN_TRAIN_YEARS = 3


def main():
    df, meteo = load()
    h = hyp_values(hypotheses())
    L, W = df[df.culture == "lentille"], df[df.culture == "ble"]
    detail, par_annee = [], []
    for t in TEST_YEARS:
        trL, trW = L[L.annee < t], W[W.annee < t]
        okL = trL.groupby("dep").annee.count()
        levL = levels(trL[trL.dep.isin(okL[okL >= MIN_TRAIN_YEARS].index)])
        levW = levels(trW)
        trL, trW = with_rel(trL, levL), with_rel(trW, levW)
        models = {k: Calibrated(k).fit(trL) for k in ("M0", "M1", "M2", "auto")}
        mW = Calibrated("M1").fit(trW)
        prix_t = float(meteo[meteo.annee == t].prix_ble.iloc[0])

        te = with_rel(L[L.annee == t], levL)
        te = te[te.dep.isin(levW.index)]
        realW = W[W.annee == t].set_index("dep").rendement_qha
        res = {k: m.predict(te) for k, m in models.items()}
        y = te.rel.to_numpy()
        row = {"annee": t, "n_dep": int(len(te)), "prix_ble": round(prix_t, 1),
               "modele_auto": models["auto"].kind}
        for k, q in res.items():
            row[f"pinball_{k}"] = round(pinball(q, y), 4)
            row[f"couverture_{k}"] = round(float(np.mean((y >= q[:, 0]) & (y <= q[:, 2]))), 3)
            row[f"largeur_{k}"] = round(float(np.mean(q[:, 2] - q[:, 0])), 3)
        q1 = res["M1"]
        row["erreur_mediane_M1"] = round(float(np.median(np.abs(q1[:, 1] - y))), 3)
        row["rel_reel_moyen"] = round(float(y.mean()), 3)
        row["rel_q10_moyen"], row["rel_q50_moyen"], row["rel_q90_moyen"] = \
            [round(float(v), 3) for v in q1.mean(axis=0)]

        tenus = {"moyenne": [], "M0": [], "M1": [], "M2": [], "auto": []}
        prix_passe = float(meteo[meteo.annee < t].groupby("annee").prix_ble.first().mean())
        for i, (_, r) in enumerate(te.iterrows()):
            if r.dep not in realW.index or np.isnan(realW[r.dep]):
                continue
            pool = pool_for(meteo, r.dep, range(2010, t), t)
            yL, yW = r.rendement_qha / 10, realW[r.dep] / 10
            yL_paid = yL * (1 - h["qualite"])  # tonnes acceptées au tri
            marge_W = prix_t * yW - h["charges_ble"]
            rec = {"annee": t, "dep": r.dep, "dep_nom": r.dep_nom,
                   "rendement_lentille_reel": round(r.rendement_qha, 1),
                   "rendement_ble_reel": round(float(realW[r.dep]), 1),
                   "prix_ble_reel": round(prix_t, 1), "marge_ble": round(marge_W),
                   "ic80_rel": [round(float(q1[i, 0]), 3), round(float(q1[i, 2]), 3)],
                   "q50_rel": round(float(q1[i, 1]), 3), "rel_reel": round(float(y[i]), 3)}
            # Référence naïve, sans modèle : prix d'équilibre calculé sur les moyennes des années passées.
            p_moy = (prix_passe * levW[r.dep] / 10 - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) \
                / (levL[r.dep] / 10 * (1 - h["qualite"]))
            tenu_moy = bool(p_moy * yL_paid - h["charges_lentille"] + h["bonus"] >= marge_W)
            tenus["moyenne"].append(tenu_moy)
            rec |= {"p_moyenne": round(p_moy), "tenu_moyenne": tenu_moy}
            for k in ("M0", "M1", "M2", "auto"):
                R, _, _ = break_even_prices(pool, models[k], mW, levL[r.dep], levW[r.dep], h,
                                            seed=t * 100 + i)
                ps = p_star(R, h["tau"])
                marge_L = ps * yL_paid - h["charges_lentille"] + h["bonus"]
                tenu = bool(marge_L >= marge_W)
                tenus[k].append(tenu)
                sfx = {"M0": "_M0", "M1": "", "M2": "_M2", "auto": "_auto"}[k]
                rec |= {f"p_star{sfx}": round(ps), f"marge_lentille{sfx}": round(marge_L),
                        f"tenu{sfx}": tenu}
            detail.append(rec)
        row["n_contrats"] = len(tenus["M1"])
        row["taux_tenus"] = round(float(np.mean(tenus["M1"])), 3) if tenus["M1"] else None
        row["taux_tenus_auto"] = round(float(np.mean(tenus["auto"])), 3) if tenus["auto"] else None
        row["taux_tenus_M2"] = round(float(np.mean(tenus["M2"])), 3) if tenus["M2"] else None
        row["taux_tenus_M0"] = round(float(np.mean(tenus["M0"])), 3) if tenus["M0"] else None
        row["taux_tenus_moyenne"] = round(float(np.mean(tenus["moyenne"])), 3) if tenus["moyenne"] else None
        row["p_star_median"] = round(float(np.median([d["p_star"] for d in detail if d["annee"] == t])))
        par_annee.append(row)
        print(f"{t}: n={row['n_dep']} blé={prix_t:.0f} €/t couverture M1={row['couverture_M1']} "
              f"pinball M0={row['pinball_M0']} M1={row['pinball_M1']} M2={row['pinball_M2']} "
              f"auto({row['modele_auto']})={row['pinball_auto']} "
              f"tenus M1={row['taux_tenus']} auto={row['taux_tenus_auto']} P*med={row['p_star_median']}")

    d = pd.DataFrame(detail)
    pa = pd.DataFrame(par_annee)
    glob = {"taux_tenus": round(float(d.tenu.mean()), 3),
            "taux_tenus_auto": round(float(d.tenu_auto.mean()), 3),
            "taux_tenus_M2": round(float(d.tenu_M2.mean()), 3),
            "taux_tenus_M0": round(float(d.tenu_M0.mean()), 3),
            "taux_tenus_moyenne": round(float(d.tenu_moyenne.mean()), 3),
            "p_star_median_M1": round(float(d.p_star.median())),
            "p_star_median_M0": round(float(d.p_star_M0.median())),
            "p_moyenne_median": round(float(d.p_moyenne.median())),
            "n_cas": int(len(d)), "n_annees": len(TEST_YEARS)}
    for k in ("M0", "M1", "M2", "auto"):
        w = pa.n_dep / pa.n_dep.sum()
        glob[f"pinball_{k}"] = round(float((pa[f"pinball_{k}"] * w).sum()), 4)
        glob[f"couverture_{k}"] = round(float((pa[f"couverture_{k}"] * w).sum()), 3)
    glob["erreur_mediane_M1"] = round(float(np.median([abs(r["rel_reel"] - r["q50_rel"]) for r in detail])), 3)
    glob["gain_pinball_M1_vs_M0"] = round(1 - glob["pinball_M1"] / glob["pinball_M0"], 3)
    glob["gain_pinball_M2_vs_M0"] = round(1 - glob["pinball_M2"] / glob["pinball_M0"], 3)
    glob["gain_pinball_auto_vs_M0"] = round(1 - glob["pinball_auto"] / glob["pinball_M0"], 3)
    out = {
        "protocole": ("Glissant : pour chaque année test t de 2019 à 2025, niveaux, modèles et "
                      "calibration conformal estimés sur les années < t uniquement ; P* calculé en "
                      "rejouant la météo et le prix du blé des années < t ; verdict avec les "
                      "rendements et le prix du blé réels de l'année t."),
        "fiabilite_visee": h["tau"],
        "global": glob, "annees": par_annee, "detail": detail,
    }
    (DATA / "backtest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("Global :", glob)


if __name__ == "__main__":
    main()
