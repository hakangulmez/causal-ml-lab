# Provenance and reproduction

The concise README presents the empirical question and results. This document retains the research protocols, result lineage, version history, reproduction boundaries and Monte Carlo replay details. Source data remain governed by DATA.md.

# Reproduction of the accepted V3 snapshot

The checked-in aggregate tables and reports are the accepted, frozen V3 results. Source data, fitted objects, row-level forecasts, bootstrap arrays and repetition-level simulation draws are excluded. Data access and attribution remain in DATA.md; MIT applies to original code, not source data.

## Rebuild and tests from a clean clone

Install Python 3.11, uv and R for C1. `make setup test lint quick` installs only repository-local dependencies and checks implementations with synthetic fixtures; the R test uses its own temporary 100-repetition fixture, not another V3 precision run. Install Tectonic locally or set `TECTONIC=/path/to/tectonic`; `make policy-note report` rebuilds the current notes and working paper from included aggregate tables, with no data download, refitting or credentials. Working-paper equations are tied to implementation hashes. The supplied frozen V2 aggregate fixtures support regression tests and comparisons; they contain no private rows or history.

## Acquisition and empirical reruns

`make all` remains the original pre-V3 empirical reproduction pipeline. M1 acquires official sources with the reader's own ignored `.env` (FRED_API_KEY, EVDS_API_KEY); C1 fetches the public SIPP extract and did example for permitted private analysis. It writes private data/runs and replaces aggregate outputs in that working checkout. It is not an exact reconstruction of the approved V3 private-artifact history: new source vintages may differ, and the original 1,000-repetition continuation reused private repetition-level checkpoints. Run it in a separate clone; do not describe its legacy 100-repetition results as V3. Archive the supplied aggregates before any empirical rerun.

V3 methods and diagnostic source code is included. M1 `make v3-methods` requires a locally acquired panel and the exact, permitted EA-MPD workbook with the documented frozen hash; a refreshed workbook is not silently substituted. `make v3-diagnostics` in C1 requires runtime SIPP data; balanced influence-function checks require the local fitted did object. The consumed MC manifests intentionally prevent an accidental second precision budget. Reconstructing those private checkpoint histories is outside the self-contained aggregate report build; no private checkpoints are redistributed. V3 protocols retain all specifications, dates, availability assumptions, seeds and fixed budgets.

The public code/figures/aggregate results were synchronized from approved local source commits, not by merging private research Git history. Publication metadata explains small documentation-only differences. No learner, instrument, lag search or causal estimand was changed for publication.


## Research lineage and detailed disclosures

V3 protocol: docs/V3_PROTOCOL.md. Required frozen V2 aggregate fixtures: versions/v2-2026-10-07/; full private archive is not distributed. New Monte Carlos preserve DGPs, penalties, sample sizes, estimator/fold settings and seed sequences. Each of three separately allocated ten-minute blocks completed 1000 matched repetitions: old100 reused only after seed/draw verification and deterministic endpoint replays, new900 executed. Python nonlinear block includes its associated Python DiD runner; Python and R draws are not pooled. Checkpoints remain private. Fit failures, runtimes, counts and stop rules are exported in results/v3_*mc_manifest.json. Coverage MCSE=sqrt(p(1-p)/R), with Wilson 95 intervals; MCSE zero at endpoints is not certainty.

SIPP three IRM refits recover raw out-of-fold probabilities from fitted objects with original folds/learners. RF estimate unchanged; Lasso numerical difference only (results/v3_irm_refit_comparison.csv). RF clips 54/9915 predictions; removes 0 observations. IPW ESS=(sum w)^2/sum(w^2), w=1/m_clip treated,1/(1-m_clip) controls; RF treated ESS=1130.549, controls=5213.286. Raw distributions and all learner/arm counts are shown separately. Clipping is not trimming. IPW ESS is a weight-concentration diagnostic; it does not include propensity-estimation uncertainty and is not a measure of causal validity.

DoubleML sensitivity for RF–IRM ATE uses the fixed 16-pair grid cf_y, cf_d in .01,.03,.05,.10; rho = 1, 95% level, null0. cf_y is the share of outcome residual variance attributable to latent confounding; IRM cf_d is a relative gain in average conditional treatment precision/Riesz variance, not the PLR treatment R-squared. RV equal-strength effect-bound threshold=0.084107, RVa confidence-bound threshold=0.049404. Confidence endpoints are 95% one-sided limits on effect bounds. The exercise presumes this confounding model and is no proof of exchangeability. Definitions: https://docs.doubleml.org/stable/guide/sensitivity.html .

Late-cohort balanced-window comparison retains cohorts 2006 and 2007 and event times -2, -1 and 0; weights fixed by cohort size, never-treated controls and unchanged ATT(g, t) fits. Influence functions form constant-weight contrasts against -1. It targets a different cohort/window population than the original dynamic analysis. Original HonestDiD results apply only to the original estimand/composition. balance_e concerns post-treatment exposure, not proof of balanced pre-treatment support (official did aggte documentation). Income-quartile groups preserve their estimates: the V3 rule is right-closed pandas qcut4 on the original held-out income sample; cutoffs are empirically computed, not retrospectively pre-specified numeric thresholds or forest-discovered groups.

Sparse treatment loading 1.5 makes treatment correlated with the five confounders. The plug-in projects Y and X off intercept/treatment before fixed-penalty Lasso. Population projected active covariance=0.081633 is below the unchanged penalty=0.132895; shrinkage can omit the confounder signal and return omitted-confounder bias near the unadjusted population value=0.612245. Actual finite-sample plug-in bias=0.609943. This algebra explains the declared design, not a universal ranking. No penalty was changed.

Inherited pension/forest/groups/MPDTA/HonestDiD/dose estimates remain in original files; V3 adds diagnostics, precision and the balanced estimand. All raw rows, probability predictions and fitted objects remain private; no paid provider calls or private-data redistribution.


## Limitations and future work

Matched-learner, scaling, oracle and fold factorials; denser/correlated or p>=n DGPs and heteroskedastic inference; fuller Monte Carlo uncertainty for RMSE and average estimated SE; nuisance-score concentration and observed-confounding benchmarks; clipping-grid/repeated-split/DAG-control sensitivity; alternative historical wealth outcomes and transportability; income-quartile contrasts and forest-ranked groups; estimator comparisons with identical covariates; new balanced-target HonestDiD sensitivity and pretrend-power studies; observational continuous-dose identification. These substantive review extensions are deferred, with no new tuning or target changes.

Hakan Zeki Gülmez | [GitHub](https://github.com/hakangulmez) | [LinkedIn](https://www.linkedin.com/in/hakan-zeki-g%C3%BClmez-088700180/)
