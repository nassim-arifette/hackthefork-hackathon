"""Modèle final, prix plancher par département et par parcelle, exports pour l'application.

Le modèle final est entraîné sur 2010-2025. P* est calculé pour la campagne 2026 en
rejouant les années météo 2010-2025 de chaque département d'Île-de-France.
Sorties : app/src/data/*.json, lus tels quels par le front.
"""
import json

import numpy as np
import pandas as pd

from common import APP_DATA, DATA, IDF_AGRI, VOISINS_LENTILLE, hypotheses
from model import Calibrated, break_even_prices, hyp_values, levels, load, p_star, pool_for, \
    with_rel

TARGET_YEAR = 2026
PRICE_GRID = list(range(400, 3001, 10))


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
    voisins = [d for d in VOISINS_LENTILLE if d in levL.index]
    lev_idf = float(levL[voisins].mean())

    deps = {}
    for dep in IDF_AGRI:
        pool = pool_for(meteo, dep, range(2010, 2026), TARGET_YEAR)
        R, yL, yW = break_even_prices(pool, mL, mW, lev_idf, levW[dep], h, n=20000, seed=int(dep))
        deps[dep] = {
            "dep": dep,
            "p_star": round(p_star(R, h["tau"])),
            "p_equilibre_median": round(p_star(R, 0.5)),
            "rendement_lentille_moyen_tha": round(float(yL.mean()), 2),
            "rendement_lentille_q10_tha": round(float(np.quantile(yL, 0.1)), 2),
            "rendement_ble_moyen_tha": round(float(yW.mean()), 2),
            "niveau_ble_qha": round(float(levW[dep]), 1),
            "fiabilite_par_prix": [{"prix": p, "fiabilite": round(float(np.mean(R <= p)), 3)}
                                   for p in range(400, 3001, 50)],
        }
        print(dep, {k: v for k, v in deps[dep].items() if k != "fiabilite_par_prix"})

    # Sensibilités (Seine-et-Marne).
    pool77 = pool_for(meteo, "77", range(2010, 2026), TARGET_YEAR)
    def ps77(**kw):
        hh = h | kw
        R, _, _ = break_even_prices(pool77, mL, mW, lev_idf, levW["77"], hh, n=20000, seed=77)
        return round(p_star(R, hh["tau"]))
    sens = {
        "fiabilite": [{"x": t, "p_star": ps77(tau=t)} for t in np.round(np.arange(0.5, 0.96, 0.05), 2).tolist()],
        "prix_ble": [{"x": p, "p_star": ps77(prix_ble=p)} for p in H["prix_ble_eur_t"]["sensibilite"]],
        "bonus_rotation": [{"x": b, "p_star": ps77(bonus=b)} for b in H["bonus_rotation_eur_ha"]["sensibilite"]],
        "charges_lentille": [{"x": round(h["charges_lentille"] * f), "p_star": ps77(charges_lentille=h["charges_lentille"] * f)}
                             for f in (0.8, 1.0, 1.2)],
    }

    # Parcelles : distance au site acheteur et prix rendu de bascule.
    parc = json.loads((DATA / "parcelles.json").read_text())
    lon = np.array([p[4] for p in parc]); lat = np.array([p[5] for p in parc])
    r = 6371.0
    p1, p2 = np.radians(lat), np.radians(site[1])
    a = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(np.radians(site[0] - lon) / 2) ** 2
    dist = 2 * r * np.arcsin(np.sqrt(a)) * detour
    out_parc = []
    for p, d in zip(parc, dist):
        dep = deps[p[1]]
        tonnes = p[3] * dep["rendement_lentille_moyen_tha"]
        p_rendu = dep["p_star"] + kappa * d
        # [id, dep, culture actuelle, surface ha, distance km, prix rendu de bascule, tonnes, anneau]
        out_parc.append([p[0], p[1], p[2], p[3], round(float(d), 1), round(float(p_rendu)),
                         round(float(tonnes), 1), p[6]])

    cand = sorted((x for x in out_parc if x[2] == "ble"), key=lambda x: x[5])
    supply, j, t_cum, ha_cum, n_cum = [], 0, 0.0, 0.0, 0
    for q in PRICE_GRID:
        while j < len(cand) and cand[j][5] <= q:
            t_cum += cand[j][6]; ha_cum += cand[j][3]; n_cum += 1; j += 1
        supply.append({"prix": q, "tonnes": round(t_cum), "hectares": round(ha_cum), "parcelles": n_cum})

    # Replay : blé départemental mesuré, lentille = choc national mesuré appliqué au niveau francilien.
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
        replay.append({"annee": y, "choc_lentille_national": round(chocL, 3),
                       "choc_ble_national": round(chocW_nat, 3), "par_departement": par_dep})

    bt = json.loads((DATA / "backtest.json").read_text())
    nat_rows = [{"annee": int(a), "ble": round(float(nat.ble[a]), 1), "lentille": round(float(nat.lentille[a]), 1)}
                for a in nat.index]
    meta = {
        "campagne": TARGET_YEAR,
        "site_acheteur": site,
        "niveau_lentille_idf_qha": round(lev_idf, 1),
        "voisins_lentille": voisins,
        "hypotheses": {k: {kk: vv for kk, vv in v.items()} for k, v in H.items()},
        "coefficients_M1_lentille": mL.model.coefficients(),
        "elargissement_conformal_lentille": round(mL.qhat, 3),
        "rendements_nationaux": nat_rows,
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
    print("Sensibilités 77 :", sens)
    print("Offre à 900, 1200, 1500 €/t :", [s for s in supply if s["prix"] in (900, 1200, 1500)])


if __name__ == "__main__":
    main()
