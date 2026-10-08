# Causal ML: shrinkage and identification

When can regularization distort an estimated treatment effect, and what can cross-fitting and sensitivity diagnostics tell us?

We compare OLS, plug-in machine learning and cross-fitted double machine learning in two seeded designs with known treatment effects. We estimate 401(k) eligibility effects using partially linear and interactive models and examine propensity overlap and sensitivity to unobserved confounding. We compare staggered-adoption estimators and a late-cohort balanced event-study window using never-treated controls. We report Monte Carlo uncertainty, effect intervals and the assumptions required for causal interpretation.

![Headline](../figures/headline.png)

- In 1,000 sparse-design simulations, linear Lasso plug-in bias is 0.610, versus 0.003 for cross-fitted DML; 95% interval coverage is 0.0% versus 93.8%.
- Cross-fitting does not always improve the result: in the nonlinear design, in-sample orthogonal ML bias is 0.007, versus 0.039 for cross-fitted DML. These fixed-design comparisons do not establish a universal ranking.
- In the historical SIPP sample, the RF-IRM estimate is $8,172. The sensitivity robustness values are 8.41% for the effect bound and 4.94% for the confidence bound under the specified confounding model; they do not prove absence of confounding.

## Limitations

- Designs and learner families differ; their rankings are not universal.
- IPW ESS measures weight concentration, not causal validity or propensity-estimation uncertainty.
- Historical eligibility is not randomized or modern policy participation.
- Balanced and full-sample event studies target different cohorts/windows.
- Group inference conditions on fitted nuisance models; transportability is untested.

## Technical notes

IPW ESS is a weight-concentration diagnostic; it does not include propensity-estimation uncertainty and is not a measure of causal validity. Clipping probabilities removes no observations. The balanced comparison uses cohorts 2006 and 2007 at event times -2, -1 and 0, with -1 as reference and constant cohort-size weights; its estimand differs from the full dynamic analysis. Income-quartile cutoffs are empirically computed, not forest-discovered groups. The technical working paper gives estimator equations, sensitivity definitions and simulation designs.

Published 1991 SIPP extract via DoubleML; the did package's MPDTA county panel; seeded synthetic experiments.
