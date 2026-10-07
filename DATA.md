# Data, licence scope and lineage

Access: 7 October 2026; local private retention. No third-party raw rows, datasets, fitted row-level predictions or secrets enter Git. Repository code licensing does not license source data.

## Owner-approved SIPP analysis

The owner approved analysis of the public 1991 SIPP extract used in the published DML literature. Doubt concerns redistribution only. Acquisition uses `DoubleML.datasets.fetch_401K(return_type="DataFrame")` at runtime; no raw-data copying to Git or exports. Underlying public source: https://github.com/VC2015/DMLonGitHub/raw/master/sipp1991.dta. The upstream repository/software licence does not establish a separate dataset redistribution licence. Restrict retention to private research. This licence scope does not make the analysis incomplete.

The extract has 9,915 individuals and 14 fields. Outcome is net_tfa (1990 USD net financial assets), treatment is e401 (eligibility), not p401 (participation). Nine conditioning covariates: age, inc, educ, fsize, marr, twoearn, db, pira, hown. Measurements refer to 1990; do not assert all covariates were measured before eligibility. No missing-row deletion, winsorization or income-based filtering. Propensity clipping .01 is fixed and disclosed.

Citations: Chernozhukov et al. (2018), https://doi.org/10.1111/ectj.12097; Bach et al. (2022), JMLR 23(53), https://jmlr.org/papers/v23/21-0862.html; official data description https://docs.doubleml.org/stable/examples/py_double_ml_pension.html. DoubleML 0.11.4 / econml 0.17.0 / scikit-learn 1.9.1 are locked; terms apply separately to software.

## mpdta

Obtain through the pinned `did` 2.3.0 CRAN package at runtime. Package licence GPL-2; attribution Callaway–Sant Anna (2021), https://arxiv.org/abs/1803.09015, journal DOI 10.1016/j.jeconom.2020.12.001. Raw county rows stay private regardless of package redistribution permissions. Maintainer data page: https://bcallaway11.github.io/did/reference/mpdta.html. Actual object: 2,500 county-year rows, 500 counties, 2003–2007, six source columns. The older installed help count is stale. Population-adjusted CS uses lpop; primary TWFE is unadjusted, and differences therefore include adjustment and aggregation.

## Private-file checksums

- data/raw/sipp1991.csv: SHA-256 `d4d4a8a4a06f7ebf89b9b9b96139ef0c2ca31178be728770d6c747f8dc8f51c4`; 510098 bytes.
- data/raw/mpdta.csv: SHA-256 `e39bc4d0a2eb3ada5b553ef2b013ec1cdbd0050691216d0afca3debce4b4cd51`; 124867 bytes.

## Synthetic data and methodological references

Original synthetic DGPs use fixed seed 20261007 and private resumable checkpoints; no thesis access/reuse. Runtime and source hashes appear in results/manifest.json and results/r_manifest.json.

Sun–Abraham: https://arxiv.org/abs/1804.05785, journal DOI 10.1016/j.jeconom.2020.09.006. Goodman–Bacon: author publication page https://www.goodman-bacon.com/publications, DOI 10.1016/j.jeconom.2021.03.014. Rambachan–Roth: author manuscript https://www.jonathandroth.com/assets/files/HonestParallelTrends_Main.pdf, DOI 10.1093/restud/rdad018. Continuous-treatment estimands: https://arxiv.org/abs/2107.02637 (Callaway, Goodman-Bacon, Sant Anna). Causal forests: https://arxiv.org/abs/1510.04342 (Wager–Athey), DOI 10.1080/01621459.2017.1319839. Publisher endpoints returning 403 were cross-checked against primary author/arXiv records; no unverifiable citation was used.

Own Python .venv and R .R-library only. Scratch libraries remain untouched. Some pre-existing R dependency libraries are read only; new/missing dependencies install into the repository library. No paid APIs or system installs; only code, documentation and aggregate estimates are published.

Native Stata schema was rechecked through the DoubleML fetcher on 7 October 2026: nifa/net_tfa/tw/inc are float32; all remaining fields int8. Cached CSV reads restore these verified types before any estimation, preserving the same learner arithmetic as a fresh fetch. No stored observations are changed or deleted.


## V2 simulation addition, 7 October 2026

Original DGP1/empirical results unchanged. DGP2 sparse confounding was committed before any draw in docs/DGP2_PREDECLARATION.md. All100 draws at n600,p200 and fixed analytical Lasso penalty are reported. A separately declared genuine joint-penalized plug-in comparator was added to DGP1 for both-design comparability; the original in-sample orthogonal NaiveML comparison remains a distinct extra row. See docs/DGP1_PLUGIN_ADDENDUM.md, results/dml_two_dgps.csv and sparse_manifest.json. This illustrates published regularization-bias theory; it was not tuned to outcomes. All synthetic inputs are original; private SIPP licence scope is unchanged. Chernozhukov et al.(2018),10.1111/ectj.12097; https://www.nber.org/papers/w23564 .
