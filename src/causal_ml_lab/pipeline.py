"""Seeded Monte Carlos and licensed private runtime replication."""

import hashlib
import json
import subprocess
import time
from pathlib import Path

import doubleml as dml
import numpy as np
import pandas as pd
from doubleml.datasets import fetch_401K
from sklearn.ensemble import (
    GradientBoostingClassifier,
    GradientBoostingRegressor,
    RandomForestClassifier,
    RandomForestRegressor,
)
from sklearn.linear_model import LassoCV, LogisticRegressionCV
from sklearn.model_selection import StratifiedKFold
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from causal_ml_lab.core import continuous_dgp, crossfit_plr, cs_simple, did_dgp, dml_dgp, ols, twfe

SEED = 20261007
COVARIATES = ["age", "inc", "educ", "fsize", "marr", "twoearn", "db", "pira", "hown"]

SIPP_DTYPES = {
    "nifa": "float32",
    "net_tfa": "float32",
    "tw": "float32",
    "age": "int8",
    "inc": "float32",
    "fsize": "int8",
    "educ": "int8",
    "db": "int8",
    "marr": "int8",
    "twoearn": "int8",
    "e401": "int8",
    "p401": "int8",
    "pira": "int8",
    "hown": "int8",
}


def learners(name, quick=False):
    if name == "Lasso":
        return make_pipeline(StandardScaler(), LassoCV(cv=3 if quick else 5)), make_pipeline(
            StandardScaler(),
            LogisticRegressionCV(cv=3 if quick else 5, max_iter=2000, random_state=SEED),
        )
    if name == "RF":
        return RandomForestRegressor(
            n_estimators=30 if quick else 150,
            min_samples_leaf=10,
            max_features=0.7,
            random_state=SEED,
            n_jobs=1,
        ), RandomForestClassifier(
            n_estimators=30 if quick else 150,
            min_samples_leaf=10,
            max_features=0.7,
            random_state=SEED,
            n_jobs=1,
        )
    return GradientBoostingRegressor(
        n_estimators=30 if quick else 100, max_depth=2, random_state=SEED
    ), GradientBoostingClassifier(n_estimators=30 if quick else 100, max_depth=2, random_state=SEED)


def mc(root, repetitions=100):
    digest = hashlib.sha256(
        Path(__file__).read_bytes() + Path(__file__).with_name("core.py").read_bytes()
    ).hexdigest()[:16]
    cache = root / "runs" / f"mc_{digest}_{repetitions}_private.csv"
    cache.parent.mkdir(exist_ok=True)
    rows = pd.read_csv(cache).to_dict("records") if cache.exists() else []
    completed = {int(row["rep"]) for row in rows}
    for rep in range(repetitions):
        if rep in completed:
            continue
        panel, truth = did_dgp(SEED + rep)
        point, se = twfe(panel)
        cs = cs_simple(panel)
        rows.extend(
            [
                dict(
                    module="DiD",
                    rep=rep,
                    method="TWFE",
                    estimate=point,
                    truth=truth,
                    se=se,
                    covered=abs(point - truth) <= 1.96 * se,
                ),
                dict(
                    module="DiD",
                    rep=rep,
                    method="CS_unconditional",
                    estimate=cs,
                    truth=truth,
                    se=np.nan,
                    covered=np.nan,
                ),
            ]
        )
        y, d, x = dml_dgp(SEED + rep)
        model = GradientBoostingRegressor(n_estimators=60, max_depth=2, random_state=SEED)
        for method, (point, se) in [
            ("OLS", ols(y, d, x)),
            ("NaiveML", crossfit_plr(y, d, x, model, naive=True)),
            ("DML", crossfit_plr(y, d, x, model, folds=5)),
        ]:
            rows.append(
                dict(
                    module="DML",
                    rep=rep,
                    method=method,
                    estimate=point,
                    truth=1.0,
                    se=se,
                    covered=abs(point - 1) <= 1.96 * se,
                )
            )
        if (rep + 1) % 10 == 0 or rep + 1 == repetitions:
            temporary = cache.with_suffix(".tmp")
            pd.DataFrame(rows).to_csv(temporary, index=False)
            temporary.replace(cache)
    f = pd.DataFrame(rows)
    (root / "runs").mkdir(exist_ok=True)
    f.to_csv(root / "runs/mc_private.csv", index=False)
    output = []
    for (module, method_key), part in f.groupby(["module", "method"]):
        e = part.estimate - part.truth
        output.append(
            dict(
                module=module,
                method=str(method_key),
                repetitions=len(part),
                bias=e.mean(),
                rmse=np.sqrt(np.mean(e**2)),
                mc_se=e.std(ddof=1) / np.sqrt(len(e)),
                coverage=part.covered.mean(),
            )
        )
    pd.DataFrame(output).to_csv(root / "results/monte_carlo.csv", index=False)
    dose, att, acrt = continuous_dgp(SEED)
    bins = pd.qcut(dose, 4, labels=False)
    out = []
    for group in range(4):
        ix = bins == group
        out.append(
            dict(
                dose_quartile=group + 1,
                n=int(ix.sum()),
                mean_dose=dose[ix].mean(),
                ATT=att[ix].mean(),
                ACRT=acrt[ix].mean(),
                ATT_se=att[ix].std(ddof=1) / np.sqrt(ix.sum()),
                ACRT_se=acrt[ix].std(ddof=1) / np.sqrt(ix.sum()),
            )
        )
    pd.DataFrame(out).to_csv(root / "results/continuous.csv", index=False)


def pension(root, quick=False, frame=None):
    path = root / "data/raw/sipp1991.csv"
    path.parent.mkdir(parents=True, exist_ok=True)
    if frame is not None:
        data = frame
    elif path.exists():
        data = pd.read_csv(path)
    else:
        # User-approved analysis; public extract fetched by the documented package API.
        data = fetch_401K(return_type="DataFrame")
        data.to_csv(path, index=False)
    # Restore the verified native Stata schema after CSV reads. Otherwise float32
    # expansion and integer promotion can change learner arithmetic on a resumed run.
    if set(SIPP_DTYPES).issubset(data.columns):
        data = data.astype(SIPP_DTYPES)
    if data[COVARIATES + ["net_tfa", "e401"]].isna().any().any():
        raise ValueError("Missing SIPP input; no silent deletion")
    np.random.seed(SEED)
    rows = []
    y = data.net_tfa.to_numpy()
    d = data.e401.to_numpy()
    x = data[COVARIATES].to_numpy()
    point, se = ols(y, d, x)
    rows.append(
        dict(
            model="OLS",
            learner="Linear",
            estimate=point,
            se=se,
            lo95=point - 1.96 * se,
            hi95=point + 1.96 * se,
            n=len(data),
        )
    )
    doubledata = dml.DoubleMLData(data, y_col="net_tfa", d_cols="e401", x_cols=COVARIATES)
    cache_token = hashlib.sha256(
        data.to_csv(index=False).encode() + Path(__file__).read_bytes() + str(quick).encode()
    ).hexdigest()[:16]
    for name in ["Lasso", "RF", "GB"]:
        for estimator in ["PLR", "IRM"]:
            cache = root / "runs" / f"pension_{estimator}_{name}_{cache_token}.json"
            if cache.exists() and not quick:
                rows.append(json.loads(cache.read_text()))
                continue
            outcome, treatment = learners(name, quick)
            if estimator == "PLR":
                model = dml.DoubleMLPLR(
                    doubledata, ml_l=outcome, ml_m=treatment, n_folds=3 if quick else 5, n_rep=1
                )
            else:
                model = dml.DoubleMLIRM(
                    doubledata,
                    ml_g=outcome,
                    ml_m=treatment,
                    n_folds=3 if quick else 5,
                    n_rep=1,
                    score="ATE",
                    trimming_threshold=0.01,
                )
            model.set_sample_splitting(
                list(
                    StratifiedKFold(3 if quick else 5, shuffle=True, random_state=SEED).split(x, d)
                )
            )
            start = time.monotonic()
            model.fit(n_jobs_cv=1)
            point = float(model.coef[0])
            se = float(model.se[0])
            ci = model.confint().iloc[0]
            row = dict(
                model=estimator,
                learner=name,
                estimate=point,
                se=se,
                lo95=float(ci.iloc[0]),
                hi95=float(ci.iloc[1]),
                n=len(data),
                seconds=time.monotonic() - start,
                folds=3 if quick else 5,
                propensity_clipping=0.01 if estimator == "IRM" else None,
            )
            rows.append(row)
            cache.parent.mkdir(exist_ok=True)
            cache.write_text(json.dumps(row, indent=2))
            print(
                json.dumps({"pension": estimator, "learner": name, "seconds": row["seconds"]}),
                flush=True,
            )
    pd.DataFrame(rows).to_csv(root / "results/pension.csv", index=False)
    return data


def forest(root, data):
    from econml.dml import CausalForestDML
    from scipy.stats import norm

    # Income groups fixed before fitting; outcomes used only in their held-out fold.
    y = data.net_tfa.to_numpy()
    t = data.e401.to_numpy()
    x = data[COVARIATES].to_numpy()
    cut = len(data) // 2
    rng = np.random.default_rng(SEED)
    idx = rng.permutation(len(data))
    train, test = idx[:cut], idx[cut:]
    estimator = CausalForestDML(
        model_y=RandomForestRegressor(n_estimators=100, min_samples_leaf=10, random_state=SEED),
        model_t=RandomForestClassifier(n_estimators=100, min_samples_leaf=10, random_state=SEED),
        discrete_treatment=True,
        n_estimators=400,
        min_samples_leaf=20,
        max_depth=8,
        random_state=SEED,
        n_jobs=1,
        cv=3,
        inference=True,
    )
    estimator.fit(y[train], t[train], X=x[train])
    effects = estimator.effect(x[test])
    lo, hi = estimator.effect_interval(x[test], alpha=0.05)
    quartile = pd.qcut(data.inc.iloc[test], 4, labels=False)
    rows = []
    for q in range(4):
        ix = np.asarray(quartile == q)
        rows.append(
            dict(
                income_quartile=q + 1,
                n=int(ix.sum()),
                mean_income=float(data.inc.iloc[test].to_numpy()[ix].mean()),
                mean_CATE=float(effects[ix].mean()),
                mean_pointwise_lo95=float(lo[ix].mean()),
                mean_pointwise_hi95=float(hi[ix].mean()),
                warning="Mean pointwise endpoints are not group-mean confidence intervals",
            )
        )
    pd.DataFrame(rows).to_csv(root / "results/forest_descriptive.csv", index=False)
    # Honest held-out orthogonal AIPW group means: nuisance learners fit training half.
    outcome, treatment = learners("RF")
    m = treatment.fit(x[train], t[train]).predict_proba(x[test])[:, 1]
    m = np.clip(m, 0.01, 0.99)
    g0 = (
        RandomForestRegressor(n_estimators=150, min_samples_leaf=10, random_state=SEED)
        .fit(x[train][t[train] == 0], y[train][t[train] == 0])
        .predict(x[test])
    )
    g1 = (
        RandomForestRegressor(n_estimators=150, min_samples_leaf=10, random_state=SEED)
        .fit(x[train][t[train] == 1], y[train][t[train] == 1])
        .predict(x[test])
    )
    score = g1 - g0 + t[test] * (y[test] - g1) / m - (1 - t[test]) * (y[test] - g0) / (1 - m)
    # Best linear predictor of held-out orthogonal effects on learned forest CATE.
    # Centering separates mean effects from calibration; forest/nuisance fits use
    # only the training half. HC1 inference is conditional on those learned fits.
    calibration, calibration_se = ols(score, effects - effects.mean(), np.empty((len(test), 0)))
    pd.DataFrame(
        [
            dict(
                term="centered_forest_CATE",
                estimate=calibration,
                se=calibration_se,
                lo95=calibration - norm.ppf(0.975) * calibration_se,
                hi95=calibration + norm.ppf(0.975) * calibration_se,
                n=len(test),
                estimand="Held-out AIPW best linear predictor slope",
                inference="HC1; conditional on training-half forest/nuisance fits",
            )
        ]
    ).to_csv(root / "results/forest_blp.csv", index=False)
    groups = []
    for q in range(4):
        z = score[np.asarray(quartile == q)]
        point = z.mean()
        se = z.std(ddof=1) / np.sqrt(len(z))
        groups.append(
            dict(
                income_quartile=q + 1,
                estimate=point,
                se=se,
                lo95=point - norm.ppf(0.975) * se,
                hi95=point + norm.ppf(0.975) * se,
                n=len(z),
                estimand="Held-out income-group ATE; not forest-ranked GATES",
            )
        )
    pd.DataFrame(groups).to_csv(root / "results/income_group_ate.csv", index=False)


def run(root: Path, quick=False, synthetic=None):
    start = time.monotonic()
    (root / "results").mkdir(exist_ok=True)
    (root / "runs").mkdir(exist_ok=True)
    # Failed components are recorded by name, not silently treated as complete.
    code = {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in (root / "src").rglob("*.py")
    }
    failures = []
    mc(root, 3 if quick else 100)
    data = pension(root, quick, synthetic)
    if not quick:
        for label, action in [
            ("R_DiD", lambda: subprocess.run(["Rscript", "scripts/did.R"], cwd=root, check=True)),
            ("CausalForest", lambda: forest(root, data)),
        ]:
            try:
                action()
            except (subprocess.CalledProcessError, ValueError, RuntimeError, ImportError) as e:
                failures.append(dict(component=label, error=type(e).__name__ + ": " + str(e)[:200]))
    manifest = dict(
        seed=SEED,
        elapsed_seconds=time.monotonic() - start,
        paid_calls=0,
        quick=quick,
        code=code,
        n_sipp=len(data),
        sipp_semantic_sha256=hashlib.sha256(data.to_csv(index=False).encode()).hexdigest(),
        failures=failures,
        folds=3 if quick else 5,
        scope="Original simulations; mpdta; approved private SIPP analysis; no thesis access",
    )
    (root / "results/manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest
