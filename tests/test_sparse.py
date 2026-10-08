"""Analytic partial-penalty oracle and independently bounded simulation accounting."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

from causal_ml_lab.core import ols
from causal_ml_lab.sparse import dgp, plugin, run


def test_unpenalized_plugin_matches_joint_ols():
    y, d, x = dgp(31, n=250, p=20)
    estimate, _ = plugin(y, d, x, alpha=0)
    oracle, _ = ols(y, d, x)
    assert abs(estimate - oracle) < 1e-5
    assert np.corrcoef(d, x[:, :5].sum(axis=1))[0, 1] > 0.9


def test_simulation_resumes_and_preserves_original(tmp_path):
    source = Path(__file__).parents[1]
    (tmp_path / "docs").mkdir()
    (tmp_path / "results").mkdir()
    for name in ["DGP2_PREDECLARATION.md", "DGP1_PLUGIN_ADDENDUM.md"]:
        (tmp_path / "docs" / name).write_bytes((source / "docs" / name).read_bytes())
    original = (source / "versions/v2-2026-10-07/results/monte_carlo.csv").read_bytes()
    (tmp_path / "results/monte_carlo.csv").write_bytes(original)
    first = run(tmp_path, repetitions=3)
    table = pd.read_csv(tmp_path / "results/dml_two_dgps.csv")
    assert len(table) == 7 and table.query('dgp=="DGP2_sparse"').repetitions.eq(3).all()
    assert set(table.query('dgp=="DGP2_sparse"').method) == {"OLS", "NaivePlugin", "DML"}
    assert table.coverage.between(0, 1).all()
    assert (table.coverage_lo95 <= table.coverage).all()
    assert (table.coverage_hi95 >= table.coverage).all()
    assert (table.query("coverage==0").coverage_hi95 > 0).all()
    assert np.isfinite(table[["bias", "rmse", "mc_se"]]).all().all()
    second = run(tmp_path, repetitions=3)
    assert first["private_cache"] == second["private_cache"]
    pd.testing.assert_frame_equal(table, pd.read_csv(tmp_path / "results/dml_two_dgps.csv"))
    assert (tmp_path / "results/monte_carlo.csv").read_bytes() == original
    assert json.loads((tmp_path / "results/sparse_manifest.json").read_text())["p"] >= 100
