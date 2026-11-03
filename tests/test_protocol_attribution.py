import numpy as np

from benchmark_protocol_attribution import expand_quantiles, legacy_adjustment, simulate_arrays


def test_expansion_changes_endpoints_without_mutating_raw_distribution():
    original = np.array([[.3, 1., 1.6], [.1, .5, .8]])
    expanded = expand_quantiles(original, .2)
    np.testing.assert_allclose(expanded, [[.1, 1., 1.8], [.02, .5, 1.]])
    np.testing.assert_allclose(original, [[.3, 1., 1.6], [.1, .5, .8]])


def test_legacy_signed_adjustment_can_contract_an_overwide_interval():
    assert legacy_adjustment(np.full(20, -.2)) == -.2
    assert legacy_adjustment(np.arange(10.)) == 8.


def test_constant_distributions_recover_break_even_and_equality():
    h = {'charges_ble': 440, 'charges_lentille': 280, 'bonus': 122, 'tau': .8}
    qL, qW = np.ones((2, 3)), np.ones((2, 3))
    p = simulate_arrays(qL, qW, np.array([200., 200.]), 15., 70., h, 2020, 200)
    expected = (200*7-440+280-122)/1.5
    assert p == expected
    assert p*1.5-280+122 >= 200*7-440
