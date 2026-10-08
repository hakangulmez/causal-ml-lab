# Read-only scientific accounting checks of balanced support, fixed weights and IFs.
.libPaths(c(normalizePath('.R-library'),.libPaths()))
p<-read.csv('results/v3_cohort_event_support.csv');w<-read.csv('results/v3_balanced_cohort_weights.csv');b<-read.csv('results/v3_balanced_event.csv');v<-as.matrix(read.csv('results/v3_balanced_event_covariance.csv'))
stopifnot(identical(w$cohort,c(2006L,2007L)),abs(sum(w$weight)-1)<1e-12,
          all(p$observed_calendar[p$balanced_included]),all(p$group_time_available[p$balanced_included]),
          nrow(p[p$balanced_included,])==6,identical(b$event,-2L:0L),b$estimate[2]==0,b$se[2]==0)
att<-readRDS('runs/mpdta_influence.rds')$att
cells<-which(att$group %in% w$cohort & att$t-att$group==0)
expected<-sum(att$att[cells]*w$weight[match(att$group[cells],w$cohort)])
stopifnot(abs(expected-b$estimate[b$event==0])<1e-12,max(abs(v-t(v)))<1e-12,
          max(abs(sqrt(diag(v))-b$se))<1e-12)
cat('V3 balanced support, fixed weights, reference and influence covariance: passed\n')
