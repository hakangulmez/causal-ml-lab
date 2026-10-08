# ruff: noqa: E501, E402
"""Render fixed V3 aggregate results; no fitting, data refresh or paid calls."""

import hashlib
import json
import runpy
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from policy import write_note

root = Path(__file__).resolve().parents[1]
res = root / "results"
nl = pd.read_csv(res / "v3_nonlinear_mc.csv")
sp = pd.read_csv(res / "v3_sparse_mc.csv")
rd = pd.read_csv(res / "v3_r_did_mc.csv")
a = nl[nl.module == "DML"].copy()
a["dgp"] = "DGP1_nonlinear"
b = sp.copy()
b["dgp"] = "DGP2_sparse"
both = pd.concat([a, b], ignore_index=True)
both["comparator_label"] = both.method.map(
    {
        "OLS": "OLS",
        "NaiveML": "V1 in-sample naive ML (orthogonal)",
        "NaivePlugin": "Linear Lasso plug-in",
        "DML": "Cross-fitted DML",
    }
)
both.to_csv(res / "dml_two_dgps.csv", index=False)
both.to_csv(res / "dml_comparators.csv", index=False)
nl.to_csv(res / "monte_carlo.csv", index=False)
rd.to_csv(res / "did_monte_carlo.csv", index=False)
# Finite-sample estimates plus population algebra under the unchanged sparse design.
from causal_ml_lab.sparse import ALPHA

mechanism = dict(
    active=5,
    treatment_loading=1.5,
    var_signal=5.0,
    var_treatment=1 + 1.5**2 * 5,
    cov_treatment_signal=1.5 * 5,
    fixed_penalty=ALPHA,
)
mechanism["unadjusted_population_bias"] = (
    mechanism["cov_treatment_signal"] / mechanism["var_treatment"]
)
mechanism["projected_active_covariance"] = 1 / mechanism["var_treatment"]
plugin = both.query('dgp=="DGP2_sparse" and method=="NaivePlugin"').iloc[0]
mechanism["finite_sample_plugin_bias"] = plugin.bias
pd.DataFrame([mechanism]).to_csv(res / "v3_sparse_bias_mechanism.csv", index=False)
(res / "v3_sparse_bias_mechanism.json").write_text(json.dumps(mechanism, indent=2) + "\n")
# Reuse the established plots, then replace prose with V3 interpretation.
legacy = (root / "scripts/outputs.py").read_text()
legacy = (
    legacy[: legacy.index("rfin =")] if "rfin =" in legacy else legacy[: legacy.index("findings =")]
)
# Existing plots are presentation only; their actual counts replace historic constants.
legacy = legacy.replace(
    "100 seeded repetitions", f"{int(a.repetitions.iloc[0])} seeded repetitions"
).replace("100 repetitions", f"{int(a.repetitions.iloc[0])} repetitions")
exec(compile(legacy, str(root / "scripts/outputs.py"), "exec"), {"__name__": "__v3_render__"})
render = runpy.run_path(str(root / "report/technical/tables.py"))["render_headline"]
render(both, dict(true_effect=1, repetitions=int(b.repetitions.iloc[0])))
# Main figure and square preview match the result-bound technical headline.
from PIL import Image

Image.open(root / "figures/technical_headline.png").save(root / "figures/headline.png")
Image.open(root / "figures/headline.png").convert("RGB").save(
    root / "figures/headline.pdf", resolution=250
)
both.to_csv(res / "dml_comparators.csv", index=False)
fig, axes = plt.subplots(2, 1, figsize=(4, 4), dpi=300)
for ax, design in zip(axes, ["DGP1_nonlinear", "DGP2_sparse"], strict=True):
    t = both[both.dgp == design]
    ax.barh(t.comparator_label, t.bias, xerr=1.96 * t.mc_se, color="#0072B2")
    ax.axvline(0, color=".5")
    ax.tick_params(labelsize=6)
    ax.set_title(design, fontsize=8)
axes[1].set_xlabel("Mean error; 95% MC bars", fontsize=8)
fig.tight_layout()
fig.savefig(root / "figures/linkedin/headline.png", dpi=300)
plt.close(fig)
e = pd.read_csv(res / "mpdta_event.csv")
balanced = pd.read_csv(res / "v3_balanced_event.csv")
fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
for ax, t, title in zip(
    axes,
    [e, balanced],
    ["Original dynamic target", "Late-cohort balanced-window target"],
    strict=True,
):
    ax.errorbar(t.event, t.estimate, yerr=1.96 * t.se, fmt="o-", color="#0072B2", capsize=3)
    ax.axhline(0, color=".5")
    ax.set(title=title, xlabel="Event time", ylabel="Log employment effect")
    ax.set_xticks(t.event)
fig.tight_layout()
fig.savefig(root / "figures/v3_balanced_event.png", dpi=250)
plt.close(fig)
rf = pd.read_csv(res / "pension.csv").query('model=="IRM" and learner=="RF"').iloc[0]
ov = pd.read_csv(res / "v3_overlap.csv").query('learner=="RF"')
sens = pd.read_csv(res / "v3_rf_irm_sensitivity.csv").iloc[0]
dml = both.query('dgp=="DGP2_sparse" and method=="DML"').iloc[0]
naive = both.query('dgp=="DGP1_nonlinear" and method=="NaiveML"').iloc[0]
ndml = both.query('dgp=="DGP1_nonlinear" and method=="DML"').iloc[0]
findings = [
    f"In {int(dml.repetitions):,} sparse-design repetitions, linear Lasso plug-in bias is {plugin.bias:.3f}, versus {dml.bias:.3f} for cross-fitted DML; nominal 95% coverage is {100 * plugin.coverage:.1f}% versus {100 * dml.coverage:.1f}%.",
    f"The nonlinear design qualifies that message: in-sample orthogonal ML bias is {naive.bias:.3f}, versus {ndml.bias:.3f} for cross-fitted DML. These fixed learner/design comparisons do not establish universal DML superiority.",
    f"The historical RF–IRM estimate remains ${rf.estimate:,.0f}. No observations are trimmed; sensitivity RV is {100 * sens.RV:.2f}% and RVa {100 * sens.RVa:.2f}% under the specified adversarial confounding model, not proof of no confounding.",
]
future = "Matched-learner, scaling, oracle and fold factorials; denser/correlated or p>=n DGPs and heteroskedastic inference; fuller Monte Carlo uncertainty for RMSE and average estimated SE; nuisance-score concentration and observed-confounding benchmarks; clipping-grid/repeated-split/DAG-control sensitivity; alternative historical wealth outcomes and transportability; income-quartile contrasts and forest-ranked groups; estimator comparisons with identical covariates; new balanced-target HonestDiD sensitivity and pretrend-power studies; observational continuous-dose identification. These substantive review extensions are deferred, with no new tuning or target changes."
technical = f"""V3 protocol: docs/V3_PROTOCOL.md. Required frozen V2 aggregate fixtures: versions/v2-2026-10-07/; full private archive is not distributed. New Monte Carlos preserve DGPs, penalties, sample sizes, estimator/fold settings and seed sequences. Each of three separately allocated ten-minute blocks completed 1000 matched repetitions: old100 reused only after seed/draw verification and deterministic endpoint replays, new900 executed. Python nonlinear block includes its associated Python DiD runner; Python and R draws are not pooled. Checkpoints remain private. Fit failures, runtimes, counts and stop rules are exported in results/v3_*mc_manifest.json. Coverage MCSE=sqrt(p(1-p)/R), with Wilson95 intervals; MCSE zero at endpoints is not certainty.

SIPP three IRM refits recover raw out-of-fold probabilities from fitted objects with original folds/learners. RF estimate unchanged; Lasso numerical difference only (results/v3_irm_refit_comparison.csv). RF clips {int(ov.clipped_count.sum())}/{int(ov.n.sum())} predictions; removes0 observations. IPW ESS=(sum w)^2/sum(w^2), w=1/m_clip treated,1/(1-m_clip) controls; RF treated ESS={ov[ov.arm == 1].ESS_clipped.iloc[0]:.3f}, controls={ov[ov.arm == 0].ESS_clipped.iloc[0]:.3f}. Raw distributions and all learner/arm counts are shown separately. Clipping is not trimming. IPW ESS is a weight-concentration diagnostic; it does not include propensity-estimation uncertainty and is not a measure of causal validity.

DoubleML sensitivity for RF–IRM ATE uses the fixed16-pair grid cf_y,cf_d in .01,.03,.05,.10;rho1,95% level,null0. cf_y is the share of outcome residual variance attributable to latent confounding; IRM cf_d is a relative gain in average conditional treatment precision/Riesz variance, not the PLR treatment R-squared. RV equal-strength effect-bound threshold={sens.RV:.6f}, RVa confidence-bound threshold={sens.RVa:.6f}. Confidence endpoints are 95% one-sided limits on effect bounds. The exercise presumes this confounding model and is no proof of exchangeability. Definitions: https://docs.doubleml.org/stable/guide/sensitivity.html .

Late-cohort balanced-window comparison retains cohorts2006/2007 and events-2,-1,0; weights fixed by cohort size, never-treated controls and unchanged ATT(g,t) fits. Influence functions form constant-weight contrasts against-1. It targets a different cohort/window population than the original dynamic analysis. Original HonestDiD results apply only to the original estimand/composition. balance_e concerns post-treatment exposure, not proof of balanced pre-treatment support (official did aggte documentation). Income-quartile groups preserve their estimates: the V3 rule is right-closed pandas qcut4 on the original held-out income sample; cutoffs are empirically computed, not retrospectively pre-specified numeric thresholds or forest-discovered groups.

Sparse treatment loading1.5 makes treatment correlated with the five confounders. The plug-in projects Y and X off intercept/treatment before fixed-penalty Lasso. Population projected active covariance={mechanism["projected_active_covariance"]:.6f} is below the unchanged penalty={ALPHA:.6f}; shrinkage can omit the confounder signal and return omitted-confounder bias near the unadjusted population value={mechanism["unadjusted_population_bias"]:.6f}. Actual finite-sample plug-in bias={plugin.bias:.6f}. This algebra explains the declared design, not a universal ranking. No penalty was changed.

Inherited pension/forest/groups/MPDTA/HonestDiD/dose estimates remain in original files; V3 adds diagnostics, precision and the balanced estimand. All raw rows, probability predictions and fitted objects remain private; no paid provider calls or private-data redistribution.
"""
write_note(
    root,
    "Causal ML: shrinkage and identification",
    "When can regularization distort a treatment effect, and what assumptions remain?",
    "We compare unchanged estimators in two fixed simulations with known effects. We increase Monte Carlo precision and add overlap and confounding-sensitivity diagnostics to the historical SIPP replication. We retain the original staggered-adoption analysis and add a narrowly supported, balanced late-cohort window.",
    findings,
    [
        "Designs and learner families differ; rankings are not universal.",
        "IPW ESS measures weight concentration, not causal validity or propensity-estimation uncertainty.",
        "Historical eligibility is not randomized or modern policy participation.",
        "Balanced and full-sample event studies target different cohorts/windows.",
        "Effect and group inference conditions on fitted nuisance structures.",
    ],
    technical + "\n\nLimitations and future work: " + future,
    "Sources: fixed seeded experiments; private public-SIPP/MPDTA retention. Aggregate V3 CSVs and inherited pension.csv.",
)
(res / "findings.json").write_text(json.dumps(findings, indent=2) + "\n")
(res / "findings.md").write_text("\n".join("- " + f for f in findings) + "\n")
(root / "figures/linkedin/summary.txt").write_text(" ".join(findings) + "\n")
(root / "README.md").write_text(
    "# causal-ml-lab\n\nWhen can regularization distort a treatment effect, and what assumptions remain?\n\n![Headline](figures/headline.png)\n\n[Two-page policy note](report/policy_note.pdf) · [Technical working paper](report/technical_report.pdf) · [Full results and assumptions](report/report.md)\n\n## Findings\n\n"
    + "\n".join("- " + f for f in findings)
    + "\n\n## Reproduce\n\n`make setup`; V3 requires the existing frozen local inputs. `make v3-diagnostics`, `make v3-mc`, `make v3-balanced`, then `make v3-outputs report`. Do not rerun Monte Carlos outside the predeclared budgets. `make quick` is isolated and offline; `make test lint`. Code MIT; data sources via scripts and DATA.md only. No source observations or fitted objects in git.\n\n## Technical notes\n\n"
    + technical
    + "\n\n## Limitations and future work\n\n"
    + future
    + "\n\nHakan Zeki Gülmez | [GitHub](https://github.com/hakangulmez) | [LinkedIn](https://www.linkedin.com/in/hakan-zeki-g%C3%BClmez-088700180/)\n"
)
inputs = [
    "dml_comparators.csv",
    "pension.csv",
    "v3_overlap.csv",
    "v3_rf_irm_sensitivity.csv",
    "v3_balanced_event.csv",
    "v3_sparse_bias_mechanism.json",
]
(res / "policy_note_lineage.json").write_text(
    json.dumps(
        dict(
            inputs={n: hashlib.sha256((res / n).read_bytes()).hexdigest() for n in inputs},
            render_only=True,
        ),
        indent=2,
    )
    + "\n"
)
for name in inputs:
    if name.endswith(".csv"):
        t = pd.read_csv(res / name)
        (res / Path(name).with_suffix(".md")).write_text(
            "\n".join(
                [
                    "| " + " | ".join(t.columns) + " |",
                    "| " + " | ".join(["---"] * len(t.columns)) + " |",
                ]
                + [
                    "| " + " | ".join(map(str, x)) + " |"
                    for x in t.itertuples(index=False, name=None)
                ]
            )
            + "\n"
        )
print(json.dumps(findings))

# Publication-only reproduction description; estimator sources remain unchanged.
p = root / "README.md"
s = p.read_text()
start, end = s.index("## Reproduce"), s.index("## Technical notes")
p.write_text(
    s[:start]
    + "## Reproduce\n\n`make setup test lint quick` validates the implementations; `make policy-note report` rebuilds accepted V3 reports from included aggregate tables. Tectonic is required for the working paper; Python 3.11 and R (C1) for the full checks. See [reproduction notes](docs/REPRODUCTION.md) for the separate legacy empirical pipeline, free source access, credentials, and limits on reconstructing private V3 checkpoint histories. Data are acquired only through scripts and DATA.md; no raw observations are included. Original code is MIT.\n\n"
    + s[end:]
)
