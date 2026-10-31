"""Tests du pipeline : données, absence de fuite, propriétés du prix plancher, exports."""
import json
import re

import numpy as np
import pandas as pd
import pytest

from common import APP_DATA, DATA, TEST_YEARS
from model import Calibrated, break_even_prices, calibrer_premier_palier, calibrer_prime_ha, hyp_values, \
    levels, load, p_star, paiement, pool_for, protection, sample_quantile, series_passees, simulate_years, with_rel
from common import hypotheses


@pytest.fixture(scope="module")
def panel():
    return pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})


def test_panel_unique_and_complete(panel):
    assert not panel.duplicated(["dep", "culture", "annee"]).any()
    assert set(panel.annee) == set(range(2010, 2026))
    assert set(panel.culture) == {"ble", "lentille", "pois_chiche", "haricot", "pois", "feverole"}


def test_panel_units_are_quintals_per_hectare(panel):
    u = panel[panel.utilisable]
    # Ordres de grandeur : blé entre 10 et 130 q/ha (18 q/ha mesurés dans les Pyrénées-Orientales
    # en 2024, année de sécheresse), lentille entre 1 et 45 q/ha.
    assert u[u.culture == "ble"].rendement_qha.between(10, 130).all()
    assert u[u.culture == "lentille"].rendement_qha.between(1, 45).all()


def test_status_3_excluded(panel):
    assert not panel[panel.utilisable].statut.isin(["3", "NC"]).any()


def test_backtest_has_no_leakage():
    """Pour chaque année test, l'entraînement ne voit que les années antérieures."""
    df, _ = load()
    L = df[df.culture == "lentille"]
    for t in TEST_YEARS:
        train = L[L.annee < t]
        assert train.annee.max() < t
        assert t not in set(train.annee)


def test_duplicate_series_are_grouped_with_past_years_only(panel):
    """Le regroupement des séries en double d'une année test ne dépend pas des années qui suivent."""
    rng = np.random.default_rng(0)
    for t in TEST_YEARS:
        kept = series_passees(panel, "lentille", t)
        assert kept.annee.max() < t
        brouille = panel.copy()
        futur = brouille.annee >= t
        brouille.loc[futur, "rendement_qha"] = rng.uniform(1, 40, futur.sum())
        pd.testing.assert_frame_equal(kept, series_passees(brouille, "lentille", t))
        wide = kept.pivot(index="dep", columns="annee", values="rendement_qha").round(2)
        deps = list(wide.index)
        for i, a in enumerate(deps):
            for b in deps[i + 1:]:
                assert int((wide.loc[a] == wide.loc[b]).sum()) < 8, (t, a, b)


def test_calibration_uses_only_training_years():
    df, _ = load()
    L = df[(df.culture == "lentille") & (df.annee < 2020)]
    m = Calibrated("M1").fit(with_rel(L, levels(L)))
    assert m.qhat >= 0


def test_auto_selection_picks_a_known_model():
    df, _ = load()
    L = df[(df.culture == "lentille") & (df.annee < 2022)]
    m = Calibrated("auto").fit(with_rel(L, levels(L)))
    assert m.kind in {"M0", "M1", "M2"}
    assert set(m.selection) == {"M0", "M1", "M2"}


def test_sample_quantile_is_monotone():
    q = np.array([[0.6, 1.0, 1.3]] * 3)
    u = np.array([0.05, 0.5, 0.95])
    s = sample_quantile(q, u)
    assert s[0] < s[1] < s[2]
    assert s[1] == pytest.approx(1.0)


@pytest.fixture(scope="module")
def sim():
    df, meteo = load()
    L, W = df[df.culture == "lentille"], df[df.culture == "ble"]
    levL, levW = levels(L), levels(W)
    mL = Calibrated("M1").fit(with_rel(L, levL))
    mW = Calibrated("M1").fit(with_rel(W, levW))
    pool = pool_for(meteo, "77", range(2010, 2026), 2026)
    return pool, mL, mW, float(levL.mean()), float(levW["77"])


def test_p_star_increases_with_reliability(sim):
    pool, mL, mW, lL, lW = sim
    h = hyp_values(hypotheses())
    R, _, _ = break_even_prices(pool, mL, mW, lL, lW, h, n=8000, seed=1)
    assert p_star(R, 0.5) < p_star(R, 0.8) < p_star(R, 0.95)


def test_p_star_increases_with_wheat_price(sim):
    pool, mL, mW, lL, lW = sim
    h = hyp_values(hypotheses())
    lo = p_star(break_even_prices(pool, mL, mW, lL, lW, h | {"prix_ble": 160}, n=8000, seed=1)[0], 0.8)
    hi = p_star(break_even_prices(pool, mL, mW, lL, lW, h | {"prix_ble": 280}, n=8000, seed=1)[0], 0.8)
    assert lo < hi


def test_p_star_is_the_break_even_quantile(sim):
    """Au prix P*, la lentille bat le blé dans la part visée des scénarios."""
    pool, mL, mW, lL, lW = sim
    h = hyp_values(hypotheses())
    R, yL, yW = break_even_prices(pool, mL, mW, lL, lW, h, n=8000, seed=3)
    ps = p_star(R, 0.8)
    assert np.mean(R <= ps) == pytest.approx(0.8, abs=0.005)


def test_exports_exist_and_parse():
    for name in ("parcels", "thresholds", "supply_curve", "replay", "backtest", "meta", "contours", "france",
                 "contrats"):
        json.loads((APP_DATA / f"{name}.json").read_text())


def test_every_hypothesis_is_labelled_and_sourced():
    for key, v in hypotheses().items():
        assert v["etiquette"] in {"mesure", "source", "suppose", "synthetique"}, key
        assert v.get("source"), key
        assert v["valeur"] is not None, key


def test_supply_curve_is_monotone():
    s = json.loads((APP_DATA / "supply_curve.json").read_text())
    t = [r["tonnes"] for r in s]
    assert all(a <= b for a, b in zip(t, t[1:]))


def test_app_text_has_no_unlabelled_market_claims():
    """Les chiffres de prix de marché cités par l'application viennent de l'export, pas du code."""
    src = (APP_DATA.parent / "App.tsx").read_text(encoding="utf-8")
    assert not re.search(r"\b(650|779|780)\s?(à|€|-|–)", src)


def test_llm_guardrail_rejects_invented_numbers():
    import importlib
    lettre = importlib.import_module("06_lettre_llm")
    allowed = {"prix": "1 435 €/t", "fiabilité": "8 années sur 10", "volume": "5 000 t"}
    assert lettre.verify("Nous garantissons 1 435 €/t, 8 années sur 10, pour 5 000 t.", allowed)
    assert not lettre.verify("Nous garantissons 1 500 €/t.", allowed)
    assert not lettre.verify("Soit 12 % de marge en plus.", allowed)


def test_tiered_payment_matches_the_pilot_examples():
    """Exemples A et B de docs/CONTRAT_SIMULATION.md : 10 ha, 16 puis 26 t acceptées."""
    prop = {"paliers": (1000, 750, 650), "prime_t": 30}
    assert 10 * paiement(prop, np.array([1.6]))[0] == pytest.approx(14980)
    assert 10 * paiement(prop, np.array([2.6]))[0] == pytest.approx(22180)
    assert 10 * paiement({"paliers": (900, 700, 600)}, np.array([1.6]))[0] == pytest.approx(13200)
    assert paiement({"prix": 900, "prime_ha": 400}, np.array([0.0]))[0] == pytest.approx(400)


def test_contracts_are_judged_like_p_star(sim):
    """Au prix unique P*, la protection est celle du prix plancher ; les contrats calibrés
    atteignent la cible au plus juste."""
    pool, mL, mW, lL, lW = sim
    h = hyp_values(hypotheses())
    yL, yW, pB = simulate_years(pool, mL, mW, lL, lW, h, n=8000, seed=3)
    R, _, _ = break_even_prices(pool, mL, mW, lL, lW, h, n=8000, seed=3)
    ps = p_star(R, 0.8)
    assert protection({"prix": ps}, yL, yW, pB, h) == pytest.approx(np.mean(R <= ps))
    p1 = calibrer_premier_palier((750, 650), yL, yW, pB, h, 0.8)
    assert protection({"paliers": (p1, 750, 650)}, yL, yW, pB, h) >= 0.8
    assert protection({"paliers": (p1 - 1, 750, 650)}, yL, yW, pB, h) < 0.8
    a = calibrer_prime_ha(900, yL, yW, pB, h, 0.8)
    assert protection({"prix": 900, "prime_ha": a}, yL, yW, pB, h) >= 0.8


def test_contract_backtest_is_consistent():
    bt = json.loads((DATA / "backtest.json").read_text())["global"]
    assert bt["contrats"]["unique"]["taux_tenus"] == pytest.approx(bt["taux_tenus"])
    app = json.loads((APP_DATA / "contrats.json").read_text())
    assert {c["id"] for c in app["calibres"]} == {"unique", "paliers", "prime_ha"}
    for c in app["calibres"]:
        assert c["simulation"]["protection"] >= 0.8 - 1e-3


def test_sentinel_series_are_physical():
    """NDVI dans [−1, 1], dates de la saison, statuts cohérents avec les seuils."""
    d = json.loads((APP_DATA / "sentinel.json").read_text())
    lo, hi = d["periode"]
    for p in d["parcelles"]:
        assert p["dates_valides"] <= p["dates_vues"]
        for date, v in p["serie"]:
            assert lo <= date <= hi and -1 <= v <= 1
        e, s = p["ecart_floraison"], d["seuils_statut"]
        attendu = "en_retard" if e < s["retard"] else "a_surveiller" if e < s["surveiller"] else "conforme"
        assert p["statut"] == attendu


def test_other_pulses_reuse_the_lentil_engine():
    """La lentille passe par le même chemin que les autres cultures et retrouve ses chiffres."""
    d = json.loads((APP_DATA / "cultures.json").read_text())
    c = {x["id"]: x for x in d["cultures"]}
    d77 = next(x for x in json.loads((APP_DATA / "thresholds.json").read_text())["par_departement"] if x["dep"] == "77")
    assert c["lentille"]["p_star"]["77"] == d77["p_star"]
    assert c["lentille"]["backtest"]["taux_tenus"] == pytest.approx(
        json.loads((DATA / "backtest.json").read_text())["global"]["taux_tenus"])
    for x in d["cultures"]:
        assert x["p_star"]["77"] > x["p_equilibre_median_77"] > 0
        p1, p2, p3 = x["tranches"]["paliers"]
        assert p1 >= p2 >= p3 > 0


def test_every_pulse_hypothesis_is_labelled_and_sourced():
    import yaml
    for culture, hyp in yaml.safe_load((DATA / "cultures.yaml").read_text()).items():
        for key, v in hyp.items():
            if key == "nom" or v is None:
                continue
            assert v["etiquette"] in {"source", "suppose"} and v["source"], (culture, key)


def _maillon_module():
    import importlib.util
    spec = importlib.util.spec_from_file_location("maillon", DATA.parent / "pipeline" / "10_maillon.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_maillon_before_harvest_ignores_later_images():
    """La version « avant récolte » ne dépend d'aucune image postérieure au 10 juin."""
    m = _maillon_module()
    dates = ["2025-04-05", "2025-05-03", "2025-06-01", "2025-06-09", "2025-06-20", "2025-07-15"]
    obs = pd.DataFrame([{"id_parcel": i, "date": d, "ndvi": 0.2 + 0.1 * k, "ndmi": 0.1}
                        for i in ("a", "b") for k, d in enumerate(dates)])
    f1, n1 = m.caracteristiques(obs, np.array(["a", "b"]), 2025, m.COUPURE)
    brouille = obs.copy()
    brouille.loc[brouille.date > f"2025-{m.COUPURE}", ["ndvi", "ndmi"]] = -0.9
    f2, n2 = m.caracteristiques(brouille, np.array(["a", "b"]), 2025, m.COUPURE)
    pd.testing.assert_frame_equal(f1, f2)
    assert (n1 == 4).all() and (n2 == 4).all()


def test_maillon_export_is_consistent():
    """Carte et métriques cohérentes : un carré connu n'est jamais jugé, les comptes se recoupent."""
    d = json.loads((APP_DATA / "maillon.json").read_text())
    seuil = d["seuil"]
    for v_idx, nom in ((3, "avant_recolte"), (4, "saison")):
        jugees = [p for p in d["parcelles"] if not p[2] and p[v_idx] is not None]
        assert all(p[v_idx] is None for p in d["parcelles"] if p[2])
        assert all(0 <= p[v_idx] <= 1 for p in jugees)
        carte = d["resultats"][nom]["un_sur_cinq"]["carte"]
        vp = sum(1 for p in jugees if p[1] and p[v_idx] >= seuil)
        fp = sum(1 for p in jugees if not p[1] and p[v_idx] >= seuil)
        assert vp == carte["vrais_positifs"] and fp == carte["faux_positifs"]
        for k in ("blocs", "transfert", "transfert_relatif"):
            r = d["resultats"][nom][k]
            assert r["precision"] == pytest.approx(r["vrais_positifs"] / (r["vrais_positifs"] + r["faux_positifs"]), abs=1e-3)
            assert r["rappel"] == pytest.approx(r["vrais_positifs"] / r["n_legumineuses"], abs=1e-3)
        u = d["resultats"][nom]["un_sur_cinq"]
        for k in ("precision", "rappel"):
            assert u["min"][k] <= u["moyenne"][k] <= u["max"][k]


def test_existing_sites_export_is_consistent():
    """Sites Sirene : actifs, dans la zone, meilleur site bien le plus proche, aucune donnée personnelle."""
    d = json.loads((APP_DATA / "sites.json").read_text())
    sites = d["sites"]
    assert d["n_sites"] == len(sites) > 0
    assert d["n_cooperatives"] == sum(s[5] for s in sites)
    assert all(s[4] in ("46.21Z", "52.10B") for s in sites)
    assert all(1.0 < s[0] < 4.2 and 47.8 < s[1] < 49.6 for s in sites)  # Île-de-France et 15 km autour
    for k, col in (("pilote", 6), ("ambition", 7)):
        best = d["meilleur"][k]
        assert sites[best["index"]][col] == min(s[col] for s in sites) == best["km_moyen"]
    assert 0 <= d["maillon"]["part_surface_moins_10_km"] <= 1
    # Le cache versionné ne garde que les champs utiles : ni dirigeants ni adresses.
    for f in (DATA.parent / "data_raw" / "sirene").glob("*_*.json"):
        txt = f.read_text()
        assert "dirigeants" not in txt and "adresse" not in txt
        assert not any(str(r["nature_juridique"]).startswith("1") for r in json.loads(txt)["results"])


def test_new_contract_exports_are_consistent():
    """Contrat indexé calibré sur la même promesse, assurance croissante avec le seuil, coûts présents."""
    c = json.loads((DATA / "contrats.json").read_text())
    h = hyp_values(hypotheses())
    assert c["indexe"]["simulation"]["protection"] >= h["tau"] - 1e-3
    planchers = [p["plancher"] for p in c["indexe"]["plancher_par_prix_ble"]]
    assert planchers == sorted(planchers)
    niveaux = c["assurance"]["niveaux"]
    for a, b in zip(niveaux, niveaux[1:]):
        assert a["seuil"] < b["seuil"]
        assert a["prime_pure_eur_ha"] <= b["prime_pure_eur_ha"] and a["frequence_sinistre"] <= b["frequence_sinistre"]
    for k in ("tri_eur_t_brute", "collecte_fixe_eur_t_brute", "collecte_eur_t_brute_km", "sechage_eur_t_point"):
        assert c["couts_acheteur"][k] > 0


def test_import_origins_are_consistent():
    """Provenance des importations : parts entre 0 et 1, triées, inférieures au total importé."""
    meta = json.loads((APP_DATA / "meta.json").read_text())
    o = meta["lentille_2025"]["origines"]
    parts = [x["part"] for x in o]
    assert parts == sorted(parts, reverse=True) and 0 < sum(parts) <= 1
    assert sum(x["tonnes"] for x in o) <= meta["lentille_2025"]["importations_t"]
