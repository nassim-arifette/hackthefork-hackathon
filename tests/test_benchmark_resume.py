"""A killed run must resume with identical predictions and calibration history."""
from argparse import Namespace
import json

import pandas as pd
import pytest

from benchmark_checkpoint import Checkpoints
import benchmark_models
import benchmark_contract


@pytest.mark.parametrize("stage", ["yield", "direct"])
def test_interrupted_run_matches_uninterrupted_run(tmp_path, monkeypatch, stage):
    if stage == "yield":
        args = Namespace(output=tmp_path / "resumed", models=["trend", "linear"],
                         years=[2019], seed=42, samples=128, device="cpu", calibration="rolling")
        run = benchmark_models.run
        stop_key = "2019-trend"
    else:
        args = Namespace(output=tmp_path / "resumed", models=["pooled"], device="cpu", reference=None)
        run = benchmark_contract.run
        stop_key = "2018-pooled"
    save = Checkpoints.save
    def crash_after_save(self, key, payload):
        save(self, key, payload)
        if key == stop_key:
            raise InterruptedError("simulated runtime loss")
    monkeypatch.setattr(Checkpoints, "save", crash_after_save)
    with pytest.raises(InterruptedError):
        run(args)
    def ensure_no_repeat(self, key, payload):
        assert key != stop_key, "Completed model/year was recomputed"
        save(self, key, payload)
    monkeypatch.setattr(Checkpoints, "save", ensure_no_repeat)
    run(args)
    resumed = pd.read_csv(args.output / "predictions.csv")
    resumed_audit = json.loads((args.output / "results.json").read_text())["audit"]
    monkeypatch.setattr(Checkpoints, "save", save)
    args.output = tmp_path / "fresh"
    run(args)
    pd.testing.assert_frame_equal(resumed, pd.read_csv(args.output / "predictions.csv"))
    assert resumed_audit == json.loads((args.output / "results.json").read_text())["audit"]
    # A fully completed run must not refit any models.
    def unexpected_fit(*args, **kwargs):
        raise AssertionError("Already completed fit executed")
    monkeypatch.setattr(benchmark_models.RollingCalibrated, "fit", unexpected_fit)
    monkeypatch.setattr(benchmark_contract.DirectPrice, "fit", unexpected_fit)
    run(args)
    pd.testing.assert_frame_equal(resumed, pd.read_csv(args.output / "predictions.csv"))


def test_changed_configuration_cannot_reuse_checkpoints(tmp_path):
    args = Namespace(output=tmp_path, models=["trend"], seed=42)
    checkpoint = Checkpoints(args, "test", ["2019-trend"])
    checkpoint.save("2019-trend", {"rows": []})
    args.seed = 43
    with pytest.raises(ValueError, match="changed"):
        Checkpoints(args, "test", ["2019-trend"])
