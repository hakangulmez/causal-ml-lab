"""Predeclared sparse linear DGP and regularized nonorthogonal comparator."""

import hashlib
import json
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from causal_ml_lab.core import crossfit_plr, dml_dgp, ols

N, P, REPS, SEED = 600, 200, 100, 20261008
ALPHA = float(np.sqrt(2 * np.log(P) / N))


def dgp(seed, n=N, p=P):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, p))
    confounders = x[:, :5].sum(axis=1)
    d = 1.5 * confounders + rng.normal(size=n)
    y = d + confounders + rng.normal(size=n)
    return y, d, x


def plugin(y, d, x, alpha=ALPHA):
    """Exact partial penalization: D/intercept unpenalized, X Lasso-penalized."""
    controls = np.column_stack([np.ones(len(d)), d])
    bx = np.linalg.lstsq(controls, x, rcond=None)[0]
    by = np.linalg.lstsq(controls, y, rcond=None)[0]
    learner = Lasso(alpha=alpha, fit_intercept=False, max_iter=10000, tol=1e-7)
    learner.fit(x - controls @ bx, y - controls @ by)
    residual_y = y - x @ learner.coef_
    theta, se = ols(residual_y, d, np.empty((len(d), 0)))
    # This SE treats learned g as fixed; deliberately naive, empirical coverage reported.
    return theta, se


def run(root: Path, repetitions=REPS):
    began = time.monotonic()
    code = {
        f"src/causal_ml_lab/{p.name}": hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [Path(__file__), Path(__file__).with_name("core.py")]
    }
    declaration = root / "docs/DGP2_PREDECLARATION.md"
    token = hashlib.sha256(json.dumps([code, repetitions], sort_keys=True).encode()).hexdigest()[
        :16
    ]
    cache = root / "runs" / ("sparse_" + token + ".csv")
    cache.parent.mkdir(exist_ok=True)
    rows = pd.read_csv(cache).to_dict("records") if cache.exists() else []
    done = {int(r["rep"]) for r in rows}
    for rep in range(repetitions):
        if rep in done:
            continue
        y, d, x = dgp(SEED + rep)
        learner = make_pipeline(StandardScaler(), Lasso(alpha=ALPHA, max_iter=10000, tol=1e-7))
        estimates = [
            ("OLS", ols(y, d, x)),
            ("NaivePlugin", plugin(y, d, x)),
            ("DML", crossfit_plr(y, d, x, learner, folds=5, seed=20261007)),
        ]
        for method, (point, se) in estimates:
            rows.append(
                dict(
                    rep=rep,
                    method=method,
                    estimate=point,
                    se=se,
                    covered=abs(point - 1) <= 1.96 * se,
                )
            )
        pd.DataFrame(rows).to_csv(cache, index=False)
        if (rep + 1) % 10 == 0:
            print(json.dumps(dict(dgp=2, repetitions=rep + 1)), flush=True)
    output = []
    for method_key, part in pd.DataFrame(rows).groupby("method"):
        error = part.estimate - 1
        coverage = float(part.covered.mean())
        output.append(
            dict(
                dgp="DGP2_sparse",
                method=str(method_key),
                repetitions=len(part),
                bias=float(error.mean()),
                rmse=float(np.sqrt(np.mean(error**2))),
                mc_se=float(error.std(ddof=1) / np.sqrt(len(error))),
                coverage=coverage,
                coverage_mc_se=float(np.sqrt(coverage * (1 - coverage) / len(part))),
            )
        )
    old = pd.read_csv(root / "results/monte_carlo.csv").query('module=="DML"').copy()
    old["dgp"] = "DGP1_nonlinear"
    old["coverage_mc_se"] = np.sqrt(old.coverage * (1 - old.coverage) / old.repetitions)
    original_plugin = []
    for rep in range(repetitions):
        y, d, x = dml_dgp(20261007 + rep)
        point, se = plugin(y, d, x, alpha=float(np.sqrt(2 * np.log(20) / 500)))
        original_plugin.append((point - 1, abs(point - 1) <= 1.96 * se))
    e = np.array([r[0] for r in original_plugin])
    covered = float(np.mean([r[1] for r in original_plugin]))
    output.append(
        dict(
            dgp="DGP1_nonlinear",
            method="NaivePlugin",
            repetitions=len(e),
            bias=float(e.mean()),
            rmse=float(np.sqrt(np.mean(e**2))),
            mc_se=float(e.std(ddof=1) / np.sqrt(len(e))),
            coverage=covered,
            coverage_mc_se=float(np.sqrt(covered * (1 - covered) / len(e))),
        )
    )
    table = pd.concat([old.drop(columns=["module"]), pd.DataFrame(output)], ignore_index=True)
    # Wilson intervals retain positive upper uncertainty even with zero covered draws.
    z = 1.959963984540054
    n = table.repetitions.to_numpy()
    proportion = table.coverage.to_numpy()
    denominator = 1 + z**2 / n
    center = (proportion + z**2 / (2 * n)) / denominator
    halfwidth = z * np.sqrt(proportion * (1 - proportion) / n + z**2 / (4 * n**2)) / denominator
    table["coverage_lo95"] = np.where(proportion == 0, 0, np.maximum(0, center - halfwidth))
    table["coverage_hi95"] = np.where(proportion == 1, 1, np.minimum(1, center + halfwidth))
    table.to_csv(root / "results/dml_two_dgps.csv", index=False)
    manifest = dict(
        code=code,
        n=N,
        p=P,
        sparsity=5,
        true_effect=1.0,
        seed=SEED,
        repetitions=repetitions,
        alpha=ALPHA,
        folds=5,
        paid_calls=0,
        declaration_sha256=hashlib.sha256(declaration.read_bytes()).hexdigest(),
        comparator_declaration_sha256=hashlib.sha256(
            (root / "docs/DGP1_PLUGIN_ADDENDUM.md").read_bytes()
        ).hexdigest(),
        inherited_dgp1_sha256=hashlib.sha256(
            (root / "results/monte_carlo.csv").read_bytes()
        ).hexdigest(),
        elapsed_seconds=time.monotonic() - began,
        private_cache=str(cache.relative_to(root)),
        naive_definition=(
            "NaivePlugin: nonorthogonal joint penalized fit in both; "
            "retained DGP1 NaiveML: in-sample orthogonal"
        ),
    )
    (root / "results/sparse_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest
