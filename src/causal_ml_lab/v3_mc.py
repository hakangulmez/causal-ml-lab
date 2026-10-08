# ruff: noqa: E501
"""Strict ten-minute blocks; completed matched repetitions only; unchanged estimators."""

import hashlib
import json
import multiprocessing as mp
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.linear_model import Lasso
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from causal_ml_lab.core import crossfit_plr, cs_simple, did_dgp, dml_dgp, ols, twfe
from causal_ml_lab.sparse import ALPHA, dgp, plugin

SEED = 20261007


def repetition(kind, rep):
    rows = []
    if kind == "nonlinear":
        y, d, x = dml_dgp(SEED + rep)
        truth = 1.0
        draw_hash = hashlib.sha256(y.tobytes() + d.tobytes() + x.tobytes()).hexdigest()
        learner = GradientBoostingRegressor(n_estimators=60, max_depth=2, random_state=SEED)
        estimates = [
            ("OLS", ols(y, d, x)),
            ("NaiveML", crossfit_plr(y, d, x, learner, naive=True)),
            ("NaivePlugin", plugin(y, d, x, alpha=float(np.sqrt(2 * np.log(20) / 500)))),
            ("DML", crossfit_plr(y, d, x, learner, folds=5)),
        ]
        for method, (point, se) in estimates:
            rows.append(
                dict(
                    module="DML",
                    rep=rep,
                    method=method,
                    estimate=point,
                    se=se,
                    truth=truth,
                    covered=abs(point - truth) <= 1.96 * se,
                    seed=SEED + rep,
                    draw_sha256=draw_hash,
                )
            )
        panel, truth = did_dgp(SEED + rep)
        point, se = twfe(panel)
        cs = cs_simple(panel)
        for method, point, se in [("TWFE", point, se), ("CS_unconditional", cs, np.nan)]:
            rows.append(
                dict(
                    module="DiD",
                    rep=rep,
                    method=method,
                    estimate=point,
                    se=se,
                    truth=truth,
                    covered=abs(point - truth) <= 1.96 * se if np.isfinite(se) else np.nan,
                    seed=SEED + rep,
                    draw_sha256=hashlib.sha256(
                        panel["y"].tobytes() + panel["d"].tobytes()
                    ).hexdigest(),
                )
            )
    else:
        y, d, x = dgp(20261008 + rep)
        truth = 1.0
        learner = make_pipeline(StandardScaler(), Lasso(alpha=ALPHA, max_iter=10000, tol=1e-7))
        for method, (point, se) in [
            ("OLS", ols(y, d, x)),
            ("NaivePlugin", plugin(y, d, x)),
            ("DML", crossfit_plr(y, d, x, learner, folds=5, seed=SEED)),
        ]:
            rows.append(
                dict(
                    module="DML",
                    rep=rep,
                    method=method,
                    estimate=point,
                    se=se,
                    truth=truth,
                    covered=abs(point - truth) <= 1.96 * se,
                    seed=20261008 + rep,
                    draw_sha256=hashlib.sha256(y.tobytes() + d.tobytes() + x.tobytes()).hexdigest(),
                )
            )
    return rows


def summary(frame):
    output = []
    z = 1.959963984540054
    for keys, part in frame.groupby(["module", "method"]):
        error = part.estimate - part.truth
        n = len(part)
        coverage = float(part.covered.replace({"True": 1.0, "False": 0.0}).astype(float).mean())
        denom = 1 + z * z / n
        center = (coverage + z * z / (2 * n)) / denom
        half = z * np.sqrt(coverage * (1 - coverage) / n + z * z / (4 * n * n)) / denom
        output.append(
            dict(
                module=keys[0],
                method=keys[1],
                repetitions=n,
                bias=float(error.mean()),
                rmse=float(np.sqrt(np.mean(error**2))),
                mc_se=float(error.std(ddof=1) / np.sqrt(n)),
                coverage=coverage,
                coverage_mc_se=float(np.sqrt(coverage * (1 - coverage) / n)),
                coverage_lo95=max(0, center - half) if np.isfinite(center) else np.nan,
                coverage_hi95=min(1, center + half) if np.isfinite(center) else np.nan,
            )
        )
    return pd.DataFrame(output)


def _safe_repetition(kind, rep):
    try:
        return dict(rows=repetition(kind, rep), error=None)
    except Exception as exc:
        return dict(rows=[], error=type(exc).__name__ + ": " + str(exc))


def run_block(root: Path, kind, budget=600, target=1000):
    saved_manifest = root / "results" / ("v3_" + kind + "_mc_manifest.json")
    if saved_manifest.exists():
        saved = json.loads(saved_manifest.read_text())
        if (
            saved["protocol_sha256"]
            != hashlib.sha256((root / "docs/V3_PROTOCOL.md").read_bytes()).hexdigest()
        ):
            raise ValueError("Protocol changed; cannot reuse consumed simulation budget")
        print("Existing budgeted block retained; no additional simulation executed", flush=True)
        return saved
    began = time.monotonic()
    deadline = began + budget
    private = root / "runs/v3_mc"
    private.mkdir(parents=True, exist_ok=True)
    checkpoint = private / (kind + ".csv")
    rows = []
    failures = []
    replays = []
    # Original rows are not reused blindly: the deterministic first and last draw
    # estimates are replayed before reuse, all draw hashes/seeds regenerated below.
    if kind == "nonlinear":
        old = pd.read_csv(root / "runs/mc_private.csv")
        expected = pd.read_csv(root / "versions/v2-2026-10-07/results/monte_carlo.csv")
        check = summary(old)
        for record in expected.itertuples():
            rec: Any = record
            r = check[(check.module == rec.module) & (check.method == rec.method)].iloc[0]
            assert (
                np.isclose(float(r.bias), float(rec.bias), atol=1e-12)
                and r.repetitions == rec.repetitions
            )
    else:
        manifest = json.loads(
            (root / "versions/v2-2026-10-07/results/sparse_manifest.json").read_text()
        )
        old = pd.read_csv(root / manifest["private_cache"])
        old["module"] = "DML"
        old["truth"] = 1.0
    reuse_count = len(old.rep.unique())
    # fork avoids paying an interpreter/import cost on each draw and permits an
    # in-progress draw to be terminated at the fixed deadline without inclusion.
    context = mp.get_context("fork")
    pool = context.Pool(1)
    try:
        for rep in [int(old.rep.min()), int(old.rep.max())]:
            out = pool.apply_async(_safe_repetition, (kind, rep)).get(
                timeout=max(0.01, deadline - time.monotonic())
            )
            assert out["error"] is None, out
            fresh = pd.DataFrame(out["rows"])
            for previous in old[old.rep == rep].itertuples():
                current = fresh[
                    (fresh.module == previous.module) & (fresh.method == previous.method)
                ].iloc[0]
                np.testing.assert_allclose(
                    np.asarray([previous.estimate, previous.se], dtype=float),
                    np.asarray([current.estimate, current.se], dtype=float),
                    rtol=1e-7,
                    atol=1e-9,
                    equal_nan=True,
                )
            replays.append(dict(rep=rep, matched=True, seed=int(fresh.seed.iloc[0])))
        rows = old.to_dict("records")
        # The additional DGP1 plug-in has no V2 row-level cache: recover it for the
        # same original seeds, within this block's budget, before any new draw.
        if kind == "nonlinear":
            for rep in sorted(old.rep.unique()):
                if time.monotonic() >= deadline:
                    raise TimeoutError("plugin recovery deadline")
                y, d, x = dml_dgp(SEED + int(rep))
                point, se = plugin(y, d, x, alpha=float(np.sqrt(2 * np.log(20) / 500)))
                rows.append(
                    dict(
                        module="DML",
                        rep=int(rep),
                        method="NaivePlugin",
                        estimate=point,
                        se=se,
                        truth=1.0,
                        covered=abs(point - 1) <= 1.96 * se,
                    )
                )
        for row in rows:
            rep = int(row["rep"])
            row["seed"] = (SEED if kind == "nonlinear" else 20261008) + rep
            if row["module"] == "DiD":
                panel, _ = did_dgp(SEED + rep)
                payload = panel["y"].tobytes() + panel["d"].tobytes()
            else:
                y, d, x = dml_dgp(SEED + rep) if kind == "nonlinear" else dgp(20261008 + rep)
                payload = y.tobytes() + d.tobytes() + x.tobytes()
            row["draw_sha256"] = hashlib.sha256(payload).hexdigest()
            row["execution"] = (
                "verified V2 reuse"
                if row["method"] != "NaivePlugin" or kind != "nonlinear"
                else "recovered V2 seed comparator"
            )
        for rep in range(reuse_count, target):
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                break
            try:
                out = pool.apply_async(_safe_repetition, (kind, rep)).get(timeout=remaining)
            except mp.TimeoutError:
                failures.append(dict(rep=rep, reason="unfinished at fixed deadline; excluded"))
                break
            if out["error"]:
                failures.append(dict(rep=rep, reason=out["error"]))
                continue
            rows.extend(row | {"execution": "new V3 repetition"} for row in out["rows"])
            temporary = checkpoint.with_suffix(".tmp")
            pd.DataFrame(rows).to_csv(temporary, index=False)
            temporary.replace(checkpoint)
            if rep % 25 == 0:
                print(
                    json.dumps(
                        dict(
                            block=kind,
                            completed=len({r["rep"] for r in rows}),
                            seconds=time.monotonic() - began,
                        )
                    ),
                    flush=True,
                )
    except (TimeoutError, mp.TimeoutError) as exc:
        failures.append(dict(reason=str(exc), phase="V2 verification/recovery"))
    finally:
        pool.terminate()
        pool.join()
    frame = pd.DataFrame(rows)
    required = 6 if kind == "nonlinear" else 3
    if len(frame):
        complete = frame.groupby("rep").size()
        frame = frame[frame.rep.isin(complete[complete == required].index)]
        frame.to_csv(checkpoint, index=False)
        table = summary(frame)
        table.to_csv(root / "results" / ("v3_" + kind + "_mc.csv"), index=False)
    actual = frame.rep.nunique() if len(frame) else 0
    manifest = dict(
        block=kind,
        budget_seconds=budget,
        target_repetitions=target,
        completed_repetitions=int(actual),
        verified_reused_repetitions=min(reuse_count, actual),
        new_completed_repetitions=max(0, actual - reuse_count),
        replay_checks=replays,
        failures=failures,
        elapsed_seconds=time.monotonic() - began,
        stop_rule="time or1000 only; incomplete/failed matched draws excluded",
        seed_sequence="20261007+rep0" if kind == "nonlinear" else "20261008+rep0",
        protocol_sha256=hashlib.sha256((root / "docs/V3_PROTOCOL.md").read_bytes()).hexdigest(),
        code_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        paid_calls=0,
    )
    (root / "results" / ("v3_" + kind + "_mc_manifest.json")).write_text(
        json.dumps(manifest, indent=2) + "\n"
    )
    print(json.dumps(manifest), flush=True)
    return manifest
