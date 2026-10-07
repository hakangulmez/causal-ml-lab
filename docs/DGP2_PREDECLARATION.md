# V2 DGP 2: predeclared regularization-bias illustration

Declared before the first DGP 2 draw on 7 October 2026, in response to the V2 review. This DGP illustrates regularization bias in the published DML theory; it is not a replacement for DGP 1 or a specification selected against Monte Carlo results.

- 100 repetitions; seeds 20261008 + repetition; n=600, p=200, five active confounders; all X and the independent outcome/treatment errors are standard normal.
- D = 1.5 sum(X_1,...,X_5) + V; Y = 1.0 D + sum(X_1,...,X_5) + U. Thus treatment/confounder correlation is strong, the true effect is 1, and linear controls are correctly specified for OLS.
- OLS: all 200 covariates and intercept, HC1 standard errors.
- Naive plug-in ML: jointly fit the partially linear outcome by Lasso-penalizing only the 200 nuisance slopes (treatment and intercept unpenalized), then use the nonorthogonal moment mean[D(Y-theta D-g(X))]=0. Implement exactly by projecting Y and X off the intercept and D before Lasso, recovering theta by OLS on Y-g(X). Report the naive conditional HC1 sandwich that ignores nuisance-estimation uncertainty; its coverage is empirical, not a validity claim.
- DML: five fixed shuffled folds, independent Lasso fits for E[Y|X] and E[D|X], and the orthogonal residual-on-residual score with influence-score standard error.
- Lasso penalty fixed analytically at sqrt(2 log(200)/600), max_iter=10000, tol=1e-7; no penalty selection on simulation results. DML has training-fold StandardScaler; the joint plug-in uses training-sample centered raw X (unit-variance population), with projection rather than ad hoc treatment penalization.
- Report mean bias, RMSE, Monte Carlo standard error of mean bias, nominal-95% coverage and binomial uncertainty. No outcome-dependent reruns, favorable seeds, or DGP coefficient adjustment.

DGP 1 retains the original 100-draw nonlinear experiment and its in-sample residual-on-residual NaiveML comparison. That existing comparator is already an orthogonal score without cross-fitting; it is not the nonorthogonal plug-in used in DGP 2. Label this distinction explicitly rather than claiming the two NaiveML constructions isolate the effect of changing DGP alone.

Reference: Chernozhukov et al. (2018), *The Econometrics Journal* 21(1), C1-C68, DOI 10.1111/ectj.12097; author abstract and working paper: https://www.nber.org/papers/w23564 .
