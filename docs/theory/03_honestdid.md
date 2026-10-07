# HonestDiD and sensitivity

Status: draft for review

## Intuition

An event study usually assumes a counterfactual post-treatment trend that cannot be observed. Sensitivity analysis asks how conclusions change when that assumption is relaxed within a stated class. Robust confidence sets incorporate sampling uncertainty and allowed violations. They do not estimate the true size of those violations.

## Model

Write the observed event-study coefficient vector as $\hat\beta=\tau+\delta+\epsilon$. Relative-magnitude restrictions bound post-treatment counterfactual deviations using the scale of pre-treatment deviations and a parameter $\bar M$. The target is a stated linear combination $l^\prime\tau_{post}$.

## Assumptions and interpretation

The normalization, pre-period coefficients and their full covariance must match the sensitivity procedure. Dropping the reference-period coefficient does not justify dropping cross-horizon covariance. A zero-violation setting is still a particular inferential construction; its confidence set can differ from a conventional pointwise interval. A bound must be chosen from substantive knowledge, not selected until a preferred conclusion survives.

## Application and limits

This project targets the impact component of the CS dynamic aggregation. The reference event time is removed, and county influence functions provide covariance. With few usable leads, the scale of permissible trend violations is weakly informed. The displayed Mbar sequence is prespecified. Bounds crossing zero are reported without interpreting them as evidence of no effect. Uniform versus pointwise uncertainty must be labelled accurately.

```{=typst}
#pagebreak()
```

## Exam questions and answers

### 1. Does Mbar measure an estimated bias?

**Answer.** No; it indexes the allowed violation class.

### 2. Why retain covariance across coefficients?

**Answer.** The target and constraints combine multiple dependent event-study estimates.

### 3. What is a sensitivity breakdown value?

**Answer.** The bound at which a stated conclusion ceases to survive the permitted violations.

### 4. Can pretrends prove post-treatment parallel trends?

**Answer.** No; future untreated trajectories remain counterfactual.

### 5. How should an interval including zero be described?

**Answer.** The maintained model and violation bound do not support a sign conclusion at that confidence level.

## Reasoning exercise

An event-study coefficient is significant, but its sensitivity confidence set contains zero under a small allowed departure from parallel trends. What should be reported? Answer: conventional significance depends on the exact-trends restriction and is not robust to that stated departure. Preserve coefficient covariance and the omitted reference period when constructing the sensitivity problem. The bound parameter describes an assumed class of deviations, not an estimated bias. With sparse pre-periods, apparent pretrend stability gives weak information about post-treatment deviations. Report the target linear combination, restriction class and confidence-set convention rather than declaring the causal sign established.

## Verified reference

https://www.jonathandroth.com/assets/files/HonestParallelTrends_Main.pdf
