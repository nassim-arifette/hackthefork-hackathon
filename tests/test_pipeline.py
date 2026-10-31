"""Tests du pipeline : données, absence de fuite, propriétés du prix plancher, exports."""
import json
import re

import numpy as np
import pandas as pd
import pytest

from common import APP_DATA, DATA, TEST_YEARS
from model import MODELS, Calibrated, break_even_prices, hyp_values, load, p_star, pool_for, sample_quantile
from common import hypotheses


@pytest.fixture(scope="module")
def panel():
    return pd.read_csv(DATA / "panel_rendements.csv", dtype={"dep": str, "serie_groupe": str})


def test_panel_unique_and_complete(panel):
    assert not panel.duplicated(["dep", "culture", "annee"]).any()
    assert set(panel.annee) == set(range(2010, 2026))
    assert set(panel.culture) == {"ble", "lentille"}


def test_panel_units_are_quintals_per_hectare(panel):
    u = panel[panel.utilisable]
    # Ordres de grandeur : blé entre 10 et 130 q/ha (18 q/ha mesurés dans les Pyrénées-Orientales
    # en 2024, année de sécheresse), lentille entre 1 et 45 q/ha.
    assert u[u.culture == "ble"].rendement_qha.between(10, 130).all()
    assert u[u.culture == "lentille"].rendement_qha.between(1, 45).all()


def test_status_3_excluded(panel):
    assert not panel[panel.utilisable].statut.isin(["3", "NC"]).any()


def test_auto_selection_picks_a_known_model():
    df, _ = load()
    L = df[(df.culture == "lentille") & (df.annee < 2022)]
    m = Calibrated("auto").fit(L)
    assert m.kind in MODELS
    assert set(m.selection) == set(MODELS)


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
    mL = Calibrated("auto").fit(L)
    mW = Calibrated("auto").fit(W)
    pool = pool_for(meteo, "77", range(2010, 2026), 2026)
    return pool, mL, mW, float(mL.levels.mean()), float(mW.levels["77"])


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
    for name in ("parcels", "thresholds", "supply_curve", "replay", "backtest", "meta", "contours", "france"):
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


def test_export_scenario_has_one_campaign_no_unconfirmed_aid_and_price_identity():
    meta = json.loads((APP_DATA / "meta.json").read_text())
    thresholds = json.loads((APP_DATA / "thresholds.json").read_text())
    parcels = json.loads((APP_DATA / "parcels.json").read_text())
    assert meta["duree_campagnes"] == 1
    assert meta["hypotheses"]["aide_couplee_eur_ha"]["valeur"] == 0
    assert thresholds["sensibilite"]["avec_aide"] < thresholds["sensibilite"]["sans_aide"]
    prices = {d["dep"]: d["p_star"] for d in thresholds["par_departement"]}
    kappa = meta["hypotheses"]["cout_transport_eur_t_km"]["valeur"]
    for p in parcels:
        assert p[5] == pytest.approx(prices[p[1]] + kappa * p[4], abs=1)
    assert meta["strategies_77"]["auto"] == prices["77"]
    for audit in (meta["audit_modele_lentille"], meta["audit_modele_ble"]):
        assert max(audit["proper_years"]) < min(audit["selection_years"])
        assert max(audit["selection_years"]) < min(audit["calibration_years"])
        assert max(audit["calibration_years"]) < meta["campagne"]
        assert audit["refit_after_calibration"] is False


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
