# Heterogeneous effects and causal forests

Status: draft for review

## Intuition

An average effect can conceal differences across people, but identifying a conditional effect is harder than predicting an outcome. A causal forest learns local contrasts after nuisance adjustment under exchangeability and overlap. Honest splitting separates tree partition choices from local effect estimation. Independent evaluation reduces overfitting to apparent heterogeneity.

## Model

$\tau(x)=E[Y(1)-Y(0)|X=x]$. An AIPW score is $g_1(X)-g_0(X)+D(Y-g_1(X))/m(X)-(1-D)(Y-g_0(X))/(1-m(X))$. Group averages of held-out scores estimate group ATEs under the maintained conditions. A best linear predictor projects the held-out score on an intercept and centered learned CATE; its slope describes calibration conditional on training fits.

## Assumptions and interpretation

A pointwise CATE confidence interval describes uncertainty at a particular covariate vector. Averaging its endpoints does not yield a confidence interval for the average effect in a group, because covariance matters. A GATES analysis usually groups by out-of-sample estimated effect ranks; income quartiles define a different target. A BLP summarizes projection onto chosen effect predictors rather than proving a structural heterogeneity mechanism.

## Application and limits

The forest is trained on one random half and evaluated on the held-out half. Income-quartile CATE means are descriptive. Held-out AIPW scores yield separate income-group ATE intervals with fixed clipping. These groups are not forest-ranked GATES, and their difference does not identify an effect of income. Heavy-tailed wealth, overlap and a single split remain fragile. No group is selected because it gives a desirable estimate.

```{=typst}
#pagebreak()
```

## Exam questions and answers

### 1. What makes forest splitting honest?

**Answer.** Partition selection and local effect estimation use separate information within the estimator.

### 2. Are averaged pointwise endpoints group confidence limits?

**Answer.** No; they omit the covariance needed for group-mean uncertainty.

### 3. What distinguishes income groups from GATES?

**Answer.** GATES groups are typically formed by held-out estimated-effect ranks rather than income alone.

### 4. Can a CATE pattern identify an income intervention?

**Answer.** No; it is treatment-effect heterogeneity conditional on income.

### 5. Why keep evaluation held out?

**Answer.** To avoid ranking and evaluating apparent heterogeneity on the same outcomes.

## Reasoning exercise

A researcher averages the lower and upper pointwise forest interval endpoints within a high-income group and calls them a confidence interval for its mean effect. Why is that invalid? Answer: group-mean variance requires dependence across individual predictions; endpoint averaging does not supply it. Form income groups independently of outcome-based effect ranking and evaluate them on held-out observations. A held-out AIPW group score can provide a formal group estimand and influence-function uncertainty under the maintained nuisance conditions. This differs from GATES formed by estimated-effect ranks. Even valid treatment-effect heterogeneity by income does not identify the effect of changing income itself.

## Verified reference

https://doi.org/10.1080/01621459.2017.1319839
