"""Évaluation glissante, décisions calculées exclusivement sur le passé.

Les rendements test et le prix du blé servent uniquement au verdict économique.
Les scores de rendement sont conditionnels à la météo réalisée, pas une prévision
avant semis. Charges et aides sont des hypothèses communes : les marges sont
reconstituées, pas des comptes d'exploitation observés.
"""
import json

import numpy as np
import pandas as pd

from common import DATA, TEST_YEARS, hypotheses
from model import (MODELS, Calibrated, break_even_prices, hyp_values, load,
                   p_star, pinball, pool_for, prepare_as_of)

# Grille fixée avant l'évaluation, jamais optimisée sur les années test.
TAU_GRID = (0.5, 0.6, 0.7, 0.8, 0.9, 0.95)
SUFFIX = {"M0": "_M0", "M1": "", "M2": "_M2", "M3": "_M3", "auto": "_auto"}


def historical_break_even(train: pd.DataFrame, dep: str, h: dict) -> np.ndarray:
    """Prix d'équilibre passés : cultures et prix appariés par département-année."""
    d = train[train.dep == dep]
    lentil = d[d.culture == "lentille"][["annee", "rendement_qha", "prix_ble"]]
    wheat = d[d.culture == "ble"][["annee", "rendement_qha"]]
    paired = lentil.merge(wheat, on="annee", suffixes=("_L", "_W"), validate="one_to_one").dropna()
    paired = paired[paired.rendement_qha_L > 0]
    if paired.empty:
        raise ValueError(f"Aucune année lentille/blé appariée pour {dep}")
    wheat_price = h["prix_ble"] if h.get("prix_ble") is not None else paired.prix_ble.to_numpy()
    return ((wheat_price * paired.rendement_qha_W.to_numpy() / 10
             - h["charges_ble"] + h["charges_lentille"] - h["bonus"])
            / (paired.rendement_qha_L.to_numpy() / 10))


def economic_outcome(price: float, lentil_yield: float, wheat_margin: float, h: dict) -> dict:
    """Résultat pour un hectare ; rendement t/ha, prix départ ferme €/t."""
    purchase = price * lentil_yield
    margin = purchase - h["charges_lentille"] + h["bonus"]
    return {"prix_eur_t": float(price), "marge_lentille_eur_ha": float(margin),
            "manque_eur_ha": float(max(0.0, wheat_margin - margin)),
            "cout_achat_eur_ha": float(purchase), "tenu": bool(margin >= wheat_margin)}


def _round_outcome(result: dict) -> dict:
    return {key: value if isinstance(value, bool) else round(value, 2) for key, value in result.items()}


def evaluate_year(df: pd.DataFrame, meteo: pd.DataFrame, h: dict, year: int,
                  model_kinds=None, n_scenarios: int = 6000) -> tuple[dict, list[dict]]:
    """Vrai chemin de décision, également appelé par les tests de perturbation.

    df/meteo peuvent contenir le futur ; la décision n'en utilise aucune ligne.
    Regroupement, niveaux et transformations sont ajustés dans le modèle sur son
    seul bloc d'apprentissage propre, avant sélection puis calibration.
    """
    kinds = tuple(model_kinds or (*MODELS, "auto"))
    train = prepare_as_of(df, year)
    trL, trW = train[train.culture == "lentille"], train[train.culture == "ble"]
    models = {kind: Calibrated(kind).fit(trL) for kind in kinds}
    wheat_model = Calibrated("auto").fit(trW)
    reference = models.get("M1", next(iter(models.values())))
    eligible = set(reference.retained_deps) & set(wheat_model.levels.index)
    for model in models.values():
        eligible &= set(model.levels.index)
    observed_wheat = df[(df.culture == "ble") & (df.annee == year)].set_index("dep").rendement_qha
    eligible &= set(observed_wheat[observed_wheat.notna()].index)
    te = df[(df.culture == "lentille") & (df.annee == year) & df.dep.isin(eligible)].copy()
    te = te.sort_values("dep").reset_index(drop=True)
    if te.empty:
        raise ValueError(f"Aucun département évaluable en {year}")
    # Niveaux identiques entre candidats : mêmes années d'apprentissage propre.
    normalizer = reference.levels.reindex(te.dep).to_numpy()
    y = te.rendement_qha.to_numpy() / normalizer
    quantiles = {kind: model.predict_quantiles(te) for kind, model in models.items()}
    intervals = {kind: model.predict(te) for kind, model in models.items()}
    wheat_prices = meteo.loc[meteo.annee == year, "prix_ble"].dropna().unique()
    if len(wheat_prices) != 1:
        raise ValueError(f"Prix national du blé non unique ou absent en {year}")
    wheat_price = float(wheat_prices[0])
    row = {"annee": int(year), "n_dep": int(len(te)), "prix_ble": round(wheat_price, 1),
           "modele_auto": models["auto"].kind if "auto" in models else None,
           "modele_ble_auto": wheat_model.kind,
           "audit": {kind: model.audit for kind, model in models.items()},
           "audit_ble": wheat_model.audit}
    for kind in kinds:
        q, interval = quantiles[kind], intervals[kind]
        row[f"pinball_{kind}"] = round(pinball(q, y), 6)
        row[f"couverture_{kind}"] = round(float(np.mean((y >= interval[:, 0]) & (y <= interval[:, 2]))), 6)
        row[f"largeur_{kind}"] = round(float(np.mean(interval[:, 2] - interval[:, 0])), 6)
        row[f"erreur_mediane_{kind}"] = round(float(np.median(np.abs(q[:, 1] - y))), 6)
        row[f"erreur_mediane_qha_{kind}"] = round(float(np.median(np.abs(q[:, 1] - y) * normalizer)), 4)

    detail = []
    diagnostic_kind = "M1" if "M1" in models else kinds[0]
    past_meteo = meteo[meteo.annee < year]
    tau_values = sorted(set(TAU_GRID) | {float(h["tau"])})
    for i, observation in te.iterrows():
        dep = observation.dep
        lentil_yield = float(observation.rendement_qha) / 10
        wheat_yield = float(observed_wheat[dep]) / 10
        wheat_margin = wheat_price * wheat_yield - h["charges_ble"]
        pool = pool_for(past_meteo, dep, sorted(past_meteo.annee.unique()), year)
        if pool.empty or pool.prix_ble.isna().any():
            raise ValueError(f"Historique météo/prix incomplet pour {dep}, décision {year}")
        historical = historical_break_even(train, dep, h)
        paired_l = trL[trL.dep == dep][["annee", "rendement_qha", "prix_ble"]]
        paired_w = trW[trW.dep == dep][["annee", "rendement_qha"]]
        paired = paired_l.merge(paired_w, on="annee", suffixes=("_L", "_W")).dropna()
        pB = h["prix_ble"] if h.get("prix_ble") is not None else paired.prix_ble.to_numpy()
        price_mean = float((np.mean(pB * paired.rendement_qha_W.to_numpy() / 10)
                           - h["charges_ble"] + h["charges_lentille"] - h["bonus"])
                          / (paired.rendement_qha_L.mean() / 10))
        distributions = {"historique": historical}
        for kind, model in models.items():
            distributions[kind] = break_even_prices(
                pool, model, wheat_model, float(model.levels[dep]),
                float(wheat_model.levels[dep]), h, n=n_scenarios,
                seed=int(year) * 1000 + int(dep))[0]
        methods = {kind: economic_outcome(p_star(values, h["tau"]), lentil_yield, wheat_margin, h)
                   for kind, values in distributions.items()}
        methods["moyenne"] = economic_outcome(price_mean, lentil_yield, wheat_margin, h)
        frontier = [{"methode": kind, "tau": tau,
                     **_round_outcome(economic_outcome(p_star(values, tau), lentil_yield, wheat_margin, h))}
                    for kind, values in distributions.items() for tau in tau_values]
        q, interval = quantiles[diagnostic_kind][i], intervals[diagnostic_kind][i]
        record = {"annee": int(year), "dep": dep, "dep_nom": observation.dep_nom,
                  "rendement_lentille_reel": round(float(observation.rendement_qha), 2),
                  "rendement_ble_reel": round(float(observed_wheat[dep]), 2),
                  "prix_ble_reference": round(wheat_price, 2), "marge_ble": round(wheat_margin, 2),
                  "niveau_lentille_qha": round(float(normalizer[i]), 4),
                  "ic80_rel": [round(float(interval[0]), 6), round(float(interval[2]), 6)],
                  "q50_rel": round(float(q[1]), 6), "rel_reel": round(float(y[i]), 6),
                  "n_annees_historique_apparie": int(len(historical)),
                  "methodes": {kind: _round_outcome(result) for kind, result in methods.items()},
                  "frontiere": frontier,
                  "predictions": {kind: {"quantiles_rel": np.round(quantiles[kind][i], 6).tolist(),
                                          "intervalle80_rel": np.round(intervals[kind][i, [0, 2]], 6).tolist()}
                                  for kind in kinds}}
        # Compatibilité : les champs sans suffixe restent les résultats M1.
        for kind, result in methods.items():
            if kind in SUFFIX:
                suffix = SUFFIX[kind]
                record |= {f"p_star{suffix}": round(result["prix_eur_t"]),
                           f"marge_lentille{suffix}": round(result["marge_lentille_eur_ha"]),
                           f"tenu{suffix}": result["tenu"]}
            else:
                record[f"p_{kind}"] = round(result["prix_eur_t"])
                record[f"tenu_{kind}"] = result["tenu"]
        detail.append(record)
    row["n_contrats"] = len(detail)
    for kind in detail[0]["methodes"]:
        suffix = "" if kind == "M1" else f"_{kind}"
        row[f"taux_tenus{suffix}"] = round(float(np.mean([r["methodes"][kind]["tenu"] for r in detail])), 6)
    if "M1" in models:
        row["p_star_median"] = round(float(np.median([r["methodes"]["M1"]["prix_eur_t"] for r in detail])))
    return row, detail


def summarise_economics(records: list[dict], seed: int = 732, n_bootstrap: int = 2000) -> dict:
    """Résumé ; bootstrap d'années entières, départements conservés ensemble.

    IC descriptif, avec peu de blocs annuels : ni indépendance temporelle, ni
    garantie individuelle, ni validité prospective ne sont établies.
    """
    table = pd.DataFrame(records)
    if table.empty:
        raise ValueError("Aucun résultat économique à résumer")
    shortfall = table.manque_eur_ha.to_numpy()
    failed = shortfall[shortfall > 0]
    by_year = table.groupby("annee").tenu.agg(["sum", "count"])
    rng = np.random.default_rng(seed)
    indices = rng.integers(0, len(by_year), size=(n_bootstrap, len(by_year)))
    ratios = by_year["sum"].to_numpy()[indices].sum(axis=1) / by_year["count"].to_numpy()[indices].sum(axis=1)
    return {"n_cas": int(len(table)), "taux_tenus": round(float(table.tenu.mean()), 6),
            "prix_median_eur_t": round(float(table.prix_eur_t.median()), 2),
            "prix_moyen_eur_t": round(float(table.prix_eur_t.mean()), 2),
            "manque_moyen_eur_ha": round(float(shortfall.mean()), 2),
            "manque_moyen_si_echec_eur_ha": round(float(failed.mean()), 2) if len(failed) else 0.0,
            "manque_p95_eur_ha": round(float(np.quantile(shortfall, 0.95)), 2),
            "cout_achat_moyen_eur_ha": round(float(table.cout_achat_eur_ha.mean()), 2),
            "taux_tenus_ic95_bootstrap_annees": np.round(np.quantile(ratios, [0.025, 0.975]), 4).tolist()}


def run_backtest(df=None, meteo=None, h=None, years=TEST_YEARS, model_kinds=None,
                 n_scenarios: int = 6000) -> dict:
    if df is None or meteo is None:
        df, meteo = load()
    h = hyp_values(hypotheses()) if h is None else h
    detail, annual = [], []
    for year in years:
        row, observations = evaluate_year(df, meteo, h, year, model_kinds, n_scenarios)
        annual.append(row)
        detail.extend(observations)
        print(f"{year}: n={row['n_dep']} sélection={row['modele_auto']} "
              f"succès M1={row.get('taux_tenus')} P* médian={row.get('p_star_median')}", flush=True)
    if not detail:
        raise ValueError("Aucune année évaluée")
    kinds = tuple(model_kinds or (*MODELS, "auto"))
    economy = {kind: summarise_economics([{"annee": r["annee"], **r["methodes"][kind]} for r in detail])
               for kind in detail[0]["methodes"]}
    frontier = []
    for kind in (k for k in economy if k != "moyenne"):
        for tau in sorted(set(TAU_GRID) | {float(h["tau"])}):
            observations = [{"annee": r["annee"], **f} for r in detail for f in r["frontiere"]
                            if f["methode"] == kind and f["tau"] == tau]
            frontier.append({"methode": kind, "tau": tau, **summarise_economics(observations)})
    aggregate = {"n_cas": len(detail), "n_annees": len(annual)}
    for kind, stats in economy.items():
        suffix = "" if kind == "M1" else f"_{kind}"
        aggregate[f"taux_tenus{suffix}"] = stats["taux_tenus"]
        aggregate[f"p_star_median_{kind}"] = stats["prix_median_eur_t"]
    aggregate["p_moyenne_median"] = economy["moyenne"]["prix_median_eur_t"]
    weights = np.array([r["n_dep"] for r in annual], dtype=float)
    weights /= weights.sum()
    for kind in kinds:
        for metric in ("pinball", "couverture", "largeur"):
            aggregate[f"{metric}_{kind}"] = round(float(np.dot(weights, [r[f"{metric}_{kind}"] for r in annual])), 6)
    if "M0" in kinds:
        for kind in kinds:
            baseline = aggregate["pinball_M0"]
            aggregate[f"gain_pinball_{kind}_vs_M0"] = round(1 - aggregate[f"pinball_{kind}"] / baseline, 6) if baseline else None
    for kind in kinds:
        errors = np.array([abs(r["rel_reel"] - r["predictions"][kind]["quantiles_rel"][1]) for r in detail])
        aggregate[f"erreur_mediane_{kind}"] = round(float(np.median(errors)), 6)
        aggregate[f"erreur_mediane_qha_{kind}"] = round(float(np.median(
            errors * np.array([r["niveau_lentille_qha"] for r in detail]))), 4)
    return {
        "protocole": ("Reconstitution économique glissante sous charges, aides et prix de référence affichés. "
                      "Pour chaque année test, regroupement, normalisation et transformations ajustés sur "
                      "l'apprentissage propre ; deux années distinctes pour la sélection ; trois dernières "
                      "années antérieures au test pour la calibration ; aucun réentraînement après calibration. "
                      "Prix décidé avant l'année test avec les seules météos et références de prix antérieures. "
                      "M0–M3 désignent le prédicteur lentille ; le prédicteur blé commun est sélectionné automatiquement. "
                      "La référence historique apparie rendement lentille, rendement blé et prix par département-année. "
                      "Les taux ne sont pas directement comparables aux anciennes versions du protocole. "
                      "Ces années ont déjà été examinées pendant le développement : cette évaluation "
                      "rétrospective ne remplace pas une validation prospective sur une nouvelle campagne."),
        "diagnostic_rendement": ("Perte pinball sur les quantiles bruts ; couverture sur les intervalles corrigés. "
                                 "Diagnostics conditionnels à la météo effectivement réalisée durant l'année test. "
                                 "Ils ne mesurent pas une prévision météo avant semis."),
        "incertitude": ("IC descriptifs à 95 % par bootstrap d'années entières ; peu de blocs annuels, "
                        "dépendance temporelle et spatiale possible. Aucune garantie individuelle de couverture "
                        "ou de marge. Coût d'achat par hectare récolté, sans transformation ni transport."),
        "distribution": ("Les simulations utilisent les quantiles bruts, séparés des bornes d'intervalle calibrées. "
                         "Interpolation, queues et dépendance résiduelle sont des hypothèses distinctes de la calibration. "
                         "La météo et le prix du blé sont appariés ; la référence historique conserve "
                         "l'appariement complet des rendements et prix observés."),
        "prix_ble_libelle": "Prix de référence reconstruit à partir d'Eurostat et d'Agreste",
        "scenario_economique": {"charges_ble_eur_ha": h["charges_ble"],
                               "charges_lentille_eur_ha": h["charges_lentille"],
                               "aide_eur_ha": h["aide"], "bonus_rotation_eur_ha": h["rotation"],
                               "base_prix": "départ ferme", "campagnes_par_decision": 1},
        "fiabilite_visee": h["tau"], "global": aggregate, "economie": economy,
        "frontiere_prix_protection": frontier, "annees": annual, "detail": detail,
    }


def main():
    result = run_backtest()
    (DATA / "backtest.json").write_text(json.dumps(result, ensure_ascii=False, indent=1, allow_nan=False))
    print("Global :", result["global"])


if __name__ == "__main__":
    main()
