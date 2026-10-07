# causal-ml-lab

When can prediction-focused machine learning distort an estimated treatment effect, and does cross-fitting help?

We compare effect estimators in two seeded experiments where the true effect is known. We retain the original nonlinear design and add a predeclared sparse-confounding design with two hundred candidate controls and Lasso nuisance estimates to illustrate regularization bias under strong confounding. We measure bias, root mean squared error and confidence-interval coverage, alongside the unchanged public-data replication.

![Headline](figures/headline.png)

[Read the two-page policy note (PDF)](report/policy_note.pdf) · [Full technical report](report/report.md)

## Findings

- Original nonlinear design: V1 in-sample naive ML bias is 0.008, versus 0.600 for the linear Lasso plug-in; OLS bias is 0.642, while cross-fitted DML bias is 0.040 with 94% coverage.
- With 200 candidate confounders, naive plug-in bias is 0.609 and coverage 0%; cross-fitted DML bias is 0.003, RMSE 0.042 and coverage 94%.
- The unchanged retirement-account replication estimates $8,172 more net financial assets for eligible people (95% interval $5,795 to $10,549), assuming measured controls remove confounding.

## Reproduce

Install Python 3.11, uv, Git and R. `make setup all` uses repo-local Python/R environments and runtime public-data fetching. `make quick` is isolated and offline; `make test lint`. See [reproduction notes](docs/REPRODUCTION.md). Only V2 simulation: scripts/run_sparse.py. No API key, paid calls or raw redistribution.

## Technical notes

DGP1 is preserved byte-for-byte in results/monte_carlo.csv:100 repetitions, n500,p20, nonlinear confounding, GradientBoosting60/depth2. OLS bias0.642348, DML bias0.040398, RMSE0.072501, coverage0.94; original NaiveML bias0.007698, coverage0.93. That original NaiveML is an in-sample orthogonal residual score, not a nonorthogonal plug-in; its lower RMSE here is retained plainly. It is an extra row in results/dml_two_dgps.csv. The genuine joint-penalized plug-in was additionally declared before computation in docs/DGP1_PLUGIN_ADDENDUM.md, with original seeds and analytical penalty sqrt(2log20/500). Its linear nuisance is misspecified for DGP1.

DGP2 was committed before its first draw (docs/DGP2_PREDECLARATION.md):100 repetitions, n600,p200, five active independent Gaussian confounders, D=1.5 sum(X1..5)+V, Y=D+sum(X1..5)+U. Truth1, seed20261008+rep. Lasso penalty0.132894913=sqrt(2log200/600), max_iter10000,tol1e-7, no evaluation tuning. NaivePlugin fits a partially linear joint regression with unpenalized intercept/treatment and penalized nuisance slopes, implemented exactly by projecting Y and X off intercept/D before Lasso. Its moment uses D rather than the residualized treatment, so first-order nuisance bias persists. HC1 treats learned g as fixed and is deliberately naive; report empirical coverage, not valid nuisance-adjusted inference. DML uses five fixed shuffled folds, training-fold scaling and Lasso for E[Y|X],E[D|X], an orthogonal residual score and influence-score SE. OLS controls all200 correctly specified covariates with HC1. Model settings and DGP coefficients were not changed after viewing results.

DGP2 naive bias0.608658, RMSE0.608810, coverage0.00; DML bias0.003207, RMSE0.041532, coverage0.94. Coverage uncertainty uses Wilson binomial intervals (including nonzero upper bounds for zero successes), and bias uncertainty is Monte Carlo, not treatment-effect confidence bands. Results are illustrative: specification, learners and design dimensions differ, so this is not an isolated test of cross-fitting alone. The explicitly labelled results/dml_comparators.csv and companion Markdown identify both V1 in-sample naive ML and linear Lasso plug-in alongside OLS/DML; the numerical results/dml_two_dgps.csv is unchanged. All estimators, bias/RMSE/coverage and Monte Carlo standard errors are in the generated comparison table and source-bound sparse_manifest.json. Original simulation and pension/forest/DiD estimates are inherited without refitting in V2.

Real SIPP outcomes refer to1990 within the1991 public extract. Runtime DoubleML fetch only, private data and no redistribution; eligibility is not randomized and relies on conditional exogeneity/overlap. PLR coefficients are not necessarily ATEs; IRM estimates require their own assumptions. Common stratified folds are retained; IRM propensity clipping0.01 is declared. Forest held-out AIPW income groups have formal influence intervals, but average pointwise forest bounds do not create group CIs. BLP calibration is conditional on training-half fits. DiD compares treated-cell ATT on the same100 simulations; empirical CS population adjustment differs from unadjusted TWFE. Sparse pre-period leads limit HonestDiD sensitivity. Sun-Abraham is the approved dCDH fallback. No modern retirement policy or German regional wage causal claim is warranted.

References: Chernozhukov et al.(2018),10.1111/ectj.12097, https://www.nber.org/papers/w23564 ; DoubleML JMLR23(53); Callaway & Sant'Anna,arxiv1803.09015; Sun & Abraham,arxiv1804.05785; forest and HonestDiD primary references in DATA.md.

## Licence

Code is MIT-licensed; third-party source data retain their original terms and are not included. Publication files and safety checks are documented in [docs/PUBLISH_CHECKLIST.md](docs/PUBLISH_CHECKLIST.md).

Hakan Zeki Gulmez | [GitHub](https://github.com/hakangulmez) | [LinkedIn](https://www.linkedin.com/in/hakan-zeki-g%C3%BClmez-088700180/)
