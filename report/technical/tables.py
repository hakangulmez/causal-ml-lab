# ruff: noqa: E501
"""CSV-backed scientific tables; no model fitting or raw-data reads."""


def generate(csv, js, macro, table, fmt):
    contract = js("technical_model_contract.json")
    macro("SIPPExtractYear", contract["sipp_extract_year"])
    macro("SIPPYear", contract["sipp_measurement_year"])
    for key, field in [("OriginalN", "n"), ("OriginalP", "p")]:
        macro(key, contract["dgp1"][field])
    macro("OriginalTrees", contract["dgp1_learner"]["n_estimators"])
    macro("OriginalDepth", contract["dgp1_learner"]["max_depth"])
    macro("RPanelN", contract["r_did"]["n"])
    macro("PythonPanelN", contract["python_did"]["n"])
    macro("SparseIterations", contract["sparse_solver"]["max_iter"])
    macro("SparseTolerance", contract["sparse_solver"]["tol"])
    s = js("manifest.json")
    sp = js("sparse_manifest.json")
    r = js("r_manifest.json")
    macro("SampleN", s["n_sipp"])
    macro("Folds", s["folds"])
    macro("Seed", s["seed"])
    macro("SparseN", sp["n"])
    macro("SparseP", sp["p"])
    macro("ActiveP", sp["sparsity"])
    macro("Replications", js("v3_sparse_mc_manifest.json")["completed_repetitions"])
    macro("SparseAlpha", sp["alpha"], 6)
    macro("SparseSeed", sp["seed"])
    macro("TrueEffect", sp["true_effect"], 0)
    mc = csv("dml_comparators.csv")
    mc["comparator_label"] = mc.method.map(
        {
            "OLS": "OLS",
            "NaiveML": "In-sample orthogonal ML",
            "NaivePlugin": "Linear Lasso plug-in",
            "DML": "Cross-fitted DML",
        }
    )
    render_headline(mc, dict(sp, repetitions=int(mc.repetitions.iloc[0])))
    pen = csv("pension.csv")
    mp = csv("mpdta_group_time.csv")
    did = csv("did_monte_carlo.csv")
    macro("MPRows", r["mpdta_rows"])
    macro("MPStart", int(mp.time.min()))
    macro("MPEnd", int(mp.time.max()))
    macro("Clip", pen.propensity_clipping.dropna().iloc[0], 2)
    for pre, dgp, method in [
        ("OriginalNaive", "DGP1_nonlinear", "NaiveML"),
        ("OriginalPlugin", "DGP1_nonlinear", "NaivePlugin"),
        ("OriginalDML", "DGP1_nonlinear", "DML"),
        ("SparsePlugin", "DGP2_sparse", "NaivePlugin"),
        ("SparseDML", "DGP2_sparse", "DML"),
    ]:
        a = mc[(mc.dgp == dgp) & (mc.method == method)].iloc[0]
        macro(pre + "Bias", a.bias, 3)
        macro(pre + "RMSE", a.rmse, 3)
        macro(pre + "Coverage", 100 * a.coverage, 0)
    a = pen[(pen.model == "IRM") & (pen.learner == "RF")].iloc[0]
    for suffix, col in [("Point", "estimate"), ("Low", "lo95"), ("High", "hi95")]:
        macro("Pension" + suffix, a[col], 0)
    rows = [
        [
            "Y: net financial assets",
            "Public SIPP extract; net_tfa",
            "Level, historical USD",
            str(s["n_sipp"]) + " persons",
        ],
        ["D: eligibility", "Same extract; e401", "Binary; not participation", "Same sample"],
        [
            "X: continuous",
            "age, inc, educ, fsize",
            "Levels; train-fold scaling for linear learner",
            "Same sample",
        ],
        ["X: indicators", "marr, twoearn, db, pira, hown", "As supplied", "Same sample"],
        [
            "Panel outcome",
            "County panel; lemp",
            "Log teen employment",
            str(int(mp.time.min())) + "–" + str(int(mp.time.max())),
        ],
        [
            "Adoption / adjustment",
            "mpdta: first.treat, lpop",
            "Cohort year / log population",
            str(r["mpdta_rows"]) + " county-year rows",
        ],
        [
            "Simulation variables",
            "Author-constructed simulations",
            "Gaussian confounding; known potential outcomes",
            "Seeded Monte Carlo designs",
        ],
        [
            "Dose example",
            "Author-constructed dose design",
            "Dose-specific effect and derivative",
            "Original synthetic draw",
        ],
    ]
    table(
        "data",
        ["Variable", "Source / ID", "Transformation", "Sample"],
        rows,
        "Analysis inputs and estimand-defining variables",
        (
            "Sources: results/manifest.json, r_manifest.json, pension.csv, "
            "mpdta_group_time.csv. Historical SIPP measurements refer to the extract "
            "described in DATA.md; no raw rows are included."
        ),
        layout="p{0.20\\linewidth}p{0.31\\linewidth}p{0.27\\linewidth}X",
        size="footnotesize",
    )
    rows = []
    for dgp in ["DGP1_nonlinear", "DGP2_sparse"]:
        for method in ["OLS", "NaiveML", "NaivePlugin", "DML"]:
            a = mc[(mc.dgp == dgp) & (mc.method == method)]
            if a.empty:
                continue
            a = a.iloc[0]
            rows.append(
                [
                    dgp.replace("DGP1_nonlinear", "Nonlinear").replace("DGP2_sparse", "Sparse"),
                    a.comparator_label,
                    fmt(a.bias),
                    fmt(a.rmse),
                    fmt(a.mc_se),
                    fmt(a.coverage, 2),
                    f"[{fmt(a.coverage_lo95, 4)}, {fmt(a.coverage_hi95, 4)}]",
                ]
            )
    table(
        "simulation",
        ["Design", "Estimator", "Bias", "RMSE", "MC SE", "Coverage", "Wilson 95%"],
        rows,
        "Estimator performance in both declared Monte Carlo designs",
        (
            "Source: author's calculations from the documented inputs. "
            "Coverage refers to nominal 95% "
            "treatment-effect intervals; MC SE is the standard error of mean bias across"
            " repetitions. Wilson intervals quantify uncertainty in estimated coverage, "
            "not treatment effects."
        ),
        layout="lp{0.26\\linewidth}rrrrX",
        size="footnotesize",
    )
    table(
        "pension",
        ["Estimator", "Nuisance", "Estimate", "SE", "Lower 95%", "Upper 95%"],
        [
            [a.model, a.learner, fmt(a.estimate, 0), fmt(a.se, 0), fmt(a.lo95, 0), fmt(a.hi95, 0)]
            for _, a in pen.iterrows()
        ],
        "Historical eligibility and net financial assets",
        (
            "Source: author's calculations from the documented inputs. "
            "USD outcome units; PLR and IRM do not "
            "generally identify the same functional under heterogeneous effects. OLS "
            "uses HC1; PLR/IRM use score-based normal intervals."
        ),
        layout="Xlrrrr",
    )
    table(
        "did_mc",
        ["Estimator", "Repetitions", "Bias", "RMSE", "MC SE", "Coverage"],
        [
            [
                a.method,
                int(a.repetitions),
                fmt(a.bias),
                fmt(a.rmse),
                fmt(a.mc_se),
                fmt(a.coverage, 2),
            ]
            for _, a in did.iterrows()
        ],
        "Staggered-adoption simulations with the same treated-cell ATT target",
        (
            "Source: results/did_monte_carlo.csv; R simulation. Unit-cluster inference "
            "for TWFE/Sun–Abraham; analytic influence inference for CS. Python Monte "
            "Carlo is a distinct saved checkpoint, not pooled here."
        ),
        layout="Xrrrrr",
    )
    a = csv("mpdta_estimates.csv")
    table(
        "mpdta",
        ["Estimator", "Estimate", "SE", "Lower 95%", "Upper 95%"],
        [
            [v.method, fmt(v.estimate, 4), fmt(v.se, 4), fmt(v.lo95, 4), fmt(v.hi95, 4)]
            for _, v in a.iterrows()
        ],
        "County teen-employment application",
        (
            "Source: author's calculations from the documented inputs. "
            "Log-employment units. CS conditions on"
            " log population; TWFE is unadjusted, so comparison also changes adjustment "
            "and aggregation."
        ),
        layout="Xrrrr",
    )
    forest = csv("forest_blp.csv")
    groups = csv("income_group_ate.csv")
    macro("HoldoutN", int(forest.n.iloc[0]))
    macro("BLPPoint", forest.estimate.iloc[0], 3)
    macro("BLPLow", forest.lo95.iloc[0], 3)
    macro("BLPHigh", forest.hi95.iloc[0], 3)
    table(
        "groups",
        ["Income quartile", "Holdout n", "ATE", "SE", "Lower 95%", "Upper 95%"],
        [
            [
                int(a.income_quartile),
                int(a.n),
                fmt(a.estimate, 0),
                fmt(a.se, 0),
                fmt(a.lo95, 0),
                fmt(a.hi95, 0),
            ]
            for _, a in groups.iterrows()
        ],
        "Held-out orthogonal income-quartile-group effects",
        (
            "Source: author's calculations from the documented inputs. "
            "Groups are income quartiles of the "
            "held-out sample; they are not forest-ranked GATES. Influence intervals "
            "condition on training-half nuisance fits."
        ),
        layout="Xrrrrr",
    )
    h = csv("honestdid.csv")
    table(
        "honest",
        ["M-bar", "Lower", "Upper", "Method", "Restriction"],
        [[fmt(a.Mbar, 1), fmt(a.lb, 4), fmt(a.ub, 4), a.method, a.Delta] for _, a in h.iterrows()],
        "Sensitivity of the impact-event ATT to relative pretrend violations",
        (
            "Source: results/honestdid.csv; HonestDiD relative-magnitude restriction, "
            "impact contrast, nominal 95% bounds. Sparse usable leads limit "
            "informativeness."
        ),
        layout="Xrrll",
    )
    cont = csv("continuous.csv")
    table(
        "continuous",
        ["Dose quartile", "n", "Mean dose", "ATT", "SE(ATT)", "ACRT", "SE(ACRT)"],
        [
            [
                int(a.dose_quartile),
                int(a.n),
                fmt(a.mean_dose),
                fmt(a.ATT),
                fmt(a.ATT_se),
                fmt(a.ACRT),
                fmt(a.ACRT_se),
            ]
            for _, a in cont.iterrows()
        ],
        "Known effects and derivatives in the dose-selection illustration",
        (
            "Source: author's calculations from the documented inputs. "
            "Descriptive means of known synthetic "
            "potential outcomes, with sample-mean SEs; no causal effect has been "
            "estimated from observational dose variation."
        ),
        layout="Xrrrrrr",
        size="footnotesize",
    )
    robust = [
        [
            "DML comparators",
            "OLS; in-sample orthogonal ML; genuine Lasso plug-in; cross-fitted DML",
            "Both original and sparse designs retained",
        ],
        [
            "Nuisance families",
            "Linear/Lasso, random forest, gradient boosting",
            "PLR and IRM side-by-side; common folds",
        ],
        ["DiD estimator", "TWFE; CS; Sun–Abraham", "Sun–Abraham; dCDH could not be installed"],
        [
            "DiD adjustment",
            "Unadjusted TWFE; population-adjusted CS",
            "Not a like-for-like estimator-only contrast",
        ],
        [
            "Sensitivity",
            "HonestDiD relative-magnitude grid",
            "Impact contrast and saved covariance",
        ],
        [
            "Heterogeneity",
            "Forest averages; held-out AIPW groups; BLP",
            "Pointwise forest bounds are not group intervals",
        ],
        ["Dose estimand", "ATT(d) versus ACRT(d)", "Known synthetic illustration only"],
        [
            "Data preprocessing",
            "Raw covariates; native dtype restoration",
            "No winsorization, row deletion or polynomial expansion",
        ],
        [
            "Overlap / inference",
            "Fixed propensity clipping; analytic score SEs",
            "No clipping sensitivity or repeated-split run performed",
        ],
    ]
    table(
        "robustness",
        ["Declared alternative", "Specification", "Interpretation"],
        robust,
        "Alternative specifications and inference",
        ("Source: comparative estimates under the stated nuisance and inference specifications."),
        layout="p{0.22\\linewidth}p{0.40\\linewidth}X",
        size="footnotesize",
    )
    event = csv("mpdta_event.csv")
    table(
        "event",
        ["Event time", "Estimate", "SE", "Lower 95%", "Upper 95%"],
        [
            [int(a.event), fmt(a.estimate, 4), fmt(a.se, 4), fmt(a.lo95, 4), fmt(a.hi95, 4)]
            for _, a in event.iterrows()
        ],
        "Saved dynamic DiD estimates and sparse pre-period evidence",
        (
            "Source: author's calculations from the documented inputs. "
            "The normalized reference period has no "
            "estimated interval. All saved leads/lags are shown; no extra event window "
            "was fitted."
        ),
        layout="Xrrrr",
    )
    b = csv("bacon.csv")
    agg = b.groupby("type", sort=False).apply(
        lambda x: (x.weight.sum(), (x.weight * x.estimate).sum()), include_groups=False
    )
    table(
        "bacon",
        ["Comparison class", "Weight sum", "Contribution"],
        [[key, fmt(values[0], 4), fmt(values[1], 4)] for key, values in agg.items()],
        "Goodman–Bacon accounting by comparison class",
        (
            "Source: results/bacon.csv; contributions are weighted component estimates, "
            "not new regressions. Already-treated comparisons remain visible. Positive "
            "component weights do not rule out negative implicit treatment-effect "
            "weights."
        ),
        layout="Xrr",
    )
    table(
        "mc_uncertainty",
        ["Design", "Estimator", "Coverage MC SE", "Bias MC SE"],
        [
            [
                a.dgp.replace("DGP1_nonlinear", "Nonlinear").replace("DGP2_sparse", "Sparse"),
                a.comparator_label,
                fmt(a.coverage_mc_se, 4),
                fmt(a.mc_se, 4),
            ]
            for _, a in mc.iterrows()
        ],
        "Monte Carlo uncertainty and comparator labels",
        (
            "Source: author's calculations from the documented inputs. "
            "A zero binomial plug-in SE at zero "
            "coverage is not certainty: use the nonzero Wilson upper endpoint in the "
            "main table."
        ),
        layout="Xp{0.31\\linewidth}rr",
        size="footnotesize",
    )

    overlap = csv("v3_overlap.csv")
    sensitivity = csv("v3_rf_irm_sensitivity.csv")
    balanced = csv("v3_balanced_event.csv")
    weights = csv("v3_balanced_cohort_weights.csv")
    support = csv("v3_cohort_event_support.csv")
    mechanism = js("v3_sparse_bias_mechanism.json")
    for name, key in [
        ("PopulationBias", "unadjusted_population_bias"),
        ("ProjectedCovariance", "projected_active_covariance"),
        ("MechanismPenalty", "fixed_penalty"),
    ]:
        macro(name, mechanism[key], 6)
    refits = csv("v3_irm_refit_comparison.csv")
    macro("LassoRefitDifference", refits[refits.learner == "Lasso"].estimate_difference.iloc[0], 9)
    macro("SensitivityRV", 100 * sensitivity.RV.iloc[0], 3)
    macro("SensitivityRVa", 100 * sensitivity.RVa.iloc[0], 3)
    table(
        "overlap",
        ["Learner", "Arm", "n", "Clipped", "Share", "Removed", "IPW ESS"],
        [
            [
                a.learner,
                "Control" if a.arm == 0 else "Treatment",
                int(a.n),
                int(a.clipped_count),
                fmt(a.clipped_share, 4),
                int(a.observations_removed),
                fmt(a.ESS_clipped, 1),
            ]
            for _, a in overlap.iterrows()
        ],
        "Raw out-of-fold propensity clipping and arm-specific effective sample sizes",
        "Source: v3_overlap.csv; thresholds0.01/0.99. No observation trimming. Weights1/m clipped for treatment,1/(1-m clipped) controls. ESS: squared sum of weights divided by sum of squared weights. Raw-probability ESS also exported; no score normalization is implied.",
        layout="Xlrrrrr",
        size="footnotesize",
    )
    table(
        "sipp_sensitivity",
        ["cf y", "cf d", "Effect lower", "Effect upper", "Conf. lower", "Conf. upper"],
        [
            [
                fmt(a.cf_y, 2),
                fmt(a.cf_d, 2),
                fmt(a.effect_lower, 0),
                fmt(a.effect_upper, 0),
                fmt(a.confidence_lower, 0),
                fmt(a.confidence_upper, 0),
            ]
            for _, a in sensitivity.iterrows()
        ],
        "RF–IRM sensitivity over the entire fixed confounding grid",
        "Source: v3_rf_irm_sensitivity.csv. rho1,95% one-sided confidence endpoints for effect bounds,null0,historical USD. RV="
        + fmt(sensitivity.RV.iloc[0], 6)
        + ", RVa="
        + fmt(sensitivity.RVa.iloc[0], 6)
        + ". Parameters refer to latent outcome variation and the relative gain in average conditional treatment precision; they are not proof of absence of confounding.",
        layout="rrrrrr",
        size="footnotesize",
    )
    table(
        "balanced",
        ["Event", "Estimate", "SE", "Lower95%", "Upper95%"],
        [
            [int(a.event), fmt(a.estimate, 4), fmt(a.se, 4), fmt(a.lo95, 4), fmt(a.hi95, 4)]
            for _, a in balanced.iterrows()
        ],
        "Late-cohort, balanced-window comparison with reference event minus one",
        "Source: v3_balanced_event.csv. Cohorts2006/2007,events-2,-1,0;never-treated controls,unchanged population-adjusted ATT(g,t),constant cohort-size weights. Different target from original dynamic analysis; its HonestDiD bounds are not transferred.",
        layout="Xrrrr",
        size="footnotesize",
    )
    table(
        "balanced_weights",
        list(weights.columns),
        weights.values.tolist(),
        "Included cohorts, fixed weights and event support",
        "Source: v3_balanced_cohort_weights.csv; support matrix is exported before aggregation. Full row-level influence functions remain private.",
        size="footnotesize",
    )
    table(
        "cohort_support",
        list(support.columns),
        support.values.tolist(),
        "Cohort-by-event-time support before balanced aggregation",
        "Source: v3_cohort_event_support.csv; non-existing event cells are unsupported, not fabricated. The balanced comparison uses only2006/2007 at-2,-1,0. balance_e concerns post-treatment exposure,not balanced pre-treatment support.",
        size="footnotesize",
    )

    dmc = csv("v3_nonlinear_mc.csv")
    dmc = dmc[dmc.module == "DiD"]
    rmc = csv("v3_r_did_mc.csv")
    table(
        "did_mc_uncertainty",
        ["Engine", "Estimator", "R", "Coverage MCSE", "Wilson95%"],
        [
            [
                engine,
                a.method,
                int(a.repetitions),
                fmt(a.coverage_mc_se, 4),
                "[" + fmt(a.coverage_lo95, 4) + "," + fmt(a.coverage_hi95, 4) + "]",
            ]
            for engine, frame in [("Python", dmc), ("R", rmc)]
            for _, a in frame.iterrows()
        ],
        "DiD Monte Carlo coverage uncertainty at actual completed counts",
        "Source: v3_nonlinear_mc.csv and v3_r_did_mc.csv. Python CS has no interval in its original implementation, so coverage is unreported. Zero endpoint MCSE is not certainty; engines use separate seeded draws.",
        layout="Xlr rX",
        size="footnotesize",
    )


def render_headline(frame, sparse_manifest):
    """Present the same bias, MC uncertainty and coverage with neutral labels."""
    from pathlib import Path

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    root = Path(__file__).resolve().parents[2]
    palette = ["#0072B2", "#E69F00", "#009E73", "#D55E00"]
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 11,
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    fig, axes = plt.subplots(1, 2, figsize=(10, 5.4))
    for ax, dgp, title in zip(
        axes,
        ["DGP1_nonlinear", "DGP2_sparse"],
        ["Nonlinear confounding", "Sparse confounding"],
        strict=True,
    ):
        order = (
            ["OLS", "NaiveML", "NaivePlugin", "DML"]
            if dgp == "DGP1_nonlinear"
            else ["OLS", "NaivePlugin", "DML"]
        )
        values = frame[frame.dgp == dgp].set_index("method").loc[order]
        labels = {
            "OLS": "OLS",
            "NaiveML": "In-sample\northogonal ML",
            "NaivePlugin": "Linear Lasso\nplug-in",
            "DML": "Cross-fitted\nDML",
        }
        ax.bar(
            [labels[k] for k in order],
            values.bias,
            color=[palette[["OLS", "NaiveML", "NaivePlugin", "DML"].index(k)] for k in order],
            yerr=1.96 * values.mc_se,
            capsize=4,
        )
        ax.axhline(0, color=".5", lw=0.7)
        ax.set(
            title=title, ylabel=f"Mean error against true effect = {sparse_manifest['true_effect']}"
        )
        ax.tick_params(axis="x", labelsize=8)
        for i, row in enumerate(values.itertuples()):
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
        f"{sparse_manifest['repetitions']} repetitions per design; "
        "bars: 95% Monte Carlo intervals for mean bias.\n"
        "Coverage describes effect intervals. Nonlinear design: boosting nuisances; "
        "sparse design: Lasso nuisances.",
        fontsize=8,
    )
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    (root / "figures").mkdir(exist_ok=True)
    fig.savefig(root / "figures/technical_headline.png", dpi=300)
    plt.close(fig)
