# Potential outcomes and identification

Status: draft for review

## Intuition

A causal effect compares outcomes under alternative treatments for the same unit. Only one potential outcome is observed. A contrast between treated and untreated groups mixes the effect with selection unless an identifying restriction removes the counterfactual difference. Defining the estimand precedes choosing an estimator.

## Model

$Y=D Y(1)+(1-D)Y(0)$. $ATE=E[Y(1)-Y(0)]$; $ATT=E[Y(1)-Y(0)|D=1]$. Conditional exchangeability is $(Y(1),Y(0))\perp D|X$, with overlap $0<P(D=1|X)<1$.

## Assumptions and interpretation

Exchangeability concerns unobserved potential outcomes and cannot be established by predictive accuracy. Covariates must be chosen with substantive timing and selection knowledge. Conditioning on descendants or colliders can create bias. Positivity supplies observed comparisons in relevant covariate strata; near violations amplify uncertainty and sensitivity to nuisance fits. SUTVA also rules out unmodelled spillovers and ambiguous treatment versions.

## Application and limits

401(k) eligibility is the treatment in the published replication; participation answers another question. PLR and IRM can target different weighted effects under heterogeneity. Covariates in the SIPP extract are contemporaneous measurements, so their causal timing requires review. Fixed propensity clipping changes how extreme estimated probabilities are handled; it cannot manufacture true overlap. A higher-income group effect does not identify the causal effect of income itself.

```{=typst}
#pagebreak()
```

## Exam questions and answers

### 1. What is the missing counterfactual?

**Answer.** The unobserved outcome under the treatment not received.

### 2. Why can ATT differ from ATE?

**Answer.** Effects and treatment selection can vary across people.

### 3. What does overlap provide?

**Answer.** Comparable observed treatment states in the relevant covariate support.

### 4. Does cross-fitting prove exchangeability?

**Answer.** No; it addresses estimation rather than identification.

### 5. Why examine covariate timing?

**Answer.** Post-treatment adjustment and collider selection can alter the estimand or create bias.

## Reasoning exercise

An eligibility comparison adjusts for an account-balance variable measured after eligibility is assigned. Does predictive power justify that control? Answer: the variable may mediate the treatment effect or be a collider. Define the eligibility intervention, outcome and timing of each covariate first; use substantive knowledge to choose an admissible adjustment set. Under conditional exchangeability and overlap, an IRM score can target an ATE; a PLR coefficient need not equal it when effects vary. A large estimate or excellent nuisance fit does not validate these assumptions. State which counterfactual population is represented and examine support before interpreting any conditional comparison.

## Verified reference

https://doi.org/10.1111/ectj.12097
