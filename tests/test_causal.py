"""Analytic estimand checks and isolated synthetic end-to-end coverage."""

import importlib.util
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import GradientBoostingRegressor

from causal_ml_lab.core import (
    continuous_dgp,
    crossfit_plr,
    cs_simple,
    did_dgp,
    dml_dgp,
    ols,
    plr_score,
    twfe,
)
from causal_ml_lab.pipeline import forest, learners, mc, pension, run


def synthetic():
    path = Path(__file__).parents[1] / "scripts/research.py"
    spec = importlib.util.spec_from_file_location("exercise", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.synthetic(300)


def test_noiseless_twfe_cs_and_cluster_inference():
    panel, truth = did_dgp(12, 120)
    panel["y"] = 2 * panel["d"] + 0.3 * panel["time"] + panel["id"] / 100
    estimate, se = twfe(panel)
    assert estimate == pytest.approx(2) and se < 1e-10
    assert cs_simple(panel) == pytest.approx(2)
    blank = {k: v.copy() for k, v in panel.items()}
    blank["d"][:] = 0
    blank["g"][:] = 0
    with pytest.raises(ValueError):
        twfe(blank)
    with pytest.raises(ValueError):
        cs_simple(blank)
    original, truth = did_dgp(12, 1000)
    assert abs(cs_simple(original) - truth) < 0.08


def test_orthogonal_score_oracle_and_crossfitting():
    y, d, x = dml_dgp(17, n=3000)
    m = 0.5 * x[:, 0] ** 2 + np.sin(x[:, 1])
    g = m + x[:, 0] ** 2 + np.cos(x[:, 1]) + 0.5 * x[:, 3]
    point, se = plr_score(y, d, g, m)
    assert abs(point - 1) < 0.08 and 0 < se < 0.05
    assert plr_score(2 * d, d, np.zeros(len(y)), np.zeros(len(y)))[0] == pytest.approx(2)
    with pytest.raises(ValueError):
        plr_score(y, d, g, d)
    model = GradientBoostingRegressor(n_estimators=10, max_depth=2, random_state=1)
    for naive in [False, True]:
        p, s = crossfit_plr(y[:300], d[:300], x[:300], model, folds=3, naive=naive)
        assert np.isfinite(p) and s > 0
    linear = 3 * d + x[:, 0]
    assert ols(linear, d, x)[0] == pytest.approx(3)


def test_continuous_estimands_and_mc_tables(tmp_path):
    dose, effect, derivative = continuous_dgp(3)
    # For the quadratic dose response, ATT/dose = a+.5*d; derivative=a+d.
    assert np.allclose(derivative - effect / dose, 0.5 * dose)
    (tmp_path / "results").mkdir()
    mc(tmp_path, 2)
    table = pd.read_csv(tmp_path / "results/monte_carlo.csv")
    assert set(table.module) == {"DiD", "DML"} and table.repetitions.eq(2).all()
    assert (tmp_path / "results/continuous.csv").exists()


def test_pension_pipeline_and_private_cache(tmp_path):
    frame = synthetic()
    (tmp_path / "results").mkdir()
    (tmp_path / "runs").mkdir()
    pension(tmp_path, quick=True, frame=frame)
    table = pd.read_csv(tmp_path / "results/pension.csv")
    assert len(table) == 7 and set(table.model) == {"OLS", "PLR", "IRM"}
    assert table.estimate.between(500, 1500).all()
    # Full route uses an existing private CSV and binds caches to data/code.
    path = tmp_path / "data/raw/sipp1991.csv"
    frame.to_csv(path, index=False)
    pension(tmp_path, quick=False)
    pension(tmp_path, quick=False)
    assert len(list((tmp_path / "runs").glob("pension_*.json"))) >= 6
    frame.loc[0, "inc"] = np.nan
    with pytest.raises(ValueError):
        pension(tmp_path, quick=True, frame=frame)
    for name in ["Lasso", "RF", "GB"]:
        out, treat = learners(name, True)
        assert hasattr(out, "fit") and hasattr(treat, "predict_proba")


def test_full_synthetic_pipeline_forest_and_failure_accounting(tmp_path, monkeypatch):
    import causal_ml_lab.pipeline as pipeline

    original_mc = pipeline.mc
    monkeypatch.setattr(pipeline, "mc", lambda root, repetitions: original_mc(root, 2))
    monkeypatch.setattr(pipeline.subprocess, "run", lambda *args, **kwargs: None)
    monkeypatch.setattr(pipeline, "forest", lambda root, data: forest(root, data))
    result = run(tmp_path, synthetic=synthetic())
    assert result["paid_calls"] == 0 and result["failures"] == []
    assert len(pd.read_csv(tmp_path / "results/income_group_ate.csv")) == 4
    assert len(pd.read_csv(tmp_path / "results/forest_descriptive.csv")) == 4
    calibration = pd.read_csv(tmp_path / "results/forest_blp.csv").iloc[0]
    assert calibration.n == 150 and calibration.se > 0
    assert calibration.lo95 < calibration.estimate < calibration.hi95

    def fail(*args, **kwargs):
        raise RuntimeError("deliberate estimator failure")

    monkeypatch.setattr(pipeline, "forest", fail)
    second = run(tmp_path, quick=True, synthetic=synthetic())
    assert second["quick"]
    failed = run(tmp_path, synthetic=synthetic())
    assert failed["failures"][0]["component"] == "CausalForest"
    assert json.loads((tmp_path / "results/manifest.json").read_text())["seed"] == 20261007


def test_native_fetch_and_csv_resume_produce_same_estimates(tmp_path, monkeypatch):
    import causal_ml_lab.pipeline as pipeline

    frame = synthetic()
    for name in ["nifa", "tw", "p401"]:
        frame[name] = 0
    frame = frame.astype(pipeline.SIPP_DTYPES)
    monkeypatch.setattr(pipeline, "fetch_401K", lambda **kwargs: frame.copy())
    (tmp_path / "results").mkdir()
    fresh = pension(tmp_path, quick=True)
    first = pd.read_csv(tmp_path / "results/pension.csv")
    resumed = pension(tmp_path, quick=True)
    second = pd.read_csv(tmp_path / "results/pension.csv")
    pd.testing.assert_frame_equal(fresh, resumed)
    columns = ["estimate", "se", "lo95", "hi95"]
    np.testing.assert_allclose(first[columns], second[columns], rtol=1e-9, atol=1e-9)
