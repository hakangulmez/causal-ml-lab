# Neyman orthogonality and cross-fitting

Status: draft for review

## Intuition

Flexible nuisance learners can predict well while introducing first-order regularization bias into a target coefficient. Orthogonal scores reduce sensitivity to small nuisance errors. Cross-fitting learns nuisance functions on one part of the data and evaluates scores on another. These tools address estimation under a maintained causal model.

## Model

For PLR, let $m(X)=E[D|X]$ and $g(X)=E[Y|X]$. The score is $(D-m(X))(Y-g(X)-\theta(D-m(X)))$. Its moment equals zero at the target. The estimate divides the mean residual product by mean squared residual treatment. Orthogonality makes the moment derivative with respect to nuisance perturbations vanish at the truth.

## Assumptions and interpretation

Cross-fitting prevents a sample observation from helping train the nuisance prediction used in its own score. Orthogonality generally leaves products of nuisance errors, so rate and moment conditions still matter. Estimated influence-score variability supplies standard errors after normalization. Treatment residual variance close to zero makes the problem weakly identified in a practical sense. Repeated splits can reveal split sensitivity, but are not supplied in this one-repetition draft.

## Application and limits

The simulation compares OLS, naive in-sample residualization and five-fold cross-fitting with fixed learners. Naive residualization can have lower finite-sample point bias in a given DGP. This does not invalidate asymptotic protections or prove uniform superiority. All six real-data PLR/IRM models share explicit stratified folds; caching cannot change splits through RNG state. Linear learner failures under nonlinear confounding must be reported rather than hidden.

```{=typst}
#pagebreak()
```

## Exam questions and answers

### 1. What does orthogonality mean?

**Answer.** First-order sensitivity of the score moment to nuisance error vanishes at the truth.

### 2. What does cross-fitting separate?

**Answer.** Nuisance training observations from observations used to evaluate their scores.

### 3. Does prediction accuracy guarantee a causal estimate?

**Answer.** No; identifying restrictions are independent of predictive performance.

### 4. Why normalize the score?

**Answer.** To translate score variability into uncertainty for the target parameter.

### 5. Must DML beat naive ML in every finite sample?

**Answer.** No; the protection is conditional and asymptotic, not uniform finite-sample dominance.

## Reasoning exercise

A nuisance learner fits treatment extremely well on the observations used to estimate the treatment coefficient. Why can the resulting residualized regression still be biased? Answer: in-sample fitting can correlate nuisance errors with the score and overfit residual variation. Cross-fitting predicts each observation from nuisance fits trained on other folds, while orthogonality cancels the first-order sensitivity to small nuisance errors around the true functions. Both need appropriate rate, moment and overlap conditions. They do not establish exchangeability and need not outperform a naive estimator in every finite sample. Compare bias, dispersion and coverage against a known simulation estimand and keep the same DGP after observing the outcome.

## Verified reference

https://doi.org/10.1111/ectj.12097
