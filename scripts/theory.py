"""Original two-page causal theory drafts; no thesis reuse."""

import subprocess
from pathlib import Path

root = Path.cwd()
target = root / "docs/theory"
target.mkdir(parents=True, exist_ok=True)
notes = [
    (
        "01_potential_outcomes",
        "Potential outcomes and identification",
        "A causal effect compares outcomes under alternative treatments for the same unit. Only one potential outcome is observed. A contrast between treated and untreated groups mixes the effect with selection unless an identifying restriction removes the counterfactual difference. Defining the estimand precedes choosing an estimator.",  # noqa: E501
        "$Y=D Y(1)+(1-D)Y(0)$. $ATE=E[Y(1)-Y(0)]$; $ATT=E[Y(1)-Y(0)|D=1]$. Conditional exchangeability is $(Y(1),Y(0))\\perp D|X$, with overlap $0<P(D=1|X)<1$.",  # noqa: E501
        "Exchangeability concerns unobserved potential outcomes and cannot be established by predictive accuracy. Covariates must be chosen with substantive timing and selection knowledge. Conditioning on descendants or colliders can create bias. Positivity supplies observed comparisons in relevant covariate strata; near violations amplify uncertainty and sensitivity to nuisance fits. SUTVA also rules out unmodelled spillovers and ambiguous treatment versions.",  # noqa: E501
        "401(k) eligibility is the treatment in the published replication; participation answers another question. PLR and IRM can target different weighted effects under heterogeneity. Covariates in the SIPP extract are contemporaneous measurements, so their causal timing requires review. Fixed propensity clipping changes how extreme estimated probabilities are handled; it cannot manufacture true overlap. A higher-income group effect does not identify the causal effect of income itself.",  # noqa: E501
        [
            (
                "What is the missing counterfactual?",
                "The unobserved outcome under the treatment not received.",
            ),
            (
                "Why can ATT differ from ATE?",
                "Effects and treatment selection can vary across people.",
            ),
            (
                "What does overlap provide?",
                "Comparable observed treatment states in the relevant covariate support.",
            ),
            (
                "Does cross-fitting prove exchangeability?",
                "No; it addresses estimation rather than identification.",
            ),
            (
                "Why examine covariate timing?",
                "Post-treatment adjustment and collider selection can alter the estimand or create bias.",  # noqa: E501
            ),
        ],
        "https://doi.org/10.1111/ectj.12097",
    ),
    (
        "02_parallel_trends",
        "Parallel trends and the TWFE problem",
        "Difference-in-differences identifies a counterfactual change, not a counterfactual outcome level. Parallel trends requires untreated potential-outcome changes to be comparable between treated and chosen controls. Different baseline levels can coexist with parallel trends. A graph or pretrend test provides evidence, not proof of the identifying assumption.",  # noqa: E501
        "$ATT(g,t)=E[Y_t(1)-Y_t(0)|G=g]$. With no anticipation and valid controls, a group-time contrast compares $Y_t-Y_{g-1}$ for cohort g and controls. A TWFE coefficient solves a residualized regression on a pooled treatment indicator.",  # noqa: E501
        "With staggered timing, already-treated units can enter comparisons for later-treated units. If effects evolve, their own treatment dynamics contaminate the contrast. Goodman-Bacon decomposes the pooled coefficient into two-by-two comparisons. Those comparison weights can be positive while implicit treatment-effect weights are problematic. Aggregation over cohorts and event times defines the target; comparisons must state the same weighting target before claiming bias.",  # noqa: E501
        "The simulation compares all methods against the treated-person-time average realised effect. CS uses never-treated controls and universal baseline. Sun-Abraham interaction terms separate cohort/event paths. The mpdta CS application conditions on population, while its primary TWFE benchmark is unadjusted; differences reflect both aggregation and covariate adjustment. Sparse pre-periods reduce power. There is no German regional minimum-wage application in this draft.",  # noqa: E501
        [
            (
                "Must baseline levels coincide?",
                "No; the identifying restriction concerns untreated changes.",
            ),
            (
                "Why can early-treated controls be problematic?",
                "Their changing treatment effect contaminates later comparisons.",
            ),
            (
                "Does a nonsignificant pretrend prove validity?",
                "No; tests may have low power and concern only observed pre-periods.",
            ),
            (
                "What must accompany an aggregate ATT?",
                "Its cohort/time weights and target population.",
            ),
            (
                "Are Bacon weights the same as all cell-effect weights?",
                "No; a positive two-by-two decomposition does not guarantee clean dynamic-effect weighting.",  # noqa: E501
            ),
        ],
        "https://arxiv.org/abs/1803.09015",
    ),
    (
        "03_honestdid",
        "HonestDiD and sensitivity",
        "An event study usually assumes a counterfactual post-treatment trend that cannot be observed. Sensitivity analysis asks how conclusions change when that assumption is relaxed within a stated class. Robust confidence sets incorporate sampling uncertainty and allowed violations. They do not estimate the true size of those violations.",  # noqa: E501
        "Write the observed event-study coefficient vector as $\\hat\\beta=\\tau+\\delta+\\epsilon$. Relative-magnitude restrictions bound post-treatment counterfactual deviations using the scale of pre-treatment deviations and a parameter $\\bar M$. The target is a stated linear combination $l^\\prime\\tau_{post}$.",  # noqa: E501
        "The normalization, pre-period coefficients and their full covariance must match the sensitivity procedure. Dropping the reference-period coefficient does not justify dropping cross-horizon covariance. A zero-violation setting is still a particular inferential construction; its confidence set can differ from a conventional pointwise interval. A bound must be chosen from substantive knowledge, not selected until a preferred conclusion survives.",  # noqa: E501
        "This project targets the impact component of the CS dynamic aggregation. The reference event time is removed, and county influence functions provide covariance. With few usable leads, the scale of permissible trend violations is weakly informed. The displayed Mbar sequence is prespecified. Bounds crossing zero are reported without interpreting them as evidence of no effect. Uniform versus pointwise uncertainty must be labelled accurately.",  # noqa: E501
        [
            ("Does Mbar measure an estimated bias?", "No; it indexes the allowed violation class."),
            (
                "Why retain covariance across coefficients?",
                "The target and constraints combine multiple dependent event-study estimates.",
            ),
            (
                "What is a sensitivity breakdown value?",
                "The bound at which a stated conclusion ceases to survive the permitted violations.",  # noqa: E501
            ),
            (
                "Can pretrends prove post-treatment parallel trends?",
                "No; future untreated trajectories remain counterfactual.",
            ),
            (
                "How should an interval including zero be described?",
                "The maintained model and violation bound do not support a sign conclusion at that confidence level.",  # noqa: E501
            ),
        ],
        "https://www.jonathandroth.com/assets/files/HonestParallelTrends_Main.pdf",
    ),
    (
        "04_orthogonality",
        "Neyman orthogonality and cross-fitting",
        "Flexible nuisance learners can predict well while introducing first-order regularization bias into a target coefficient. Orthogonal scores reduce sensitivity to small nuisance errors. Cross-fitting learns nuisance functions on one part of the data and evaluates scores on another. These tools address estimation under a maintained causal model.",  # noqa: E501
        "For PLR, let $m(X)=E[D|X]$ and $g(X)=E[Y|X]$. The score is $(D-m(X))(Y-g(X)-\\theta(D-m(X)))$. Its moment equals zero at the target. The estimate divides the mean residual product by mean squared residual treatment. Orthogonality makes the moment derivative with respect to nuisance perturbations vanish at the truth.",  # noqa: E501
        "Cross-fitting prevents a sample observation from helping train the nuisance prediction used in its own score. Orthogonality generally leaves products of nuisance errors, so rate and moment conditions still matter. Estimated influence-score variability supplies standard errors after normalization. Treatment residual variance close to zero makes the problem weakly identified in a practical sense. Repeated splits can reveal split sensitivity, but are not supplied in this one-repetition draft.",  # noqa: E501
        "The simulation compares OLS, naive in-sample residualization and five-fold cross-fitting with fixed learners. Naive residualization can have lower finite-sample point bias in a given DGP. This does not invalidate asymptotic protections or prove uniform superiority. All six real-data PLR/IRM models share explicit stratified folds; caching cannot change splits through RNG state. Linear learner failures under nonlinear confounding must be reported rather than hidden.",  # noqa: E501
        [
            (
                "What does orthogonality mean?",
                "First-order sensitivity of the score moment to nuisance error vanishes at the truth.",  # noqa: E501
            ),
            (
                "What does cross-fitting separate?",
                "Nuisance training observations from observations used to evaluate their scores.",
            ),
            (
                "Does prediction accuracy guarantee a causal estimate?",
                "No; identifying restrictions are independent of predictive performance.",
            ),
            (
                "Why normalize the score?",
                "To translate score variability into uncertainty for the target parameter.",
            ),
            (
                "Must DML beat naive ML in every finite sample?",
                "No; the protection is conditional and asymptotic, not uniform finite-sample dominance.",  # noqa: E501
            ),
        ],
        "https://doi.org/10.1111/ectj.12097",
    ),
    (
        "05_heterogeneity",
        "Heterogeneous effects and causal forests",
        "An average effect can conceal differences across people, but identifying a conditional effect is harder than predicting an outcome. A causal forest learns local contrasts after nuisance adjustment under exchangeability and overlap. Honest splitting separates tree partition choices from local effect estimation. Independent evaluation reduces overfitting to apparent heterogeneity.",  # noqa: E501
        "$\\tau(x)=E[Y(1)-Y(0)|X=x]$. An AIPW score is $g_1(X)-g_0(X)+D(Y-g_1(X))/m(X)-(1-D)(Y-g_0(X))/(1-m(X))$. Group averages of held-out scores estimate group ATEs under the maintained conditions. A best linear predictor projects the held-out score on an intercept and centered learned CATE; its slope describes calibration conditional on training fits.",  # noqa: E501
        "A pointwise CATE confidence interval describes uncertainty at a particular covariate vector. Averaging its endpoints does not yield a confidence interval for the average effect in a group, because covariance matters. A GATES analysis usually groups by out-of-sample estimated effect ranks; income quartiles define a different target. A BLP summarizes projection onto chosen effect predictors rather than proving a structural heterogeneity mechanism.",  # noqa: E501
        "The forest is trained on one random half and evaluated on the held-out half. Income-quartile CATE means are descriptive. Held-out AIPW scores yield separate income-group ATE intervals with fixed clipping. These groups are not forest-ranked GATES, and their difference does not identify an effect of income. Heavy-tailed wealth, overlap and a single split remain fragile. No group is selected because it gives a desirable estimate.",  # noqa: E501
        [
            (
                "What makes forest splitting honest?",
                "Partition selection and local effect estimation use separate information within the estimator.",  # noqa: E501
            ),
            (
                "Are averaged pointwise endpoints group confidence limits?",
                "No; they omit the covariance needed for group-mean uncertainty.",
            ),
            (
                "What distinguishes income groups from GATES?",
                "GATES groups are typically formed by held-out estimated-effect ranks rather than income alone.",  # noqa: E501
            ),
            (
                "Can a CATE pattern identify an income intervention?",
                "No; it is treatment-effect heterogeneity conditional on income.",
            ),
            (
                "Why keep evaluation held out?",
                "To avoid ranking and evaluating apparent heterogeneity on the same outcomes.",
            ),
        ],
        "https://doi.org/10.1080/01621459.2017.1319839",
    ),
]
cases = {
    "01_potential_outcomes": (
        "An eligibility comparison adjusts for an account-balance variable measured after "
        "eligibility is assigned. Does predictive power justify that control? Answer: the "
        "variable may mediate the treatment effect or be a collider. Define the "
        "eligibility intervention, outcome and timing of each covariate first; use "
        "substantive knowledge to choose an admissible adjustment set. Under conditional "
        "exchangeability and overlap, an IRM score can target an ATE; a PLR coefficient "
        "need not equal it when effects vary. A large estimate or excellent nuisance fit "
        "does not validate these assumptions. State which counterfactual population is "
        "represented and examine support before interpreting any conditional comparison."
    ),
    "02_parallel_trends": (
        "A late-treated county is compared with an early-treated county after the latter "
        "has already adopted. What goes wrong when treatment effects evolve? Answer: the "
        "control outcome now contains an evolving treatment effect, so the contrast need "
        "not recover the late cohort effect. Use an admissible never-treated or "
        "not-yet-treated comparison and state anticipation and parallel-trends "
        "assumptions. Aggregate cohort-time effects with weights matching the stated "
        "target population. A positive Bacon decomposition weight does not guarantee "
        "positive weights on every dynamic effect. Compare adjusted and unadjusted "
        "estimators carefully: covariate adjustment and aggregation can both explain a "
        "numerical difference."
    ),
    "03_honestdid": (
        "An event-study coefficient is significant, but its sensitivity confidence set "
        "contains zero under a small allowed departure from parallel trends. What should "
        "be reported? Answer: conventional significance depends on the exact-trends "
        "restriction and is not robust to that stated departure. Preserve coefficient "
        "covariance and the omitted reference period when constructing the sensitivity "
        "problem. The bound parameter describes an assumed class of deviations, not an "
        "estimated bias. With sparse pre-periods, apparent pretrend stability gives weak "
        "information about post-treatment deviations. Report the target linear "
        "combination, restriction class and confidence-set convention rather than "
        "declaring the causal sign established."
    ),
    "04_orthogonality": (
        "A nuisance learner fits treatment extremely well on the observations used to "
        "estimate the treatment coefficient. Why can the resulting residualized "
        "regression still be biased? Answer: in-sample fitting can correlate nuisance "
        "errors with the score and overfit residual variation. Cross-fitting predicts "
        "each observation from nuisance fits trained on other folds, while orthogonality "
        "cancels the first-order sensitivity to small nuisance errors around the true "
        "functions. Both need appropriate rate, moment and overlap conditions. They do "
        "not establish exchangeability and need not outperform a naive estimator in every "
        "finite sample. Compare bias, dispersion and coverage against a known simulation "
        "estimand and keep the same DGP after observing the outcome."
    ),
    "05_heterogeneity": (
        "A researcher averages the lower and upper pointwise forest interval endpoints "
        "within a high-income group and calls them a confidence interval for its mean "
        "effect. Why is that invalid? Answer: group-mean variance requires dependence "
        "across individual predictions; endpoint averaging does not supply it. Form "
        "income groups independently of outcome-based effect ranking and evaluate them on "
        "held-out observations. A held-out AIPW group score can provide a formal group "
        "estimand and influence-function uncertainty under the maintained nuisance "
        "conditions. This differs from GATES formed by estimated-effect ranks. Even valid "
        "treatment-effect heterogeneity by income does not identify the effect of "
        "changing income itself."
    ),
}
for name, title, intro, formula, mechanism, application, qa, reference in notes:
    text = f"# {title}\n\nStatus: draft for review\n\n## Intuition\n\n{intro}\n\n## Model\n\n{formula}\n\n## Assumptions and interpretation\n\n{mechanism}\n\n## Application and limits\n\n{application}\n\n```{{=typst}}\n#pagebreak()\n```\n\n## Exam questions and answers\n\n"  # noqa: E501  # noqa: E501
    for i, (q, a) in enumerate(qa, 1):
        text += f"### {i}. {q}\n\n**Answer.** {a}\n\n"
    text += (
        "## Reasoning exercise\n\n"
        + cases[name]
        + "\n\n## Verified reference\n\n"
        + reference
        + "\n"
    )  # noqa: E501
    p = target / (name + ".md")
    p.write_text(text)
    subprocess.run(
        [
            "pandoc",
            str(p),
            "--pdf-engine=typst",
            "--metadata-file=docs/render.yaml",
            "-o",
            str(p.with_suffix(".pdf")),
        ],
        check=True,
    )
