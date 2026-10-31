"""Tests des décisions réellement exécutées, pas d'un filtre temporel reconstruit."""
import importlib

import numpy as np
import pandas as pd
import pytest

from common import hypotheses
from model import MODELS, WEATHER, hyp_values, load

backtest = importlib.import_module("03_backtest")


@pytest.fixture(scope="module")
def evaluated_year():
    df, meteo = load()
    h = hyp_values(hypotheses())
    annual, detail = backtest.evaluate_year(df, meteo, h, 2020, n_scenarios=600)
    return df, meteo, h, annual, detail


def test_actual_decisions_are_invariant_to_current_and_future_data(evaluated_year):
    """Muter rendements, surfaces, groupes, météo et prix futurs ne change aucun prix.

    L'année de décision elle-même est mutée : ses observations peuvent changer le
    verdict, mais pas le prix qui aurait été fixé avant de les connaître.
    """
    df, meteo, h, annual, detail = evaluated_year
    changed, weather = df.copy(deep=True), meteo.copy(deep=True)
    mask = changed.annee >= 2020
    changed.loc[mask, "rendement_qha"] *= 7
    changed.loc[mask, "surface_ha"] *= (1 + changed.loc[mask, "dep"].astype(int)) * 1000
    changed.loc[mask, WEATHER] = changed.loc[mask, WEATHER] * 20 + 500
    changed.loc[mask, "prix_ble"] += 1000
    # Ces marqueurs historiques ont été calculés sur toute la période ; le modèle
    # doit les ignorer même si des observations anciennes portent ces étiquettes.
    changed["serie_groupe"] = "999"
    changed["doublon"] = True
    weather.loc[weather.annee >= 2020, WEATHER] *= 30
    weather.loc[weather.annee >= 2020, "prix_ble"] += 1000
    annual_changed, detail_changed = backtest.evaluate_year(changed, weather, h, 2020, n_scenarios=600)
    assert annual["audit"] == annual_changed["audit"]
    assert annual["audit_ble"] == annual_changed["audit_ble"]
    assert [r["dep"] for r in detail] == [r["dep"] for r in detail_changed]
    for original, altered in zip(detail, detail_changed):
        for method in original["methodes"]:
            assert original["methodes"][method]["prix_eur_t"] == altered["methodes"][method]["prix_eur_t"]
        assert [r["prix_eur_t"] for r in original["frontiere"]] == [r["prix_eur_t"] for r in altered["frontiere"]]
    # Mutation effective, y compris sur ce que le verdict est autorisé à voir.
    assert detail[0]["marge_ble"] != detail_changed[0]["marge_ble"]
    assert detail[0]["rendement_lentille_reel"] != detail_changed[0]["rendement_lentille_reel"]


def test_historical_reference_pairs_crop_yields_and_price_by_year():
    panel = pd.DataFrame([
        {"dep": "10", "annee": 2010, "culture": "lentille", "rendement_qha": 10, "prix_ble": 200},
        {"dep": "10", "annee": 2011, "culture": "lentille", "rendement_qha": 20, "prix_ble": 100},
        {"dep": "10", "annee": 2011, "culture": "ble", "rendement_qha": 40, "prix_ble": 100},
        {"dep": "10", "annee": 2010, "culture": "ble", "rendement_qha": 50, "prix_ble": 200},
    ])
    h = {"prix_ble": None, "charges_ble": 300, "charges_lentille": 400, "bonus": 0}
    prices = backtest.historical_break_even(panel, "10", h)
    np.testing.assert_allclose(prices, [1100, 250])
    assert np.quantile(prices, 0.8) == pytest.approx(930)


def test_all_methods_compare_price_shortfall_and_purchase_on_same_cases(evaluated_year):
    _, _, h, _, details = evaluated_year
    expected = {*MODELS, "auto", "historique", "moyenne"}
    for r in details:
        assert set(r["methodes"]) == expected
        for result in r["methodes"].values():
            purchase = result["prix_eur_t"] * r["rendement_lentille_reel"] / 10
            assert result["cout_achat_eur_ha"] == pytest.approx(purchase, abs=0.03)
            shortfall = max(0, r["marge_ble"] - result["marge_lentille_eur_ha"])
            assert result["manque_eur_ha"] == pytest.approx(shortfall, abs=0.02)
        for method in expected - {"moyenne"}:
            curve = [point for point in r["frontiere"] if point["methode"] == method]
            assert [point["tau"] for point in curve] == sorted(set(backtest.TAU_GRID) | {h["tau"]})
            prices = [point["prix_eur_t"] for point in curve]
            assert prices == sorted(prices)
            assert [point["manque_eur_ha"] for point in curve] == sorted([point["manque_eur_ha"] for point in curve], reverse=True)


def test_uncertainty_resamples_whole_years_not_individual_departments():
    records = []
    for year, success in ((2019, False), (2020, True)):
        for _ in range(100):
            records.append({"annee": year, "tenu": success, "prix_eur_t": 1000,
                            "manque_eur_ha": 0 if success else 200, "cout_achat_eur_ha": 1500})
    result = backtest.summarise_economics(records)
    assert result["taux_tenus"] == 0.5
    assert result["taux_tenus_ic95_bootstrap_annees"] == [0.0, 1.0]
    assert result["manque_moyen_eur_ha"] == 100
    assert result["manque_moyen_si_echec_eur_ha"] == 200
