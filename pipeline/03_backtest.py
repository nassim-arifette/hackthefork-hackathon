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
        models = {k: Calibrated(k).fit(trL) for k in ("M0", "M1", "M2")}
        mW = Calibrated("M1").fit(trW)

        te = with_rel(L[L.annee == t], levL)
        te = te[te.dep.isin(levW.index)]
        realW = W[W.annee == t].set_index("dep").rendement_qha
        res = {k: m.predict(te) for k, m in models.items()}
        y = te.rel.to_numpy()
        row = {"annee": t, "n_dep": int(len(te))}
        for k, q in res.items():
            row[f"pinball_{k}"] = round(pinball(q, y), 4)
            row[f"couverture_{k}"] = round(float(np.mean((y >= q[:, 0]) & (y <= q[:, 2]))), 3)
            row[f"largeur_{k}"] = round(float(np.mean(q[:, 2] - q[:, 0])), 3)
        q1 = res["M1"]
        row["rel_reel_moyen"] = round(float(y.mean()), 3)
        row["rel_q10_moyen"], row["rel_q50_moyen"], row["rel_q90_moyen"] = \
            [round(float(v), 3) for v in q1.mean(axis=0)]

        tenus = []
        for i, (_, r) in enumerate(te.iterrows()):
            if r.dep not in realW.index or np.isnan(realW[r.dep]):
                continue
            pool = pool_for(meteo, r.dep, range(2010, t), t)
            R, _, _ = break_even_prices(pool, models["M1"], mW, levL[r.dep], levW[r.dep], h,
                                        seed=t * 100 + i)
            ps = p_star(R, h["tau"])
            yL, yW = r.rendement_qha / 10, realW[r.dep] / 10
            marge_L = ps * yL - h["charges_lentille"] + h["bonus"]
            marge_W = h["prix_ble"] * yW - h["charges_ble"]
            tenu = bool(marge_L >= marge_W)
            tenus.append(tenu)
            detail.append({"annee": t, "dep": r.dep, "dep_nom": r.dep_nom,
                           "p_star": round(ps), "rendement_lentille_reel": round(r.rendement_qha, 1),
                           "rendement_ble_reel": round(float(realW[r.dep]), 1),
                           "ic80_rel": [round(float(q1[i, 0]), 3), round(float(q1[i, 2]), 3)],
                           "rel_reel": round(float(y[i]), 3),
                           "marge_lentille": round(marge_L), "marge_ble": round(marge_W),
                           "tenu": tenu})
        row["n_contrats"] = len(tenus)
        row["taux_tenus"] = round(float(np.mean(tenus)), 3) if tenus else None
        par_annee.append(row)
        print(f"{t}: n={row['n_dep']} couverture M1={row['couverture_M1']} "
              f"pinball M0={row['pinball_M0']} M1={row['pinball_M1']} M2={row['pinball_M2']} "
              f"contrats tenus={row['taux_tenus']}")

    d = pd.DataFrame(detail)
    pa = pd.DataFrame(par_annee)
    glob = {"taux_tenus": round(float(d.tenu.mean()), 3), "n_cas": int(len(d)),
            "n_annees": len(TEST_YEARS)}
    for k in ("M0", "M1", "M2"):
        w = pa.n_dep / pa.n_dep.sum()
        glob[f"pinball_{k}"] = round(float((pa[f"pinball_{k}"] * w).sum()), 4)
        glob[f"couverture_{k}"] = round(float((pa[f"couverture_{k}"] * w).sum()), 3)
    glob["gain_pinball_M1_vs_M0"] = round(1 - glob["pinball_M1"] / glob["pinball_M0"], 3)
    glob["gain_pinball_M2_vs_M0"] = round(1 - glob["pinball_M2"] / glob["pinball_M0"], 3)
    out = {
        "protocole": ("Glissant : pour chaque année test t de 2019 à 2025, niveaux, modèles et "
                      "calibration conformal estimés sur les années < t uniquement ; "
                      "P* calculé avec les années météo < t ; prix du blé et charges supposés."),
        "fiabilite_visee": h["tau"],
        "global": glob, "annees": par_annee, "detail": detail,
    }
    (DATA / "backtest.json").write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print("Global :", glob)


if __name__ == "__main__":
    main()
