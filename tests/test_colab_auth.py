"""Classify auth failures without training, accepting terms, or exposing tokens."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys
from unittest.mock import Mock

import pytest

spec = importlib.util.spec_from_file_location("colab_runner", Path(__file__).resolve().parents[1] / "scripts/colab_benchmark.py")
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


@pytest.mark.parametrize("token,valid,accepted,expected", [
    (" ", True, True, "Clé absente"),
    ("private-test-value", False, True, "Clé refusée"),
    ("private-test-value", None, True, "vérification Prior Labs inaccessible"),
    ("private-test-value", True, False, "licence TabPFN 3.5 non acceptée"),
    ("private-test-value", True, None, "licence Prior Labs inaccessible"),
    ("private-test-value", True, True, None),
])
def test_preflight_classifies_failure_without_exposing_key(monkeypatch, capsys, token, valid, accepted, expected):
    auth = SimpleNamespace(settings=SimpleNamespace(tabpfn=SimpleNamespace(auth_api_url="https://example.invalid")),
        verify_token=Mock(return_value=valid), _get_license_name=Mock(return_value="model-specific-license"),
        check_license_accepted=Mock(return_value=accepted))
    monkeypatch.setitem(sys.modules, "tabpfn", SimpleNamespace(browser_auth=auth))
    monkeypatch.setenv("TABPFN_TOKEN", token)
    if expected:
        with pytest.raises(RuntimeError, match=expected) as error:
            runner.check_tabpfn_access()
        assert "private-test-value" not in str(error.value)
    else:
        runner.check_tabpfn_access()
        auth.check_license_accepted.assert_called_once_with(token, "https://example.invalid", "model-specific-license")
    if not token.strip() or valid is not True:
        auth.check_license_accepted.assert_not_called()
    assert "private-test-value" not in capsys.readouterr().out
