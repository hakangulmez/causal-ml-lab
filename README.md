# causal-ml-lab

When can regularization distort an estimated treatment effect, and what can cross-fitting and sensitivity diagnostics tell us?

![Headline](figures/headline.png)

## Findings

- In 1,000 sparse-design simulations, linear Lasso plug-in bias is 0.610, versus 0.003 for cross-fitted DML; 95% interval coverage is 0.0% versus 93.8%.
- Cross-fitting does not always improve the result: in the nonlinear design, in-sample orthogonal ML bias is 0.007, versus 0.039 for cross-fitted DML. These fixed-design comparisons do not establish a universal ranking.
- In the historical SIPP sample, the RF-IRM estimate is $8,172. The sensitivity robustness values are 8.41% for the effect bound and 4.94% for the confidence bound under the specified confounding model; they do not prove absence of confounding.

## Method

We compare OLS, plug-in machine learning and cross-fitted double machine learning in two seeded designs with known treatment effects. We estimate 401(k) eligibility effects using partially linear and interactive models and examine propensity overlap and sensitivity to unobserved confounding. We compare staggered-adoption estimators and a late-cohort balanced event-study window using never-treated controls. We report Monte Carlo uncertainty, effect intervals and the assumptions required for causal interpretation.

## Data sources

The published 1991 SIPP extract is fetched at runtime through DoubleML; the MPDTA county panel comes from the did package. Synthetic designs are defined in code. [DATA.md](DATA.md) records citations and the analysis-only scope of dataset access. No microdata, row-level predictions or fitted objects are redistributed.

## How to reproduce

Requirements: Python 3.11, uv and Tectonic, plus R. Dependencies install inside the repository.

```sh
make setup
make test lint quick
make policy-note report
```

The last command rebuilds the notes and working paper from included aggregate results, without data acquisition or model fitting. `make quick` is offline and synthetic. Empirical acquisition/rerun commands, required credentials and source-vintage constraints are documented in [provenance and reproduction](docs/PROVENANCE.md).

## Reports

[Two-page policy note](report/policy_note.pdf) · [Technical working paper](report/technical_report.pdf) · [Detailed results](report/report.md)

## Limitations

- Designs and learner families differ; their rankings are not universal.
- IPW ESS measures weight concentration, not causal validity or propensity-estimation uncertainty.
- Historical eligibility is not randomized or modern policy participation.
- Balanced and full-sample event studies target different cohorts/windows.
- Group inference conditions on fitted nuisance models; transportability is untested.

## Licence

Original code: [MIT](LICENSE). Third-party data retain their source terms and are not included.

Hakan Zeki Gülmez · [GitHub](https://github.com/hakangulmez) · [LinkedIn](https://www.linkedin.com/in/hakan-zeki-g%C3%BClmez-088700180/)
