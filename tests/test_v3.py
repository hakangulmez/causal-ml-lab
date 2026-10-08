"""V3 diagnostic/accounting checks with synthetic data; no published experiment runs."""

import json

import numpy as np
import pandas as pd
import pytest

from causal_ml_lab import v3_diagnostics as dg
from causal_ml_lab import v3_mc as mc


class Classifier:
    def predict_proba(self, x):
        p = np.where(x[:, 0] % 3 == 0, 0.001, np.where(x[:, 0] % 3 == 1, 0.5, 0.999))
        return np.column_stack([1 - p, p])


class FakeIRM:
    def __init__(self, data, **kwargs):
        self.data = data
        self.coef = np.array([10.0])
        self.se = np.array([2.0])

    def set_sample_splitting(self, folds):
        self.folds = folds

    def fit(self, **kwargs):
        classifier = Classifier()
        self.models = {"ml_m": {"e401": [[classifier] * 5]}}
        raw = classifier.predict_proba(self.data[dg.COVARIATES].to_numpy())[:, 1]
        self.predictions = {"ml_m": np.clip(raw, 0.01, 0.99).reshape(-1, 1, 1)}

    def sensitivity_analysis(self, cf_y, cf_d, **kwargs):
        bound = np.sqrt(cf_y * cf_d / (1 - cf_d))
        self.sensitivity_params = {
            "theta": {"lower": [10 - bound], "upper": [10 + bound]},
            "ci": {"lower": [8 - bound], "upper": [12 + bound]},
            "rv": [0.08],
            "rva": [0.05],
        }


def test_raw_overlap_clips_without_trimming_and_defines_ess():
    raw = np.array([0.0, 0.5, 1.0, 0.01, 0.5, 0.99])
    d = np.array([0, 0, 0, 1, 1, 1])
    result = dg.overlap(raw, d)
    assert sum(r["observations_removed"] for r in result) == 0
    assert result[0]["clipped_count"] == 2 and result[1]["clipped_count"] == 0
    expected = np.array([1 / 0.99, 2, 100.0])
    assert result[0]["ESS_clipped"] == pytest.approx(expected.sum() ** 2 / (expected @ expected))
    assert dg.effective_sample_size(np.ones(6)) == 6
    assert np.isnan(dg.effective_sample_size([np.inf, 1]))
    assert np.isnan(dg.effective_sample_size([0, 0]))


def test_diagnostics_exports_raw_probabilities_sensitivity_and_unchanged_target(
    tmp_path, monkeypatch
):
    for path in ["data/raw", "results", "figures", "docs", "versions/v2-2026-10-07/results"]:
        (tmp_path / path).mkdir(parents=True)
    data = pd.DataFrame({k: np.zeros(100) for k in dg.SIPP_DTYPES})
    data["age"] = np.arange(100)
    data["inc"] = np.arange(100) + 1
    data["e401"] = np.arange(100) % 2
    data.to_csv(tmp_path / "data/raw/sipp1991.csv", index=False)
    pd.DataFrame(
        [dict(model="IRM", learner=k, estimate=10, se=2) for k in ["Lasso", "RF", "GB"]]
    ).to_csv(tmp_path / "versions/v2-2026-10-07/results/pension.csv", index=False)
    (tmp_path / "results/income_group_ate.csv").write_text("unchanged aggregate\n")
    (tmp_path / "docs/V3_PROTOCOL.md").write_text("synthetic test protocol")
    monkeypatch.setattr(dg.dml, "DoubleMLData", lambda data, **kwargs: data)
    monkeypatch.setattr(dg.dml, "DoubleMLIRM", FakeIRM)
    monkeypatch.setattr(dg, "learners", lambda *args: (None, None))
    first = dg.run(tmp_path)
    second = dg.run(tmp_path)
    assert first["folds_sha256"] == second["folds_sha256"]
    assert first["removed"] == 0
    assert len(pd.read_csv(tmp_path / "results/v3_rf_irm_sensitivity.csv")) == 16
    assert (
        pd.read_csv(tmp_path / "results/v3_irm_refit_comparison.csv").estimate_difference == 0
    ).all()
    assert (tmp_path / "figures/v3_overlap.png").exists()
    assert len(pd.read_csv(tmp_path / "results/v3_income_quartile_cutoffs.csv")) == 4
    with pytest.raises(FileNotFoundError):
        dg.run(tmp_path / "missing")


def synthetic_repetition(kind, rep):
    names = ["OLS", "NaivePlugin", "DML"]
    return [
        dict(
            module="DML",
            rep=rep,
            method=m,
            estimate=1 + rep * 0.001,
            se=0.1,
            truth=1.0,
            covered=True,
            seed=20261008 + rep,
        )
        for m in names
    ]


class Async:
    def __init__(self, value):
        self.value = value

    def get(self, timeout):
        return self.value


class Pool:
    def apply_async(self, func, args):
        return Async(func(*args))

    def terminate(self):
        pass

    def join(self):
        pass


class Context:
    def Pool(self, n):
        return Pool()


def test_matched_checkpoint_counts_completion_and_failures(tmp_path, monkeypatch):
    for path in ["runs", "results", "docs", "versions/v2-2026-10-07/results"]:
        (tmp_path / path).mkdir(parents=True)
    (tmp_path / "docs/V3_PROTOCOL.md").write_text("synthetic protocol")
    (tmp_path / "versions/v2-2026-10-07/results/sparse_manifest.json").write_text(
        json.dumps({"private_cache": "runs/old.csv"})
    )
    pd.DataFrame(synthetic_repetition("sparse", 0) + synthetic_repetition("sparse", 1)).to_csv(
        tmp_path / "runs/old.csv", index=False
    )

    def rep(kind, j):
        if j == 2:
            raise ValueError("synthetic fit failure")
        return synthetic_repetition(kind, j)

    monkeypatch.setattr(mc, "repetition", rep)
    monkeypatch.setattr(mc.mp, "get_context", lambda name: Context())
    # Draw-generation mock is bookkeeping only, not a new research DGP.
    monkeypatch.setattr(mc, "dgp", lambda seed: (np.ones(4), np.ones(4), np.ones((4, 2))))
    out = mc.run_block(tmp_path, "sparse", budget=10, target=4)
    assert out["completed_repetitions"] == 3 and len(out["failures"]) == 1
    saved = pd.read_csv(tmp_path / "runs/v3_mc/sparse.csv")
    assert set(saved.rep) == {0, 1, 3}
    assert saved.groupby("rep").size().eq(3).all()
    stats = pd.read_csv(tmp_path / "results/v3_sparse_mc.csv")
    assert stats.repetitions.eq(3).all()
    assert stats.coverage_mc_se.eq(0).all() and stats.coverage_lo95.lt(1).all()


def test_coverage_mcse_wilson_endpoints_and_strings():
    frame = pd.DataFrame(
        [
            dict(module="DML", method="A", estimate=1.0, truth=1.0, covered="True"),
            dict(module="DML", method="A", estimate=1.0, truth=1.0, covered="False"),
        ]
    )
    row = mc.summary(frame).iloc[0]
    assert row.coverage == 0.5 and row.coverage_mc_se == pytest.approx(np.sqrt(0.5 * 0.5 / 2))
    frame["covered"] = False
    row = mc.summary(frame).iloc[0]
    assert row.coverage_mc_se == 0 and row.coverage_hi95 > 0


def test_unfinished_repetition_is_excluded_at_the_deadline(tmp_path, monkeypatch):
    for path in ["runs", "results", "docs", "versions/v2-2026-10-07/results"]:
        (tmp_path / path).mkdir(parents=True)
    (tmp_path / "docs/V3_PROTOCOL.md").write_text("synthetic protocol")
    (tmp_path / "versions/v2-2026-10-07/results/sparse_manifest.json").write_text(
        json.dumps({"private_cache": "runs/old.csv"})
    )
    pd.DataFrame(synthetic_repetition("sparse", 0) + synthetic_repetition("sparse", 1)).to_csv(
        tmp_path / "runs/old.csv", index=False
    )

    class DeadlineAsync:
        def get(self, timeout):
            raise mc.mp.TimeoutError()

    class DeadlinePool(Pool):
        def apply_async(self, func, args):
            return DeadlineAsync() if args[1] == 2 else super().apply_async(func, args)

    class DeadlineContext:
        def Pool(self, n):
            return DeadlinePool()

    monkeypatch.setattr(mc, "repetition", synthetic_repetition)
    monkeypatch.setattr(mc.mp, "get_context", lambda name: DeadlineContext())
    monkeypatch.setattr(mc, "dgp", lambda seed: (np.ones(4), np.ones(4), np.ones((4, 2))))
    out = mc.run_block(tmp_path, "sparse", budget=10, target=4)
    assert out["completed_repetitions"] == 2 and out["failures"][0]["rep"] == 2
    assert len(pd.read_csv(tmp_path / "runs/v3_mc/sparse.csv")) == 6
    # A consumed block does not receive a new budget on a later invocation.
    monkeypatch.setattr(mc, "repetition", lambda *args: pytest.fail("must not restart budget"))
    assert mc.run_block(tmp_path, "sparse", budget=10, target=4) == out
