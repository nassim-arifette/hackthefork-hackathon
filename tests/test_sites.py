"""Meaningful invariants of the shared site/procurement accounting convention."""
import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location("benchmark_sites", Path(__file__).parents[1] / "pipeline" / "benchmark_sites.py")
sites = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = sites
SPEC.loader.exec_module(sites)


def small_parcels():
    return sites.Parcels(["a", "b", "c"], np.array(["77", "77", "78"]),
                         np.array([10., 20., 30.]), np.array([9., 18., 27.]),
                         np.array([2.95, 2.96, 3.]), np.array([48.55, 48.55, 48.57]),
                         np.array([1500., 1500., 1400.]))


def test_gross_costs_converted_to_net_and_no_delivered_double_count():
    parcels = small_parcels()
    p = sites.Parameters(8, mode="collection", delivered_price=1600, transport_gross_t_km=0)
    r = sites.evaluate(parcels, (2.95, 48.55), p)
    assert r["expected_net_t"] == 9
    assert r["collection_eur_net_t"] == pytest.approx(5 / .9)
    assert r["sorting_eur_net_t"] == 200
    assert r["landed_eur_net_t"] == 1800
    assert r["budget_eur"] == 16200
    assert r["farm_eur_net_t"] == pytest.approx(1600 - 5 / .9)


def test_whole_parcels_surplus_budget_and_selection_are_consistent():
    parcels = small_parcels()
    r = sites.evaluate(parcels, (2.95, 48.55), sites.Parameters(30))
    assert r["selected_ids"] == ["c", "a"]
    assert r["expected_net_t"] == 36
    assert r["surplus_t"] == 6
    assert r["area_ha"] == 40
    assert r["budget_eur"] == pytest.approx(r["landed_eur_net_t"] * 36)


@pytest.mark.parametrize("mode", ["collection", "landed"])
def test_search_keeps_current_site_as_candidate(mode):
    parcels = small_parcels()
    p = sites.Parameters(30, mode=mode)
    current = (2.95, 48.55)
    baseline = sites.evaluate(parcels, current, p)
    best = sites.optimize(parcels, current, p)
    assert best["reached"]
    assert best["objective_eur_net_t"] <= baseline["objective_eur_net_t"] + 1e-9
    same = sites.evaluate(parcels, (best["longitude"], best["latitude"]), p)
    assert best["selected_ids"] == same["selected_ids"]
    assert best["objective_eur_net_t"] == same["objective_eur_net_t"]


def test_infeasible_volume_has_no_finite_objective():
    parcels = small_parcels()
    for p in (sites.Parameters(1000), sites.Parameters(30, mode="collection", delivered_price=1)):
        r = sites.optimize(parcels, (2.95, 48.55), p)
        assert r["status"] == "insufficient_expected_volume"
        assert not r["reached"]
        assert r["objective_eur_net_t"] is None


def test_rejected_quality_reduces_volume_once():
    parcels = small_parcels()
    r = sites.evaluate(parcels, (2.95, 48.55), sites.Parameters(1000, loss=.2))
    assert r["expected_net_t"] == pytest.approx(54 * .8 / .9)
    assert r["sorting_eur_net_t"] == pytest.approx(180 / .8)


@pytest.mark.parametrize("price", [1500, 1600])
@pytest.mark.parametrize("target", [300, 5000])
def test_real_export_counterexamples_and_corrected_search(target, price):
    parcels, config, _ = sites.load_parcels()
    p = sites.Parameters(target, mode="collection", delivered_price=price,
                         loss=config["loss"], fixed_gross_t=config["fixed_gross_t"],
                         transport_gross_t_km=config["transport_gross_t_km"],
                         sorting_gross_t=config["sorting_gross_t"], detour=config["detour"])
    current = config["site"]
    old_base = sites.evaluate(parcels, current, p, legacy=True)
    old_best = sites.evaluate(parcels, sites.LEGACY_SITES[target], p, legacy=True)
    assert old_base["reached"] and old_best["reached"]
    if price == 1500:
        assert old_best["mean_route_km"] > old_base["mean_route_km"]
    else:
        assert old_best["mean_route_km"] < old_base["mean_route_km"]
    baseline = sites.evaluate(parcels, current, p)
    best = sites.optimize(parcels, current, p)
    assert best["reached"]
    assert best["objective_eur_net_t"] <= baseline["objective_eur_net_t"] + 1e-9
    selected = sites.evaluate(parcels, (best["longitude"], best["latitude"]), p)
    assert selected["selected_ids"] == best["selected_ids"]
