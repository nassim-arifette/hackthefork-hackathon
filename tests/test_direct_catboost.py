"""Guard past-only selection and year-equal loss, independently of CatBoost."""
import pandas as pd
import pytest

from benchmark_direct_catboost import choose_past


def records(year, model, losses):
    return [{"year": year, "dep": str(i), "model": model, "contract_loss": loss}
            for i, loss in enumerate(losses)]


def test_selection_ignores_current_and_future_outcomes():
    history = records(2018, "a", [1, 2]) + records(2018, "b", [3, 4])
    poisoned = history + records(2019, "a", [1e20]) + records(2019, "b", [0])
    poisoned += records(2025, "a", [1e20]) + records(2025, "b", [0])
    expected = choose_past(pd.DataFrame(history), 2019, ["a", "b"])
    assert choose_past(pd.DataFrame(poisoned), 2019, ["a", "b"]) == expected
    assert expected[0] == "a"
    assert expected[1]["validation_years"] == [2018]


def test_selection_weights_years_equally_and_excludes_old_years():
    rows = records(2016, "a", [10]) + records(2016, "b", [0])
    rows += records(2018, "a", [0] * 20) + records(2018, "b", [2] * 20)
    rows += records(2015, "a", [0]) + records(2015, "b", [1e20])
    choice, info = choose_past(pd.DataFrame(rows), 2019, ["a", "b"])
    assert choice == "b"
    assert info["scores"] == {"a": 5., "b": 1.}


def test_selection_rejects_unequal_cohorts():
    rows = records(2018, "a", [1, 2]) + records(2018, "b", [3])
    with pytest.raises(ValueError, match="inconsistent OOF cohorts"):
        choose_past(pd.DataFrame(rows), 2019, ["a", "b"])
