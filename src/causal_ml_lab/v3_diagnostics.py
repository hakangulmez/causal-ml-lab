# ruff: noqa: E501
"""Recover unchanged IRM fits for raw overlap and fixed sensitivity diagnostics."""

import hashlib
import json
import pickle
import time
import warnings
from pathlib import Path

import doubleml as dml
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.model_selection import StratifiedKFold

from causal_ml_lab.pipeline import COVARIATES, SEED, SIPP_DTYPES, learners


def effective_sample_size(weights):
    weights = np.asarray(weights, dtype=float)
    return (
        float(weights.sum() ** 2 / (weights @ weights))
        if np.isfinite(weights).all() and (weights @ weights) > 0
        else np.nan
    )


def overlap(raw, treatment, threshold=0.01):
    clipped = np.clip(raw, threshold, 1 - threshold)
    rows = []
    for arm in [0, 1]:
        mask = treatment == arm
        weights = 1 / clipped[mask] if arm else 1 / (1 - clipped[mask])
        with np.errstate(divide="ignore"):
            raw_weights = 1 / raw[mask] if arm else 1 / (1 - raw[mask])
        changed = raw[mask] != clipped[mask]
        rows.append(
            dict(
                arm=arm,
                n=int(mask.sum()),
                clipped_count=int(changed.sum()),
                clipped_share=float(changed.mean()),
                below_count=int((raw[mask] < threshold).sum()),
                above_count=int((raw[mask] > 1 - threshold).sum()),
                observations_removed=0,
                ESS_clipped=effective_sample_size(weights),
                ESS_raw=effective_sample_size(raw_weights),
                weight_definition="1/m_clip for treated; 1/(1-m_clip) for control, restricted to each arm",
                ESS_definition="(sum w)^2 / sum(w^2)",
                threshold=threshold,
            )
        )
    return rows


def run(root: Path):
    began = time.monotonic()
    deadline = began + 3600
    path = root / "data/raw/sipp1991.csv"
    if not path.exists():
        raise FileNotFoundError("Frozen SIPP required; acquisition disabled")
    data = pd.read_csv(path).astype(SIPP_DTYPES)
    np.random.seed(SEED)
    dd = dml.DoubleMLData(data, y_col="net_tfa", d_cols="e401", x_cols=COVARIATES)
    x = data[COVARIATES].to_numpy()
    treatment = data.e401.to_numpy()
    folds = list(StratifiedKFold(5, shuffle=True, random_state=SEED).split(x, treatment))
    split_hash = hashlib.sha256(
        b"".join(train.tobytes() + test.tobytes() for train, test in folds)
    ).hexdigest()
    private = root / "runs/v3_diagnostics"
    private.mkdir(parents=True, exist_ok=True)
    old = pd.read_csv(root / "versions/v2-2026-10-07/results/pension.csv")
    diagnostics: list[dict] = []
    refits = []
    sensitivity = []
    hist = {}
    warning_log: list[dict] = []
    for name in ["Lasso", "RF", "GB"]:
        if time.monotonic() >= deadline:
            raise TimeoutError("SIPP diagnostic budget exceeded")
        start = time.monotonic()
        cache = private / (name + ".pkl")
        if cache.exists():
            with cache.open("rb") as stream:
                model = pickle.load(stream)
        else:
            g, m = learners(name, False)
            model = dml.DoubleMLIRM(
                dd, ml_g=g, ml_m=m, n_folds=5, n_rep=1, score="ATE", trimming_threshold=0.01
            )
            model.set_sample_splitting(folds)
            with warnings.catch_warnings(record=True) as recorded:
                warnings.simplefilter("always")
                model.fit(n_jobs_cv=1, store_models=True)
            warning_log.extend(
                dict(learner=name, category=w.category.__name__, message=str(w.message))
                for w in recorded
            )
            with cache.open("wb") as stream:
                pickle.dump(model, stream)
        raw = np.empty(len(data))
        for fitted, (_, test) in zip(model.models["ml_m"]["e401"][0], folds, strict=True):
            raw[test] = fitted.predict_proba(x[test])[:, 1]
        np.testing.assert_allclose(
            np.clip(raw, 0.01, 0.99), model.predictions["ml_m"][:, 0, 0], rtol=0, atol=1e-12
        )
        np.savez_compressed(private / (name + "_raw_propensity.npz"), raw=raw, treatment=treatment)
        hist[name] = raw
        diagnostics.extend(dict(learner=name, **row) for row in overlap(raw, treatment))
        inherited = old[(old.model == "IRM") & (old.learner == name)].iloc[0]
        refits.append(
            dict(
                learner=name,
                estimate=float(model.coef[0]),
                se=float(model.se[0]),
                v2_estimate=float(inherited.estimate),
                estimate_difference=float(model.coef[0] - inherited.estimate),
                se_difference=float(model.se[0] - inherited.se),
                seconds=time.monotonic() - start,
                folds_sha256=split_hash,
                n=len(data),
            )
        )
        if name == "RF":
            for cf_y in [0.01, 0.03, 0.05, 0.10]:
                for cf_d in [0.01, 0.03, 0.05, 0.10]:
                    model.sensitivity_analysis(
                        cf_y=cf_y, cf_d=cf_d, rho=1.0, level=0.95, null_hypothesis=0.0
                    )
                    p = model.sensitivity_params
                    sensitivity.append(
                        dict(
                            cf_y=cf_y,
                            cf_d=cf_d,
                            rho=1.0,
                            level=0.95,
                            null_effect=0.0,
                            estimate=float(model.coef[0]),
                            effect_lower=float(p["theta"]["lower"][0]),
                            effect_upper=float(p["theta"]["upper"][0]),
                            confidence_lower=float(p["ci"]["lower"][0]),
                            confidence_upper=float(p["ci"]["upper"][0]),
                            RV=float(p["rv"][0]),
                            RVa=float(p["rva"][0]),
                            confidence_convention="95% one-sided confidence bounds for effect-bound endpoints",
                        )
                    )
        print(json.dumps(refits[-1]), flush=True)
    pd.DataFrame(diagnostics).to_csv(root / "results/v3_overlap.csv", index=False)
    pd.DataFrame(refits).to_csv(root / "results/v3_irm_refit_comparison.csv", index=False)
    pd.DataFrame(sensitivity).to_csv(root / "results/v3_rf_irm_sensitivity.csv", index=False)
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.7), sharex=True)
    for ax, (name, raw) in zip(axes, hist.items(), strict=True):
        for arm, color in [(0, "#0072B2"), (1, "#D55E00")]:
            ax.hist(
                raw[treatment == arm],
                bins=np.linspace(0, 1, 51),
                density=True,
                alpha=0.45,
                color=color,
                label="Control" if arm == 0 else "Treatment",
            )
        ax.axvline(0.01, color="black", ls="--", lw=1)
        ax.axvline(0.99, color="black", ls="--", lw=1)
        ax.set(title=name, xlabel="Raw out-of-fold propensity", ylabel="Density")
        ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(root / "figures/v3_overlap.png", dpi=250)
    plt.close(fig)
    # Compute the original holdout income-quartile rule without changing estimates.
    idx = np.random.default_rng(SEED).permutation(len(data))
    test = idx[len(data) // 2 :]
    _, bins = pd.qcut(data.inc.iloc[test], 4, labels=False, retbins=True)
    pd.DataFrame(
        [
            dict(
                group=q + 1,
                lower=float(bins[q]),
                upper=float(bins[q + 1]),
                rule="held-out empirical income quartile; right-closed; first lower endpoint included",
                grouping_cutoffs="computed from heldout income; not pre-specified numerical thresholds",
            )
            for q in range(4)
        ]
    ).to_csv(root / "results/v3_income_quartile_cutoffs.csv", index=False)
    manifest = dict(
        seed=SEED,
        folds_sha256=split_hash,
        input_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        protocol_sha256=hashlib.sha256((root / "docs/V3_PROTOCOL.md").read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        elapsed_seconds=time.monotonic() - began,
        refit_only_IRM=True,
        clipping_only=True,
        removed=0,
        raw_prediction_method="stored fitted fold classifiers predict_proba; matched clipped SDK predictions",
        warnings=warning_log,
        paid_calls=0,
        official_definitions="https://docs.doubleml.org/stable/guide/sensitivity.html",
        income_group_estimates_inherited_sha256=hashlib.sha256(
            (root / "results/income_group_ate.csv").read_bytes()
        ).hexdigest(),
    )
    (root / "results/v3_diagnostics_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    (private / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
