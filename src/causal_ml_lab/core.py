"""Transparent estimands, cluster inference and cross-fitted orthogonal scores."""

import numpy as np
from sklearn.base import clone
from sklearn.model_selection import KFold


def ols(y, d, x):
    design = np.column_stack([np.ones(len(y)), d, x])
    b = np.linalg.lstsq(design, y, rcond=None)[0]
    e = y - design @ b
    bread = np.linalg.pinv(design.T @ design)
    meat = (design * e[:, None]).T @ (design * e[:, None])
    variance = bread @ meat @ bread * len(y) / (len(y) - design.shape[1])
    return float(b[1]), float(np.sqrt(variance[1, 1]))


def plr_score(y, d, g, m):
    v = d - m
    r = y - g
    den = float(np.mean(v * v))
    if den < 1e-12:
        raise ValueError("Treatment residual variance is zero")
    theta = float(np.mean(v * r) / den)
    influence = v * (r - theta * v) / den
    return theta, float(np.std(influence, ddof=1) / np.sqrt(len(y)))


def crossfit_plr(y, d, x, learner, folds=5, seed=20261007, naive=False):
    g = np.zeros(len(y))
    m = np.zeros(len(y))
    splits = (
        [(np.arange(len(y)), np.arange(len(y)))]
        if naive
        else KFold(folds, shuffle=True, random_state=seed).split(x)
    )
    for train, test in splits:
        g[test] = clone(learner).fit(x[train], y[train]).predict(x[test])
        m[test] = clone(learner).fit(x[train], d[train]).predict(x[test])
    return plr_score(y, d, g, m)


def twfe(panel):
    # Balanced panel two-way within residualization; retain cluster covariance.
    y = np.asarray(panel["y"])
    d = np.asarray(panel["d"])
    ids = np.asarray(panel["id"])
    t = np.asarray(panel["time"])

    def within(a):
        out = a.copy() - a.mean()
        for key in [ids, t]:
            for value in np.unique(key):
                out[key == value] -= a[key == value].mean() - a.mean()
        return out

    yy, dd = within(y), within(d)
    den = float(dd @ dd)
    if den < 1e-12:
        raise ValueError("No residual treatment variation")
    theta = float(dd @ yy / den)
    resid = yy - theta * dd
    sums = np.array([np.sum(dd[ids == i] * resid[ids == i]) for i in np.unique(ids)])
    n = len(sums)
    se = float(np.sqrt(np.sum(sums * sums) * n / (n - 1)) / den)
    return theta, se


def cs_simple(panel):
    # Unconditional balanced-panel group-time estimator against never treated.
    import pandas as pd

    p = pd.DataFrame(panel)
    wide = p.pivot(index="id", columns="time", values="y")
    cohort = p.groupby("id").g.first()
    att = []
    weights = []
    for g in sorted(cohort.unique()):
        if g == 0:
            continue
        treated = cohort.index[cohort == g]
        controls = cohort.index[cohort == 0]
        for time in wide.columns[wide.columns >= g]:
            change = wide[time] - wide[g - 1]
            att.append(float(change.loc[treated].mean() - change.loc[controls].mean()))
            weights.append(len(treated))
    if not weights:
        raise ValueError("No treated cohort-time cells")
    return float(np.average(att, weights=weights))


def did_dgp(seed, n=400):
    rng = np.random.default_rng(seed)
    cohorts = rng.choice([0, 3, 5, 7], n)
    ids = np.repeat(np.arange(n), 8)
    times = np.tile(np.arange(1, 9), n)
    g = np.repeat(cohorts, 8)
    d = ((g > 0) & (times >= g)).astype(float)
    effects = d * (times - g + 1) * (1 + (g == 5) * 0.7 + (g == 7) * 1.5)
    y = (
        np.repeat(rng.normal(size=n), 8)
        + 0.15 * times
        + effects
        + rng.normal(scale=0.5, size=n * 8)
    )
    return dict(id=ids, time=times, g=g, d=d, y=y), float(effects[d == 1].mean())


def dml_dgp(seed, n=500, p=20):
    rng = np.random.default_rng(seed)
    x = rng.normal(size=(n, p))
    d = 0.5 * x[:, 0] ** 2 + np.sin(x[:, 1]) + rng.normal(size=n)
    y = 1.0 * d + x[:, 0] ** 2 + np.cos(x[:, 1]) + 0.5 * x[:, 3] + rng.normal(size=n)
    return y, d, x


def continuous_dgp(seed, n=5000):
    rng = np.random.default_rng(seed)
    x = rng.uniform(0, 1, n)
    dose = 0.2 + 0.6 * x + rng.uniform(0, 0.2, n)
    # Y(d)-Y(0)=a_i d + .5 d²; selection on gains a_i=1+2x.
    a = 1 + 2 * x
    effect = a * dose + 0.5 * dose * dose
    derivative = a + dose
    return dose, effect, derivative
