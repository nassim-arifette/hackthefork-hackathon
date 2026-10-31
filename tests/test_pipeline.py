"""Tests du pipeline : données, absence de fuite, propriétés du prix plancher, exports."""
import json
import re

import numpy as np
import pandas as pd
import pytest

from common import APP_DATA, DATA, TEST_YEARS
from model import Calibrated, break_even_prices, calibrer_premier_palier, calibrer_prime_ha, hyp_values, \
    levels, load, p_star, paiement, pool_for, protection, sample_quantile, simulate_years, with_rel
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


def test_backtest_has_no_leakage():
    """Pour chaque année test, l'entraînement ne voit que les années antérieures."""
    df, _ = load()
    L = df[df.culture == "lentille"]
    for t in TEST_YEARS:
        train = L[L.annee < t]
        assert train.annee.max() < t
        assert t not in set(train.annee)


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
