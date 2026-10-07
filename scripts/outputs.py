# ruff: noqa: E501
"""Code-derived summaries, uncertainty figures and exactly two-page draft note."""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from policy import write_note

from causal_ml_lab.viz import PALETTE, apply_style

root = Path.cwd()
figdir = root / "figures"
figdir.mkdir(exist_ok=True)
apply_style()
did = pd.read_csv(root / "results/did_monte_carlo.csv")
mc = pd.read_csv(root / "results/monte_carlo.csv")
pension = pd.read_csv(root / "results/pension.csv")
mp = pd.read_csv(root / "results/mpdta_estimates.csv")
manifest = json.loads((root / "results/manifest.json").read_text())
assert did.method.nunique() == len(did) == 3, "DiD summaries must have one row per estimator"
both = pd.read_csv(root / "results/dml_two_dgps.csv")
labels = {
    "OLS": "OLS",
    "NaiveML": "V1 in-sample naive ML",
    "NaivePlugin": "Linear Lasso plug-in",
    "DML": "Cross-fitted DML",
}
labelled = both.copy()
labelled["comparator_label"] = labelled.method.map(labels)
labelled.to_csv(root / "results/dml_comparators.csv", index=False)
fig, axes = plt.subplots(1, 2, figsize=(10, 5.4))
for ax, dgp, title in zip(
    axes,
    ["DGP1_nonlinear", "DGP2_sparse"],
    ["Nonlinear confounding (original)", "Sparse confounding (predeclared)"],
    strict=True,
):
    order = (
        ["OLS", "NaiveML", "NaivePlugin", "DML"]
        if dgp == "DGP1_nonlinear"
        else ["OLS", "NaivePlugin", "DML"]
    )
    table = both[both.dgp == dgp].set_index("method").loc[order]
    display = (
        ["OLS", "V1 in-sample\nnaive ML", "Linear Lasso\nplug-in", "Cross-fitted\nDML"]
        if len(order) == 4
        else ["OLS", "Linear Lasso\nplug-in", "Cross-fitted\nDML"]
    )
    ax.bar(
        display,
        table.bias,
        color=[PALETTE[["OLS", "NaiveML", "NaivePlugin", "DML"].index(name)] for name in order],
        yerr=1.96 * table.mc_se,
        capsize=4,
    )
    ax.axhline(0, color=".5", lw=0.7)
    ax.set(title=title, ylabel="Mean error against true effect = 1")
    ax.tick_params(axis="x", labelsize=8, rotation=0)
    for i, row in enumerate(table.itertuples()):
        ax.annotate(
            f"95% coverage: {100 * row.coverage:.0f}%",
            (i, row.bias),
            xytext=(0, 14),
            textcoords="offset points",
            ha="center",
            fontsize=8,
        )
    ax.margins(y=0.25)
fig.text(
    0.02,
    0.02,
    "100 repetitions each; bars: 95% Monte Carlo uncertainty for mean bias. Coverage is for effect confidence intervals.\nDGP1: boosting DML, linear Lasso plug-in; DGP2: Lasso nuisances. Original in-sample comparator retained.",
    fontsize=8,
)
fig.tight_layout(rect=(0, 0.12, 1, 1))
fig.savefig(figdir / "headline.png", dpi=300)
fig.savefig(figdir / "headline.pdf")
plt.close(fig)
fig, ax = plt.subplots(figsize=(9, 4))
positions = np.arange(len(pension))
ax.errorbar(
    pension.estimate / 1000,
    positions,
    xerr=np.vstack(
        [(pension.estimate - pension.lo95) / 1000, (pension.hi95 - pension.estimate) / 1000]
    ),
    fmt="o",
    capsize=4,
    color=PALETTE[0],
)
ax.axvline(0, color=".5", lw=0.6)
ax.set(
    yticks=positions,
    yticklabels=pension.model + " / " + pension.learner,
    xlabel="Net financial assets estimate (thousand 1990 USD)",
    title="401(k) eligibility: PLR coefficient vs IRM ATE",
)
fig.text(
    0.02,
    0.01,
    "95% intervals; unconfoundedness assumed; same stratified folds. Public SIPP extract via DoubleML; private retention.",  # noqa: E501
    fontsize=7,
)
fig.tight_layout(rect=(0, 0.06, 1, 1))
fig.savefig(figdir / "pension.png", dpi=300)
fig.savefig(figdir / "pension.pdf")
plt.close(fig)
event = pd.read_csv(root / "results/mpdta_event.csv")
fig, ax = plt.subplots(figsize=(8, 4))
ax.errorbar(
    event.event, event.estimate, yerr=1.96 * event.se, fmt="o-", capsize=4, color=PALETTE[0]
)
ax.axhline(0, color=".5", lw=0.7)
ax.axvline(-0.5, color=".5", lw=0.7)
ax.set(xlabel="Event time", ylabel="Log employment ATT", title="mpdta: CS dynamic aggregation")
fig.text(
    0.02,
    0.01,
    "County-cluster 95% pointwise intervals; universal baseline (-1 normalized). did package public example; author calculations.",  # noqa: E501
    fontsize=7,
)
fig.tight_layout(rect=(0, 0.07, 1, 1))
fig.savefig(figdir / "event_study.png", dpi=300)
fig.savefig(figdir / "event_study.pdf")
plt.close(fig)
if (root / "results/honestdid.csv").exists():
    h = pd.read_csv(root / "results/honestdid.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    mid = (h.lb + h.ub) / 2
    ax.errorbar(
        h.Mbar, mid, yerr=np.vstack([mid - h.lb, h.ub - mid]), fmt="o", capsize=4, color=PALETTE[1]
    )
    ax.axhline(0, color=".5", lw=0.7)
    ax.set(
        xlabel="Relative deviation bound Mbar",
        ylabel="Robust impact-ATT confidence set",
        title="HonestDiD: sensitivity to trend violations",
    )
    fig.text(
        0.02,
        0.01,
        "95% C-LF relative-magnitude sets; midpoint is graphical, not a point estimate. Sparse leads. did / HonestDiD.",  # noqa: E501
        fontsize=7,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(figdir / "honestdid.png", dpi=300)
    fig.savefig(figdir / "honestdid.pdf")
    plt.close(fig)
if (root / "results/income_group_ate.csv").exists():
    g = pd.read_csv(root / "results/income_group_ate.csv")
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.errorbar(
        g.income_quartile,
        g.estimate / 1000,
        yerr=1.96 * g.se / 1000,
        fmt="o",
        capsize=4,
        color=PALETTE[2],
    )
    ax.axhline(0, color=".5", lw=0.7)
    ax.set(
        xlabel="Held-out income quartile",
        ylabel="Eligibility group ATE (thousand USD)",
        title="Held-out AIPW income-group effects",
    )
    fig.text(
        0.02,
        0.01,
        "95% influence-score intervals; prespecified propensity clipping .01. Group ATEs, not forest-ranked GATES. SIPP/DoubleML.",  # noqa: E501
        fontsize=7,
    )
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    fig.savefig(figdir / "heterogeneity.png", dpi=300)
    fig.savefig(figdir / "heterogeneity.pdf")
    plt.close(fig)
if (root / "results/forest_blp.csv").exists():
    blp = pd.read_csv(root / "results/forest_blp.csv").iloc[0]
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.errorbar(
        [blp.estimate],
        [0],
        xerr=[[blp.estimate - blp.lo95], [blp.hi95 - blp.estimate]],
        fmt="o",
        capsize=4,
        color=PALETTE[0],
    )
    ax.axvline(0, color=".5", lw=0.7, label="No linear predictability")
    ax.axvline(1, color=".5", lw=0.7, ls="--", label="Unit calibration")
    ax.set(yticks=[], xlabel="BLP calibration slope", title="Held-out forest effect calibration")
    ax.legend(fontsize=8)
    fig.text(
        0.02,
        0.01,
        "95% HC1 interval; conditional on training-half forest/nuisance fits. SIPP/DoubleML.",
        fontsize=7,
    )
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    fig.savefig(figdir / "forest_blp.png", dpi=300)
    fig.savefig(figdir / "forest_blp.pdf")
    plt.close(fig)
r = did[did.method == "TWFE"].iloc[0]
cs = did[did.method == "CS"].iloc[0]
dml = mc[(mc.module == "DML") & (mc.method == "DML")].iloc[0]
naive = mc[(mc.module == "DML") & (mc.method == "NaiveML")].iloc[0]
rfin = pension[(pension.model == "IRM") & (pension.learner == "RF")].iloc[0]
sp = both.query('dgp=="DGP2_sparse" and method=="DML"').iloc[0]
plug = both.query('dgp=="DGP2_sparse" and method=="NaivePlugin"').iloc[0]
old_ols = mc.query('module=="DML" and method=="OLS"').iloc[0]
old_plugin = both.query('dgp=="DGP1_nonlinear" and method=="NaivePlugin"').iloc[0]
findings = [
    f"Original nonlinear design: V1 in-sample naive ML bias is {naive.bias:.3f}, versus {old_plugin.bias:.3f} for the linear Lasso plug-in; OLS bias is {old_ols.bias:.3f}, while cross-fitted DML bias is {dml.bias:.3f} with {100 * dml.coverage:.0f}% coverage.",
    f"With 200 candidate confounders, naive plug-in bias is {plug.bias:.3f} and coverage {100 * plug.coverage:.0f}%; cross-fitted DML bias is {sp.bias:.3f}, RMSE {sp.rmse:.3f} and coverage {100 * sp.coverage:.0f}%.",
    f"The unchanged retirement-account replication estimates ${rfin.estimate:,.0f} more net financial assets for eligible people (95% interval ${rfin.lo95:,.0f} to ${rfin.hi95:,.0f}), assuming measured controls remove confounding.",
]
(root / "results/findings.json").write_text(json.dumps(findings, indent=2))
(root / "results/findings.md").write_text("\n".join("- " + x for x in findings) + "\n")
for p in (root / "results").glob("*.csv"):
    t = pd.read_csv(p)
    lines = [
        "| " + " | ".join(t.columns) + " |",
        "| " + " | ".join(["---"] * len(t.columns)) + " |",
    ]
    lines += [
        "| " + " | ".join(map(str, row)) + " |" for row in t.itertuples(index=False, name=None)
    ]
    p.with_suffix(".md").write_text("\n".join(lines) + "\n")
(figdir / "linkedin").mkdir(exist_ok=True)
fig, axes = plt.subplots(2, 1, figsize=(4, 4), dpi=300)
plot_lo = min(0.0, float((both.bias - 1.96 * both.mc_se).min()))
plot_hi = max(0.0, float((both.bias + 1.96 * both.mc_se).max()))
plot_pad = 0.08 * (plot_hi - plot_lo)
short_labels = {
    "OLS": "OLS",
    "NaiveML": "V1 in-sample naive ML",
    "NaivePlugin": "Linear Lasso plug-in",
    "DML": "Cross-fitted DML",
}
for ax, design, title in zip(
    axes,
    ["DGP1_nonlinear", "DGP2_sparse"],
    ["Original nonlinear design", "Added sparse design"],
    strict=True,
):
    order = (
        ["OLS", "NaiveML", "NaivePlugin", "DML"]
        if design == "DGP1_nonlinear"
        else ["OLS", "NaivePlugin", "DML"]
    )
    table = both[both.dgp == design].set_index("method").loc[order]
    colors = [PALETTE[["OLS", "NaiveML", "NaivePlugin", "DML"].index(name)] for name in order]
    ax.barh(
        [short_labels[name] for name in order],
        table.bias,
        xerr=1.96 * table.mc_se,
        color=colors,
        capsize=2,
    )
    ax.axvline(0, color=".5", lw=0.6)
    ax.set_title(title, fontsize=9)
    ax.tick_params(labelsize=7)
    ax.invert_yaxis()
    ax.set_xlim(plot_lo - plot_pad, plot_hi + plot_pad)
    ax.set_xticks(np.arange(0.0, plot_hi + plot_pad, 0.2))
axes[1].set_xlabel("Mean error (true effect = 1)", fontsize=8)
fig.text(
    0.02,
    0.01,
    "100 seeded repetitions; 95% MC error bars. Original DGPs.\nDraft social asset; no new simulations.",
    fontsize=6,
)
fig.tight_layout(rect=(0, 0.09, 1, 1))
fig.savefig(figdir / "linkedin/headline.png", dpi=300)
plt.close(fig)
(figdir / "linkedin/summary.txt").write_text(" ".join(findings) + "\n")
question = "When can prediction-focused machine learning distort an estimated treatment effect, and does cross-fitting help?"
method = "We compare effect estimators in two seeded experiments where the true effect is known. We retain the original nonlinear design and add a predeclared sparse-confounding design with two hundred candidate controls and Lasso nuisance estimates to illustrate regularization bias under strong confounding. We measure bias, root mean squared error and confidence-interval coverage, alongside the unchanged public-data replication."
limitations = [
    "These illustrative designs do not establish universal estimator rankings.",
    "The nuisance learners and dimensions differ between designs.",
    "Naive plug-in intervals ignore nuisance-estimation uncertainty.",
    "A hundred repetitions give imprecise coverage estimates.",
    "The real-data estimate depends on untestable confounding assumptions.",
]
sparse = json.loads((root / "results/sparse_manifest.json").read_text())
old_ols = mc.query('module=="DML" and method=="OLS"').iloc[0]
technical = f"""DGP1 is preserved byte-for-byte in results/monte_carlo.csv:100 repetitions, n500,p20, nonlinear confounding, GradientBoosting60/depth2. OLS bias{old_ols.bias:.6f}, DML bias{dml.bias:.6f}, RMSE{dml.rmse:.6f}, coverage{dml.coverage:.2f}; original NaiveML bias{naive.bias:.6f}, coverage{naive.coverage:.2f}. That original NaiveML is an in-sample orthogonal residual score, not a nonorthogonal plug-in; its lower RMSE here is retained plainly. It is an extra row in results/dml_two_dgps.csv. The genuine joint-penalized plug-in was additionally declared before computation in docs/DGP1_PLUGIN_ADDENDUM.md, with original seeds and analytical penalty sqrt(2log20/500). Its linear nuisance is misspecified for DGP1.

DGP2 was committed before its first draw (docs/DGP2_PREDECLARATION.md):100 repetitions, n600,p200, five active independent Gaussian confounders, D=1.5 sum(X1..5)+V, Y=D+sum(X1..5)+U. Truth1, seed20261008+rep. Lasso penalty{sparse["alpha"]:.9f}=sqrt(2log200/600), max_iter10000,tol1e-7, no evaluation tuning. NaivePlugin fits a partially linear joint regression with unpenalized intercept/treatment and penalized nuisance slopes, implemented exactly by projecting Y and X off intercept/D before Lasso. Its moment uses D rather than the residualized treatment, so first-order nuisance bias persists. HC1 treats learned g as fixed and is deliberately naive; report empirical coverage, not valid nuisance-adjusted inference. DML uses five fixed shuffled folds, training-fold scaling and Lasso for E[Y|X],E[D|X], an orthogonal residual score and influence-score SE. OLS controls all200 correctly specified covariates with HC1. Model settings and DGP coefficients were not changed after viewing results.

DGP2 naive bias{plug.bias:.6f}, RMSE{plug.rmse:.6f}, coverage{plug.coverage:.2f}; DML bias{sp.bias:.6f}, RMSE{sp.rmse:.6f}, coverage{sp.coverage:.2f}. Coverage uncertainty uses Wilson binomial intervals (including nonzero upper bounds for zero successes), and bias uncertainty is Monte Carlo, not treatment-effect confidence bands. Results are illustrative: specification, learners and design dimensions differ, so this is not an isolated test of cross-fitting alone. The explicitly labelled results/dml_comparators.csv and companion Markdown identify both V1 in-sample naive ML and linear Lasso plug-in alongside OLS/DML; the numerical results/dml_two_dgps.csv is unchanged. All estimators, bias/RMSE/coverage and Monte Carlo standard errors are in the generated comparison table and source-bound sparse_manifest.json. Original simulation and pension/forest/DiD estimates are inherited without refitting in V2.

Real SIPP outcomes refer to1990 within the1991 public extract. Runtime DoubleML fetch only, private data and no redistribution; eligibility is not randomized and relies on conditional exogeneity/overlap. PLR coefficients are not necessarily ATEs; IRM estimates require their own assumptions. Common stratified folds are retained; IRM propensity clipping0.01 is declared. Forest held-out AIPW income groups have formal influence intervals, but average pointwise forest bounds do not create group CIs. BLP calibration is conditional on training-half fits. DiD compares treated-cell ATT on the same100 simulations; empirical CS population adjustment differs from unadjusted TWFE. Sparse pre-period leads limit HonestDiD sensitivity. Sun-Abraham is the approved dCDH fallback. No modern retirement policy or German regional wage causal claim is warranted.

References: Chernozhukov et al.(2018),10.1111/ectj.12097, https://www.nber.org/papers/w23564 ; DoubleML JMLR23(53); Callaway & Sant'Anna,arxiv1803.09015; Sun & Abraham,arxiv1804.05785; forest and HonestDiD primary references in DATA.md."""
sources = "Sources: original seeded simulations; public 1991 SIPP extract via DoubleML, private retention. Author calculations; results/dml_two_dgps.csv and unchanged pension.csv."
write_note(
    root,
    "Causal ML: prediction accuracy is not enough",
    question,
    method,
    findings,
    limitations,
    technical,
    sources,
)
(root / "README.md").write_text(
    "# causal-ml-lab\n\n"
    + question
    + "\n\n"
    + method
    + "\n\n![Headline](figures/headline.png)\n\n[Read the two-page policy note (PDF)](report/policy_note.pdf) · [Full technical report](report/report.md)\n\n## Findings\n\n"
    + "\n".join("- " + x for x in findings)
    + "\n\n## Reproduce\n\nInstall Python 3.11, uv, Git and R. `make setup all` uses repo-local Python/R environments and runtime public-data fetching. `make quick` is isolated and offline; `make test lint`. See [reproduction notes](docs/REPRODUCTION.md). Only V2 simulation: scripts/run_sparse.py. No API key, paid calls or raw redistribution.\n\n## Technical notes\n\n"
    + technical
    + "\n\n## Licence\n\nCode is MIT-licensed; third-party source data retain their original terms and are not included. Publication files and safety checks are documented in [docs/PUBLISH_CHECKLIST.md](docs/PUBLISH_CHECKLIST.md).\n\nHakan Zeki Gulmez | [GitHub](https://github.com/hakangulmez) | [LinkedIn](https://www.linkedin.com/in/hakan-zeki-g%C3%BClmez-088700180/)\n"
)
print(json.dumps(dict(findings=findings, pages_expected=2)))
