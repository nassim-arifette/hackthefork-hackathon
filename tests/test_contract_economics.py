"""Invariants économiques communs : marge blé, tri et calibrage minimal à 80 %."""

import json
import math

import numpy as np
import pytest
import yaml

from common import APP_DATA, DATA, VOISINS_LENTILLE, hypotheses
from contract_economics import (
    accepted_yield, calibrate_coefficient, contract_basis, crop_hypotheses,
    evaluate, expected_unit_cost, required_coefficient, signed_required_income,
    tier_bounds,
)
from contrats import calibres
from model import (Calibrated, calibrer_premier_palier, hyp_values, levels,
                   levels_lookup, load, p_star, pool_for, protection,
                   simulate_years, with_rel)


def test_crop_hypotheses_reuse_the_labelled_source_parameters():
    lentil = crop_hypotheses("lentille")
    base = hyp_values(hypotheses())
    assert lentil == base | {"charges_culture": base["charges_lentille"]}
    crops = yaml.safe_load((DATA / "cultures.yaml").read_text(encoding="utf-8"))
    for culture, source in crops.items():
        h = crop_hypotheses(culture)
        assert h["charges_culture"] == h["charges_lentille"] == source["charges_eur_ha"]["valeur"]
        assert h["aide"] == source["aide_eur_ha"]["valeur"]
        assert h["rotation"] == source["rotation_eur_ha"]["valeur"]
        assert h["qualite"] == source["part_refusee"]["valeur"]
        assert h["bonus"] == h["aide"] + h["rotation"]
        assert h["charges_ble"] == base["charges_ble"]
    with pytest.raises(ValueError, match="Culture inconnue"):
        crop_hypotheses("inconnue")


def test_quality_loss_reduces_only_accepted_tonnes_and_payment():
    raw = np.array([0.0, 1.0, 2.0])
    accepted = accepted_yield(raw, 0.2)
    np.testing.assert_allclose(accepted, [0, 0.8, 1.6])
    result = evaluate(1000, contract_basis("fixed", accepted), [0, 800, 1600], accepted)
    np.testing.assert_allclose(result["paid_eur_ha"], [0, 800, 1600])
    assert result["held"].all()
    assert np.isnan(result["effective_price_eur_t"][0])
    np.testing.assert_allclose(result["effective_price_eur_t"][1:], 1000)


def test_signed_need_matches_wheat_margin_including_aid_and_rotation():
    need = signed_required_income(200, [1, 5, 8], 700, 400, aid=105, rotation=150)
    np.testing.assert_allclose(need, [-355, 445, 1045])
    accepted = accepted_yield([1.5, 2.0, 2.5], 0.1)
    coefficient = calibrate_coefficient(need, accepted)
    result = evaluate(coefficient, accepted, need, accepted)
    crop_margin = result["paid_eur_ha"] - 400 + 105 + 150
    wheat_margin = 200 * np.array([1, 5, 8]) - 700
    np.testing.assert_array_equal(result["held"], crop_margin >= wheat_margin)


def test_negative_targets_remain_in_the_quantile_and_zero_price_is_allowed():
    need = np.array([-5.0, -4.0, -3.0, -2.0, 100.0])
    basis = np.ones(5)
    np.testing.assert_array_equal(required_coefficient(need, basis), need)
    assert calibrate_coefficient(need, basis) == 0
    assert p_star(need, 0.8) == 0
    outcome = evaluate(0, basis, need, basis)
    np.testing.assert_array_equal(outcome["held"], [True, True, True, True, False])
    np.testing.assert_allclose(outcome["shortfall_eur_ha"], [0, 0, 0, 0, 100])


@pytest.mark.parametrize("shape", ["fixed", "indexed", "tiers"])
def test_each_contract_quantile_is_minimal_and_counts_equalities(shape):
    accepted = np.array([0.5, 1, 2, 3, 4])
    basis = contract_basis(shape, accepted, p_w=[180, 190, 200, 210, 220], past_mean_accepted=2)
    thresholds = np.array([-1, 2, 3, 3, 10])
    need = thresholds * basis
    coefficient = calibrate_coefficient(need, basis)
    assert coefficient == pytest.approx(3)
    result = evaluate(coefficient, basis, need, accepted)
    assert result["held"].mean() == 0.8
    assert evaluate(np.nextafter(coefficient, -np.inf), basis, need, accepted)["held"].mean() < 0.8


def test_indexed_contract_fixes_a_multiplier_not_a_price_per_tonne():
    accepted = np.array([1.0, 3.0])
    basis = contract_basis("indexed", accepted, p_w=[100, 300])
    result = evaluate(2, basis, [0, 0], accepted)
    np.testing.assert_allclose(result["paid_eur_ha"], [200, 1800])
    np.testing.assert_allclose(result["effective_price_eur_t"], [200, 600])
    doubled_basis = contract_basis("indexed", accepted, p_w=[200, 600])
    np.testing.assert_allclose(evaluate(2, doubled_basis, [0, 0], accepted)["paid_eur_ha"],
                               2 * result["paid_eur_ha"])


def test_tier_boundaries_and_marginal_slopes_are_prespecified():
    b1, b2 = tier_bounds(2)
    assert (b1, b2) == pytest.approx((1.4, 2.8))
    accepted = np.array([0, b1, b2, b2 + 1])
    np.testing.assert_allclose(contract_basis("tiers", accepted, past_mean_accepted=2),
                               [0, b1, b1 + 0.7 * b1, b1 + 0.7 * b1 + 0.4])
    # Un rendement courant extrême ne redéfinit pas les deux premières tranches.
    changed = np.r_[accepted, 1000]
    np.testing.assert_allclose(contract_basis("tiers", changed, past_mean_accepted=2)[:-1],
                               contract_basis("tiers", accepted, past_mean_accepted=2))
    b1_zero, b2_zero = tier_bounds(0)
    assert 0 < b1_zero < b2_zero


def test_expected_unit_cost_is_ratio_of_means_not_mean_of_prices():
    accepted = np.array([1.0, 3.0])
    basis = contract_basis("indexed", accepted, p_w=[100, 300])
    assert expected_unit_cost(1, basis, accepted) == 250
    assert np.mean(evaluate(1, basis, [0, 0], accepted)["effective_price_eur_t"]) == 200
    assert np.isnan(expected_unit_cost(0, [0, 0], [0, 0]))


def test_zero_basis_is_treated_by_economic_feasibility():
    need = [-2, 0, 1, 2, 3]
    basis = [0, 0, 1, 1, 0]
    np.testing.assert_array_equal(required_coefficient(need, basis), [-np.inf, -np.inf, 1, 2, np.inf])
    coefficient = calibrate_coefficient(need, basis)
    assert coefficient == 2
    assert evaluate(coefficient, basis, need, basis)["held"].mean() == 0.8
    with pytest.raises(ValueError, match="Couverture impossible"):
        calibrate_coefficient(need, basis, coverage=1)
    assert calibrate_coefficient([-1, 0], [0, 0]) == 0


def test_equality_survives_one_ulp_payment_roundoff():
    need, basis = 818.3982727383226, 0.7496312783213095
    coefficient = need / basis
    assert coefficient * basis < need
    result = evaluate(coefficient, basis, need, basis)
    assert result["held"]
    assert result["shortfall_eur_ha"] == 0
    assert not evaluate(coefficient - 1e-6, basis, need, basis)["held"]


@pytest.mark.parametrize("q", [-0.1, 1.1, np.nan])
def test_invalid_quality_is_rejected(q):
    with pytest.raises(ValueError):
        accepted_yield([1], q)


def test_missing_historical_tier_mean_cannot_fall_back_to_current_yields():
    with pytest.raises(ValueError, match="moyen passé"):
        contract_basis("tiers", [1, 2, 3])


@pytest.mark.parametrize("threshold,expected", [(-10, 0), (0, 0), (1200, 1200),
                                                (1200.0001, 1201), (25000.25, 25001)])
def test_first_tier_is_the_minimal_nonnegative_integer_without_a_price_cap(threshold, expected):
    h = {"qualite": 0.2, "charges_ble": 0, "charges_lentille": 0, "bonus": 0}
    y_l, y_w, p_w = np.array([1.25]), np.array([1.0]), np.array([threshold])
    price = calibrer_premier_palier((700, 400), y_l, y_w, p_w, h, 0.8)
    assert price == expected
    assert protection({"paliers": (price, 700, 400)}, y_l, y_w, p_w, h) >= 0.8
    if price:
        assert protection({"paliers": (price - 1, 700, 400)}, y_l, y_w, p_w, h) < 0.8


def test_first_tier_credits_later_tranches_and_supports_custom_bounds():
    h = {"qualite": 0, "charges_ble": 700, "charges_lentille": 500, "bonus": 255}
    # At y=4 and bounds=(1.5, 3), later tiers pay 1.5*700 + 1*400 = 1450 €/ha.
    y_l, y_w, p_w = np.array([4.0]), np.array([10.0]), np.array([300.0])
    price = calibrer_premier_palier((700, 400), y_l, y_w, p_w, h, 0.8, bornes=(1.5, 3))
    assert price == 730  # (3000 - 700 + 500 - 255 - 1450) / 1.5
    assert protection({"paliers": (price, 700, 400), "bornes": (1.5, 3)}, y_l, y_w, p_w, h) == 1
    assert protection({"paliers": (price - 1, 700, 400), "bornes": (1.5, 3)}, y_l, y_w, p_w, h) == 0


def test_first_tier_reports_impossible_coverage_at_zero_accepted_yield():
    h = {"qualite": 1, "charges_ble": 0, "charges_lentille": 0, "bonus": 0}
    with pytest.raises(ValueError, match="Couverture impossible"):
        calibrer_premier_palier((700, 400), np.array([1]), np.array([1]), np.array([200]), h, 0.8)


def test_exported_guaranteed_integer_price_rounds_up_and_keeps_eighty_percent():
    thresholds = np.arange(10000) * 0.01 + 1487.258
    y_l = y_w = np.ones_like(thresholds)
    h = {"qualite": 0, "charges_ble": 0, "charges_lentille": 0, "bonus": 0, "tau": 0.8}
    exact = p_star(thresholds, 0.8)
    assert exact == pytest.approx(1567.248)
    assert protection({"prix": round(exact)}, y_l, y_w, thresholds, h) < 0.8
    contract = calibres(y_l, y_w, thresholds, h, exact)[0]
    assert contract["prix"] == 1568
    assert protection(contract, y_l, y_w, thresholds, h) >= 0.8


def test_real_seine_et_marne_exports_use_minimal_guaranteed_rounded_coefficients():
    """Rejoue les 20 000 scénarios publics, mêmes modèles et graine que 05/07/09."""
    h = hyp_values(hypotheses())
    df, meteo = load()
    lentil, wheat = df[df.culture == "lentille"], df[df.culture == "ble"]
    m_l = Calibrated("M1").fit(with_rel(lentil, levels(lentil)))
    m_w = Calibrated("M1").fit(with_rel(wheat, levels(wheat)))
    lev_l, lev_w = levels_lookup("lentille"), levels_lookup("ble")
    neighbours = [d for d in VOISINS_LENTILLE if d in lev_l.index]
    y_l, y_w, p_w = simulate_years(pool_for(meteo, "77", range(2010, 2026), 2026),
                                  m_l, m_w, float(lev_l[neighbours].mean()), lev_w["77"],
                                  h, n=20000, seed=77)
    accepted = accepted_yield(y_l, h["qualite"])
    need = signed_required_income(p_w, y_w, h["charges_ble"], h["charges_lentille"],
                                  h["aide"], h["rotation"])
    price = math.ceil(calibrate_coefficient(need, accepted, h["tau"]))
    assert evaluate(price, accepted, need, accepted)["held"].mean() >= h["tau"]
    assert evaluate(price - 1, accepted, need, accepted)["held"].mean() < h["tau"]
    thresholds = json.loads((APP_DATA / "thresholds.json").read_text())
    assert next(d["p_star"] for d in thresholds["par_departement"] if d["dep"] == "77") == price
    contracts = json.loads((APP_DATA / "contrats.json").read_text())
    assert next(c["prix"] for c in contracts["calibres"] if c["id"] == "unique") == price
    crops = json.loads((APP_DATA / "cultures.json").read_text())
    lentil_export = next(c for c in crops["cultures"] if c["id"] == "lentille")
    assert lentil_export["p_star"]["77"] == price
    indexed_basis = contract_basis("indexed", accepted, p_w=p_w)
    multiplier = math.ceil(100 * calibrate_coefficient(need, indexed_basis, h["tau"])) / 100
    assert evaluate(multiplier, indexed_basis, need, accepted)["held"].mean() >= h["tau"]
    assert evaluate(multiplier - 0.01, indexed_basis, need, accepted)["held"].mean() < h["tau"]
    meta = json.loads((APP_DATA / "meta.json").read_text())
    assert meta["contrat_indexe"]["m_star"] == lentil_export["indexe_m_star"] == multiplier
