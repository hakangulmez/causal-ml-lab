# Parallel trends and the TWFE problem

Status: draft for review

## Intuition

Difference-in-differences identifies a counterfactual change, not a counterfactual outcome level. Parallel trends requires untreated potential-outcome changes to be comparable between treated and chosen controls. Different baseline levels can coexist with parallel trends. A graph or pretrend test provides evidence, not proof of the identifying assumption.

## Model

$ATT(g,t)=E[Y_t(1)-Y_t(0)|G=g]$. With no anticipation and valid controls, a group-time contrast compares $Y_t-Y_{g-1}$ for cohort g and controls. A TWFE coefficient solves a residualized regression on a pooled treatment indicator.

## Assumptions and interpretation

With staggered timing, already-treated units can enter comparisons for later-treated units. If effects evolve, their own treatment dynamics contaminate the contrast. Goodman-Bacon decomposes the pooled coefficient into two-by-two comparisons. Those comparison weights can be positive while implicit treatment-effect weights are problematic. Aggregation over cohorts and event times defines the target; comparisons must state the same weighting target before claiming bias.

## Application and limits

The simulation compares all methods against the treated-person-time average realised effect. CS uses never-treated controls and universal baseline. Sun-Abraham interaction terms separate cohort/event paths. The mpdta CS application conditions on population, while its primary TWFE benchmark is unadjusted; differences reflect both aggregation and covariate adjustment. Sparse pre-periods reduce power. There is no German regional minimum-wage application in this draft.

```{=typst}
#pagebreak()
```

## Exam questions and answers

### 1. Must baseline levels coincide?

**Answer.** No; the identifying restriction concerns untreated changes.

### 2. Why can early-treated controls be problematic?

**Answer.** Their changing treatment effect contaminates later comparisons.

### 3. Does a nonsignificant pretrend prove validity?

**Answer.** No; tests may have low power and concern only observed pre-periods.

### 4. What must accompany an aggregate ATT?

**Answer.** Its cohort/time weights and target population.

### 5. Are Bacon weights the same as all cell-effect weights?

**Answer.** No; a positive two-by-two decomposition does not guarantee clean dynamic-effect weighting.

## Reasoning exercise

A late-treated county is compared with an early-treated county after the latter has already adopted. What goes wrong when treatment effects evolve? Answer: the control outcome now contains an evolving treatment effect, so the contrast need not recover the late cohort effect. Use an admissible never-treated or not-yet-treated comparison and state anticipation and parallel-trends assumptions. Aggregate cohort-time effects with weights matching the stated target population. A positive Bacon decomposition weight does not guarantee positive weights on every dynamic effect. Compare adjusted and unadjusted estimators carefully: covariate adjustment and aggregation can both explain a numerical difference.

## Verified reference

https://arxiv.org/abs/1803.09015
