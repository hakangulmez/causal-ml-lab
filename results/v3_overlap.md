| learner | arm | n | clipped_count | clipped_share | below_count | above_count | observations_removed | ESS_clipped | ESS_raw | weight_definition | ESS_definition | threshold |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Lasso | 0 | 6233 | 0 | 0.0 | 0 | 0 | 0 | 4613.687659343959 | 4613.687659343959 | 1/m_clip for treated; 1/(1-m_clip) for control, restricted to each arm | (sum w)^2 / sum(w^2) | 0.01 |
| Lasso | 1 | 3682 | 0 | 0.0 | 0 | 0 | 0 | 3023.2690437098563 | 3023.2690437098563 | 1/m_clip for treated; 1/(1-m_clip) for control, restricted to each arm | (sum w)^2 / sum(w^2) | 0.01 |
| RF | 0 | 6233 | 51 | 0.0081822557356008 | 51 | 0 | 0 | 5213.286006065378 | 5213.170054959246 | 1/m_clip for treated; 1/(1-m_clip) for control, restricted to each arm | (sum w)^2 / sum(w^2) | 0.01 |
| RF | 1 | 3682 | 3 | 0.0008147745790331 | 3 | 0 | 0 | 1130.5494647959235 | 869.7575367776108 | 1/m_clip for treated; 1/(1-m_clip) for control, restricted to each arm | (sum w)^2 / sum(w^2) | 0.01 |
| GB | 0 | 6233 | 0 | 0.0 | 0 | 0 | 0 | 5571.965962687483 | 5571.965962687483 | 1/m_clip for treated; 1/(1-m_clip) for control, restricted to each arm | (sum w)^2 / sum(w^2) | 0.01 |
| GB | 1 | 3682 | 0 | 0.0 | 0 | 0 | 0 | 2422.893261454615 | 2422.893261454615 | 1/m_clip for treated; 1/(1-m_clip) for control, restricted to each arm | (sum w)^2 / sum(w^2) | 0.01 |
