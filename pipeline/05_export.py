"""Modèle final, prix plancher par département et par parcelle, exports pour l'application.

Le modèle final (M1 calibré) est entraîné sur 2010-2025. P* est calculé pour la campagne
2026 en rejouant les années 2010-2025 : leur météo et leur prix du blé.
Sorties : app/src/data/*.json, lus tels quels par le front.
"""
import json

import numpy as np
import pandas as pd

from common import APP_DATA, DATA, IDF_AGRI, RAW, VOISINS_LENTILLE, hypotheses
from model import FEATURES, Calibrated, break_even_prices, hyp_values, levels, levels_lookup, load, \
    p_star, pool_for, with_rel

TARGET_YEAR = 2026
POOL_YEARS = range(2010, 2026)
PRICE_GRID = list(range(400, 3001, 10))
N_SIM = 20000


def simulate(meteo, dep, mL, mW, levL, levW, h, seed):
    pool = pool_for(meteo, dep, POOL_YEARS, TARGET_YEAR)
    R, yL, yW = break_even_prices(pool, mL, mW, levL, levW, h, n=N_SIM, seed=seed)
    return R, yL, yW, pool


def bootstrap_p_star(df, meteo, dep, lev_l, lev_w, h, B=40, seed=0):
    """Incertitude sur P* : on rééchantillonne les années d'entraînement (par blocs d'une
    année entière), on réentraîne les deux modèles et on recalcule P*."""
    rng = np.random.default_rng(seed)
    years = np.array(sorted(df.annee.unique()))
    out = []
    for b in range(B):
        d = pd.concat([df[df.annee == y] for y in rng.choice(years, size=len(years), replace=True)])
        Lb, Wb = d[d.culture == "lentille"], d[d.culture == "ble"]
        mLb = Calibrated("M1").fit(with_rel(Lb, levels(Lb)))
        mWb = Calibrated("M1").fit(with_rel(Wb, levels(Wb)))
        R, _, _, _ = simulate(meteo, dep, mLb, mWb, lev_l, lev_w, h, seed=1000 + b)
        out.append(p_star(R, h["tau"]))
    return [round(float(np.quantile(out, q))) for q in (0.1, 0.5, 0.9)]


def main():
    H = hypotheses()
    h = hyp_values(H)
    kappa = H["cout_transport_eur_t_km"]["valeur"]
    detour = H["facteur_detour_route"]["valeur"]
    site = H["site_acheteur"]["valeur"]

    df, meteo = load()
    L, W = df[df.culture == "lentille"], df[df.culture == "ble"]
    levL, levW = levels(L), levels(W)
    mL = Calibrated("M1").fit(with_rel(L, levL))
    mW = Calibrated("M1").fit(with_rel(W, levW))
    # Pour la consultation (Île-de-France, voisins), on garde tous les départements mesurés.
    levW_all, levL_all = levels_lookup("ble"), levels_lookup("lentille")
    voisins = [d for d in VOISINS_LENTILLE if d in levL_all.index]
    lev_idf = float(levL_all[voisins].mean())
    prix = pd.read_csv(DATA / "prix_ble.csv").set_index("annee").prix_eur_t

    deps = {}
    for dep in IDF_AGRI:
        R, yL, yW, _ = simulate(meteo, dep, mL, mW, lev_idf, levW_all[dep], h, seed=int(dep))
        deps[dep] = {
            "dep": dep,
            "p_star": round(p_star(R, h["tau"])),
            "p_equilibre_median": round(p_star(R, 0.5)),
            "rendement_lentille_moyen_tha": round(float(yL.mean()), 2),
            "rendement_lentille_accepte_tha": round(float(yL.mean() * (1 - h["qualite"])), 2),
            "rendement_lentille_q10_tha": round(float(np.quantile(yL, 0.1)), 2),
            "rendement_ble_moyen_tha": round(float(yW.mean()), 2),
            "niveau_ble_qha": round(float(levW_all[dep]), 1),
            "fiabilite_par_prix": [{"prix": p, "fiabilite": round(float(np.mean(R <= p)), 3)}
                                   for p in range(400, 3001, 25)],
        }
        print(dep, {k: v for k, v in deps[dep].items() if k != "fiabilite_par_prix"})

    # Challenger LightGBM : même calcul, autre modèle de rendement, et ce qu'il a appris.
    mL2 = Calibrated("M2").fit(with_rel(L, levL))
    R2, _, _, _ = simulate(meteo, "77", mL2, mW, lev_idf, levW_all["77"], h, seed=77)
    gain = mL2.model.models[1].booster_.feature_importance(importance_type="gain")
    importances = sorted(({"variable": f, "part": round(float(g / gain.sum()), 3)}
                          for f, g in zip(FEATURES, gain)), key=lambda x: -x["part"])
    challenger = {"p_star_77": round(p_star(R2, h["tau"])), "importances_q50": importances,
                  "elargissement_conformal": round(mL2.qhat, 3)}
    print("Challenger LightGBM :", challenger)

    # Les autres façons de fixer le prix, pour la Seine-et-Marne, campagne 2026.
    mL0 = Calibrated("M0").fit(with_rel(L, levL))
    R0, _, _, _ = simulate(meteo, "77", mL0, mW, lev_idf, levW_all["77"], h, seed=77)
    prix_moyen = float(prix.loc[2010:2025].mean())
    p_moy = (prix_moyen * levW_all["77"] / 10 - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) \
        / (lev_idf / 10 * (1 - h["qualite"]))
    strategies_77 = {"moyenne": round(p_moy), "M0": round(p_star(R0, h["tau"])),
                     "M1": deps["77"]["p_star"], "M2": challenger["p_star_77"]}
    print("Stratégies 77 :", strategies_77)

    ic77 = bootstrap_p_star(df, meteo, "77", lev_idf, levW_all["77"], h)
    deps["77"]["p_star_ic80"] = [ic77[0], ic77[2]]
    print("Incertitude P* 77 (bootstrap, 10-50-90 %) :", ic77)

    # Contrat indexé : plancher = m × prix du blé de la récolte. m* au quantile τ.
    R77, yL77, yW77, pool77 = simulate(meteo, "77", mL, mW, lev_idf, levW_all["77"], h, seed=77)
    rng = np.random.default_rng(77)
    s = rng.integers(0, len(pool77), N_SIM)
    pB = pool77.prix_ble.to_numpy()[s]
    m_ratio = ((pB * yW77 - h["charges_ble"] + h["charges_lentille"] - h["bonus"]) / (yL77 * (1 - h["qualite"]))) / pB
    indexe = {"m_star": round(float(np.quantile(m_ratio, h["tau"])), 2),
              "m_median": round(float(np.quantile(m_ratio, 0.5)), 2)}

    # Sensibilités (Seine-et-Marne).
    def ps77(**kw):
        hh = h | kw
        hh["bonus"] = hh["aide"] + hh["rotation"]
        R, _, _, _ = simulate(meteo, "77", mL, mW, lev_idf, levW_all["77"], hh, seed=77)
        return round(p_star(R, hh["tau"]))
    sens = {
        "fiabilite": [{"x": t, "p_star": ps77(tau=t)} for t in np.round(np.arange(0.5, 0.96, 0.05), 2).tolist()],
        "prix_ble_fixe": [{"x": p, "p_star": ps77(prix_ble=p)} for p in (160, 200, 240, 280)],
        "charges_ble": [{"x": c, "p_star": ps77(charges_ble=c)} for c in H["charges_ble_eur_ha"]["sensibilite"]],
        "charges_lentille": [{"x": c, "p_star": ps77(charges_lentille=c)} for c in H["charges_lentille_eur_ha"]["sensibilite"]],
        "bonus_rotation": [{"x": b, "p_star": ps77(rotation=b)} for b in H["bonus_rotation_eur_ha"]["sensibilite"]],
        "sans_aide": ps77(aide=0),
        "aide": [{"x": a, "p_star": ps77(aide=a)} for a in H["aide_couplee_eur_ha"]["sensibilite"]],
        "qualite": [{"x": q, "p_star": ps77(qualite=q)} for q in H["part_non_valorisee"]["sensibilite"]],
    }
    v3 = H["scenario_historique"]["valeur"]
    sens["scenario_historique"] = ps77(charges_ble=v3["charges_ble"], charges_lentille=v3["charges_lentille"],
                                       aide=v3["aide"], rotation=v3["rotation"], qualite=v3["part_non_valorisee"])

    # Ailleurs en France : P* des départements producteurs, avec leur propre niveau.
    # Un département représente les départements dont Agreste estime le rendement avec lui.
    panel_all = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})
    grp = panel_all[panel_all.culture == "lentille"].drop_duplicates("dep").set_index("dep").serie_groupe
    noms = panel_all.drop_duplicates("dep").set_index("dep").dep_nom
    france = []
    for dep in levL.index:
        if dep not in levW_all.index or dep not in set(meteo.dep):
            continue
        R, yL, _, _ = simulate(meteo, dep, mL, mW, levL[dep], levW_all[dep], h, seed=int(dep[:2], 36))
        avec = sorted(noms[d] for d in grp[grp == dep].index if d != dep)
        france.append({"dep": dep, "nom": noms[dep], "avec": avec, "p_star": round(p_star(R, h["tau"])),
                       "rendement_lentille_qha": round(float(levL[dep]), 1),
                       "rendement_ble_qha": round(float(levW_all[dep]), 1)})
    france.sort(key=lambda x: x["p_star"])

    # Parcelles : distance au site acheteur et prix rendu de bascule.
    parc = json.loads((DATA / "parcelles.json").read_text())
    lon = np.array([p[4] for p in parc]); lat = np.array([p[5] for p in parc])
    p1, p2 = np.radians(lat), np.radians(site[1])
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(site[0] - lon) / 2) ** 2
    dist = 2 * 6371.0 * np.arcsin(np.sqrt(a)) * detour
    out_parc = []
    for p, d in zip(parc, dist):
        dep = deps[p[1]]
        # Tonnes acceptées au tri : ce sont elles que le contrat paie et que l'acheteur reçoit.
        tonnes = p[3] * dep["rendement_lentille_moyen_tha"] * (1 - h["qualite"])
        p_rendu = dep["p_star"] + h["forfait"] + kappa * d
        # [id, dep, culture actuelle, surface ha, distance km, prix rendu de bascule, tonnes, anneau,
        #  longitude, latitude] : le point représentatif permet de déplacer le site dans l'application.
        out_parc.append([p[0], p[1], p[2], p[3], round(float(d), 1), round(float(p_rendu)),
                         round(float(tonnes), 1), p[6], p[4], p[5]])

    cand = sorted((x for x in out_parc if x[2] == "ble"), key=lambda x: x[5])
    supply, j, t_cum, ha_cum, n_cum = [], 0, 0.0, 0.0, 0
    for q in PRICE_GRID:
        while j < len(cand) and cand[j][5] <= q:
            t_cum += cand[j][6]; ha_cum += cand[j][3]; n_cum += 1; j += 1
        supply.append({"prix": q, "tonnes": round(t_cum), "hectares": round(ha_cum), "parcelles": n_cum})

    # Replay : blé départemental et prix du blé mesurés ; lentille = choc national mesuré
    # appliqué au rendement moyen simulé en Île-de-France.
    panel = pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str})
    nat = pd.read_csv(DATA / "rendements_nationaux.csv").pivot(index="annee", columns="culture",
                                                               values="rendement_qha")
    replay = []
    for y in (2016, 2020):
        prev = list(range(y - 5, y))
        chocL = float(nat.lentille[y] / nat.lentille[prev].mean() - 1)
        chocW_nat = float(nat.ble[y] / nat.ble[prev].mean() - 1)
        par_dep = {}
        for dep in IDF_AGRI:
            b = panel[(panel.dep == dep) & (panel.culture == "ble")].set_index("annee").rendement_qha
            par_dep[dep] = {
                "rendement_ble_tha": round(float(b[y]) / 10, 2),
                "choc_ble": round(float(b[y] / b[prev].mean() - 1), 3),
                "rendement_lentille_tha": round(deps[dep]["rendement_lentille_moyen_tha"] * (1 + chocL), 2),
            }
        replay.append({"annee": y, "prix_ble": round(float(prix[y]), 1),
                       "choc_lentille_national": round(chocL, 3),
                       "choc_ble_national": round(chocW_nat, 3), "par_departement": par_dep})

    bt = json.loads((DATA / "backtest.json").read_text())
    commerce = pd.read_csv(DATA / "commerce_lentilles.csv")
    prix_lent = pd.read_csv(DATA / "prix_lentille_observes.csv")
    prix_lent = prix_lent[prix_lent.retenu]
    prod_nat = pd.read_csv(DATA / "rendements_nationaux.csv")
    prod_lent = prod_nat[prod_nat.culture == "lentille"].set_index("annee")
    surf_dep = (panel[(panel.culture == "lentille") & (panel.annee == 2025)]
                .groupby("dep").surface_ha.sum().round().astype(int).to_dict())
    c25 = commerce.set_index("annee").loc[2025]
    meta = {
        "campagne": TARGET_YEAR,
        "site_acheteur": site,
        "niveau_lentille_idf_qha": round(lev_idf, 1),
        "voisins_lentille": voisins,
        "panel_lentille": {"series_independantes": int(L.dep.nunique()), "cas": int(len(L)),
                           "departements_mesures": int(levL_all.size)},
        "hypotheses": H,
        "coefficients_M1_lentille": mL.model.coefficients(),
        "elargissement_conformal_lentille": round(mL.qhat, 3),
        "rendements_nationaux": [{"annee": int(a), "ble": round(float(nat.ble[a]), 1),
                                  "lentille": round(float(nat.lentille[a]), 1)} for a in nat.index],
        "prix_ble": [{"annee": int(a), "prix": float(v)} for a, v in prix.items()],
        "prix_lentille_observes": {"min": int(prix_lent.prix_eur_t.min()), "max": int(prix_lent.prix_eur_t.max()),
                                   "annees": [int(prix_lent.annee.min()), int(prix_lent.annee.max())]},
        "lentille_2025": {"production_t": round(float(prod_lent.production_q[2025]) / 10),
                          "surface_ha": round(float(prod_lent.surface_ha[2025])),
                          "importations_t": int(c25.importations_t), "exportations_t": int(c25.exportations_t),
                          # Pays d'origine hors UE, pays d'expédition dans l'UE (Comext).
                          "origines": [{"pays": r.pays, "tonnes": int(r.tonnes), "part": float(r.part)}
                                       for r in pd.read_csv(DATA / "commerce_lentilles_origines.csv").head(5).itertuples()]},
        "commerce": commerce.to_dict(orient="records"),
        # Prix des lentilles importées, €/t à la frontière (Comext, valeur / tonnes).
        "prix_import": [{"annee": int(r.annee), "monde": int(r.prix_import_eur_t), "canada": int(r.prix_import_canada_eur_t)}
                        for r in pd.read_csv(DATA / "prix_import_lentilles.csv").itertuples()
                        if r.prix_import_eur_t == r.prix_import_eur_t and r.prix_import_canada_eur_t == r.prix_import_canada_eur_t],
        "surface_lentille_par_dep_2025": surf_dep,
        "contrat_indexe": indexe,
        "challenger_lightgbm": challenger,
        "strategies_77": strategies_77,
        "france": france,
        "n_parcelles": len(out_parc),
        "n_candidates": len(cand),
    }

    APP_DATA.mkdir(parents=True, exist_ok=True)
    def dump(name, obj):
        (APP_DATA / name).write_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")))
    dump("parcels.json", out_parc)
    dump("thresholds.json", {"par_departement": list(deps.values()), "sensibilite": sens})
    dump("supply_curve.json", supply)
    dump("replay.json", replay)
    dump("backtest.json", bt)
    dump("meta.json", meta)
    dump("contours.json", json.loads((DATA / "contours_idf.json").read_text()))
    france_geo = json.loads((RAW / "geo" / "departements.geojson").read_text())
    for f in france_geo["features"]:
        f["properties"] = {"code": f["properties"]["code"], "nom": f["properties"]["nom"]}
    dump("france.json", france_geo)
    print("Contrat indexé :", indexe)
    print("Sensibilités 77 :", sens)
    print("France (5 moins chers) :", france[:5])
    print("Offre :", [s for s in supply if s["prix"] in (1000, 1200, 1400, 1600, 1800)])


if __name__ == "__main__":
    main()
