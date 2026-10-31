"""Le même moteur sur d'autres légumineuses : pois chiche, haricot sec, pois protéagineux, féverole.

Pour chaque culture :
- modèle quantile M1 appris sur ses séries Agreste (statuts 1-2, doublons regroupés) et la météo
  de ses départements (data/meteo_dept_cultures.csv), aux anomalies mises à l'échelle du modèle
  principal ; le modèle du blé est celui de la lentille, inchangé ;
- niveau de rendement en Île-de-France : celui du département quand Agreste le publie avec un
  statut 1 ou 2, sinon la moyenne des départements voisins du bassin parisien qui en ont un ;
- prix plancher pour 8 années sur 10 dans les quatre départements franciliens (20 000 années,
  mêmes graines que 05_export.py), barème par tranches calibré aux proportions de la
  proposition lentille, backtest glissant 2019-2025 sur les départements producteurs ;
- départements où la culture tient le mieux, à charges franciliennes.
La lentille passe par le même chemin : on doit retrouver les chiffres du pipeline principal.
Hypothèses : data/cultures.yaml. Sortie : data/cultures.json et app/src/data/cultures.json.
"""
import json

import numpy as np
import pandas as pd
import yaml

from common import APP_DATA, DATA, IDF_AGRI, TEST_YEARS, VOISINS_LENTILLE, hypotheses
from model import Calibrated, anomalies, break_even_prices, calibrer_premier_palier, hyp_values, levels, \
    load, p_star, paiement, pool_for, read_meteo, series_passees, simulate_years, with_rel

N_SIM, TARGET_YEAR, POOL_YEARS, MIN_TRAIN_YEARS = 20000, 2026, range(2010, 2026), 3
BASSIN = ["10", "51", "89", "28", "45", "60", "02", "27", "41", "80"]
CULTURES = ["lentille", "pois_chiche", "haricot", "pois", "feverole"]


def backtest(C, met, W, u, h, panel, culture, meteo_c):
    """Comme 03_backtest.py : apprentissage sur les séries regroupées avec le seul passé."""
    tenus, index, couverts, par_annee = [], [], [], {}
    wu = u[u.culture == "ble"]
    for t in TEST_YEARS:
        trC = series_passees(panel, culture, t).merge(meteo_c, on=["dep", "annee"], how="inner")
        n_ans = trC.groupby("dep").annee.count()
        levC_t = levels(trC[trC.dep.isin(n_ans[n_ans >= MIN_TRAIN_YEARS].index)])
        if len(levC_t) < 3:
            continue
        mC_t = Calibrated("M1").fit(with_rel(trC, levC_t))
        trW = W[W.annee < t]
        mW_t = Calibrated("M1").fit(with_rel(trW, levels(trW)))
        levW_t = wu[wu.annee < t].groupby("dep").rendement_qha.mean()
        realW = wu[wu.annee == t].set_index("dep").rendement_qha
        prix_t = float(met[met.annee == t].prix_ble.iloc[0])
        te = with_rel(C[C.annee == t], levC_t)
        te = te[te.dep.isin(levW_t.index)]
        if len(te):
            q = mC_t.predict(te)
            couverts += list((te.rel.to_numpy() >= q[:, 0]) & (te.rel.to_numpy() <= q[:, 2]))
        for i, (_, r) in enumerate(te.iterrows()):
            if r.dep not in realW.index or np.isnan(realW[r.dep]):
                continue
            pool = pool_for(met, r.dep, range(2010, t), t)
            yC, yW, pB = simulate_years(pool, mC_t, mW_t, levC_t[r.dep], levW_t[r.dep], h, seed=t * 100 + i)
            R = (pB * yW - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) / (yC * (1 - h["qualite"]))
            ps, m = p_star(R, h["tau"]), p_star(R / pB, h["tau"])
            vendu = r.rendement_qha / 10 * (1 - h["qualite"])
            marge_b = prix_t * realW[r.dep] / 10 - h["charges_ble"]
            tenus.append(bool(ps * vendu - h["charges_lentille"] + h["bonus"] >= marge_b))
            index.append(bool(m * prix_t * vendu - h["charges_lentille"] + h["bonus"] >= marge_b))
            par_annee.setdefault(t, []).append(tenus[-1])
    taux = lambda v: round(float(np.mean(v)), 3) if v else None
    return {"n_cas": len(tenus), "taux_tenus": taux(tenus), "taux_tenus_indexe": taux(index),
            "couverture_80": taux(couverts), "par_annee": {str(t): taux(v) for t, v in par_annee.items()}}


def main():
    H = hypotheses()
    base = hyp_values(H)
    cy = yaml.safe_load((DATA / "cultures.yaml").read_text())
    df, meteo = load()                                  # modèle principal : 43 départements
    _, scale = anomalies(read_meteo())
    meteo_c, _ = anomalies(read_meteo("meteo_dept_cultures.csv"), scale)
    panel = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    util = panel[panel.utilisable]
    u = util[~util.doublon]
    noms = panel.drop_duplicates("dep").set_index("dep").dep_nom.to_dict()
    nat = pd.read_csv(DATA / "rendements_nationaux.csv").pivot(index="annee", columns="culture", values="rendement_qha")
    lookup = lambda c: util[util.culture == c].groupby("dep").rendement_qha.mean()

    W = df[df.culture == "ble"]
    mW = Calibrated("M1").fit(with_rel(W, levels(W)))
    levW_all = lookup("ble")
    proposition = json.loads((DATA / "pilote_300t" / "contrats.json").read_text())["synthetique_2027"]["paliers_marginaux_eur_t"]

    out, ratios = [], None
    for c in CULTURES:
        h = dict(base)
        if c == "lentille":
            C, met = df[df.culture == "lentille"], meteo
            obs = json.loads((APP_DATA / "meta.json").read_text())["prix_lentille_observes"]
            nom, hyp_c, ref = "Lentille", None, [obs["min"], obs["max"]]
        else:
            y = cy[c]
            C = u[u.culture == c].merge(meteo_c, on=["dep", "annee"], how="inner")
            met, nom = meteo_c, y["nom"]
            h |= {"charges_lentille": y["charges_eur_ha"]["valeur"], "aide": y["aide_eur_ha"]["valeur"],
                  "rotation": y["rotation_eur_ha"]["valeur"], "qualite": y["part_refusee"]["valeur"]}
            h["bonus"] = h["aide"] + h["rotation"]
            hyp_c = {k: y[k] for k in ("charges_eur_ha", "aide_eur_ha", "rotation_eur_ha", "part_refusee", "prix_reference")}
            ref = y["prix_reference"]["valeur"] if y["prix_reference"] else None
        levC = levels(C)
        mC = Calibrated("M1").fit(with_rel(C, levC))

        # Niveau de rendement en Île-de-France.
        lk = lookup(c)
        if c == "lentille":
            v = float(lk[[d for d in VOISINS_LENTILLE if d in lk.index]].mean())
            lev_idf, origine = {d: v for d in IDF_AGRI}, "emprunté aux départements voisins"
        else:
            voisins = [d for d in BASSIN if d in lk.index]
            v = float(lk[voisins].mean()) if voisins else float(lk.median())
            lev_idf = {d: float(lk[d]) if d in lk.index else v for d in IDF_AGRI}
            mesures = [d for d in IDF_AGRI if d in lk.index]
            origine = ("mesuré dans chaque département" if len(mesures) == len(IDF_AGRI)
                       else "emprunté aux départements voisins" if voisins and not mesures
                       else "médiane nationale" if not voisins and not mesures
                       else "mesuré ou emprunté selon le département")

        # Prix plancher dans les quatre départements, mêmes graines que 05_export.py.
        p_dep, sims = {}, {}
        for dep in IDF_AGRI:
            pool = pool_for(meteo, dep, POOL_YEARS, TARGET_YEAR)
            yC, yW, pB = simulate_years(pool, mC, mW, lev_idf[dep], levW_all[dep], h, n=N_SIM, seed=int(dep))
            R = (pB * yW - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) / (yC * (1 - h["qualite"]))
            p_dep[dep] = round(p_star(R, h["tau"]))
            sims[dep] = (yC, yW, pB, R)
        yC, yW, pB, R = sims["77"]
        ps = p_star(R, h["tau"])
        m_star = p_star(R / pB, h["tau"])  # contrat indexé : plancher = m* × prix du blé
        if c == "lentille":
            ratios = (proposition[1] / ps, proposition[2] / ps)
        p2, p3 = round(ps * ratios[0]), round(ps * ratios[1])
        paid = yC * (1 - h["qualite"])
        # Tranches à l'échelle du rendement : pour la lentille (1,43 t/ha acceptées), 1 et 2 t/ha.
        bornes = (round(0.7 * float(paid.mean()), 1), round(1.4 * float(paid.mean()), 1))
        p1 = calibrer_premier_palier((p2, p3), yC, yW, pB, h, h["tau"], bornes)
        cout_tr = float(paiement({"paliers": (p1, p2, p3), "bornes": bornes}, paid).mean() / paid.mean())
        mid = float(np.mean(ref)) if ref else None
        grid = range(int(ps * 0.3) // 10 * 10, int(ps * 2.2) // 10 * 10 + 1, 10)

        # Backtest glissant, comme 03_backtest.py (mêmes graines : la lentille y retrouve ses 78 %),
        # avec en plus un contrat indexé : plancher = m* × prix du blé de la récolte.
        bt = backtest(C, met, W, u, h, panel, c, meteo_c)

        # Là où la culture tient le mieux (charges franciliennes partout).
        classement = []
        for dep in sorted(set(levC.index) & set(levW_all.index) & set(met.dep)):
            pool = pool_for(met, dep, POOL_YEARS, TARGET_YEAR)
            Rd, _, _ = break_even_prices(pool, mC, mW, levC[dep], levW_all[dep], h, n=N_SIM, seed=int(dep[:2], 36))
            classement.append({"dep": dep, "nom": noms.get(dep, dep), "p_star": round(p_star(Rd, h["tau"])),
                               "rendement_qha": round(float(levC[dep]), 1)})
        classement.sort(key=lambda x: x["p_star"])

        rec = {
            "id": c, "nom": nom, "n_couples": int(len(C)), "n_series": int(C.dep.nunique()),
            "cv_national": round(float(nat[c].std() / nat[c].mean()), 2),
            "niveau_idf_qha": {d: round(v, 1) for d, v in lev_idf.items()}, "origine_niveau": origine,
            "hypotheses": hyp_c, "reference": ref,
            "p_star": p_dep, "p_equilibre_median_77": round(p_star(R, 0.5)),
            "rendement_moyen_77_tha": round(float(yC.mean()), 2),
            "rendement_q10_77_tha": round(float(np.quantile(yC, 0.1)), 2),
            "fiabilite_reference": round(float(np.mean(R <= mid)), 3) if mid else None,
            "fiabilite_par_prix": [{"prix": p, "fiabilite": round(float(np.mean(R <= p)), 3)} for p in grid],
            "tranches": {"paliers": [p1, p2, p3], "bornes_tha": list(bornes), "cout_moyen_t": round(cout_tr),
                         "economie": round(1 - cout_tr / ps, 3)},
            "indexe_m_star": round(m_star, 2),
            "backtest": bt, "meilleurs": classement[:3], "n_departements_classes": len(classement),
        }
        out.append(rec)
        print(f"{c:12s} P* 77={p_dep['77']} (78 {p_dep['78']}, 91 {p_dep['91']}, 95 {p_dep['95']}) "
              f"médiane {rec['p_equilibre_median_77']} | réf {rec['fiabilite_reference']} | tranches {p1}/{p2}/{p3} "
              f"−{rec['tranches']['economie']:.0%} | backtest {bt} | niveau IdF {rec['niveau_idf_qha']['77']} q/ha "
              f"({origine}) | meilleurs {[(m['nom'], m['p_star']) for m in classement[:3]]}")

    res = {"campagne": TARGET_YEAR, "fiabilite_visee": base["tau"], "cultures": out}
    (DATA / "cultures.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
    (APP_DATA / "cultures.json").write_text(json.dumps(res, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
