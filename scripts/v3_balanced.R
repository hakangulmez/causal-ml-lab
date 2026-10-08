# Aggregate retained group-time effects/IFs; no new ATT(g,t) fit.
.libPaths(c(normalizePath('.R-library'),.libPaths()))
suppressPackageStartupMessages({library(did);library(jsonlite);library(digest)})
objects<-readRDS('runs/mpdta_influence.rds');att<-objects$att
p<-read.csv('data/raw/mpdta.csv');counts<-table(p$first.treat[!duplicated(p$countyreal)])
cohorts<-c(2006,2007);weights<-as.numeric(counts[as.character(cohorts)]);weights<-weights/sum(weights)
support<-expand.grid(cohort=sort(unique(p$first.treat[p$first.treat>0])),event=-2:2)
support$time<-support$cohort+support$event
support$observed_calendar<-support$time %in% unique(p$year)
support$group_time_available<-mapply(function(g,t)any(att$group==g & att$t==t),support$cohort,support$time)
support$reference<-support$event==-1
support$balanced_included<-support$cohort %in% cohorts & support$event %in% -2:0
write.csv(support,'results/v3_cohort_event_support.csv',row.names=FALSE)
stopifnot(all(support$observed_calendar[support$balanced_included]),all(support$group_time_available[support$balanced_included]))
inf<-as.matrix(att$inffunc);n<-nrow(inf);influences<-matrix(0,n,3);points<-rep(0,3)
for(j in seq_along(-2:0)) {
 e<-(-2:0)[j]
 cells<-sapply(cohorts,function(g){selected<-which(att$group==g & att$t==g+e);stopifnot(length(selected)==1);selected})
 points[j]<-sum(weights*att$att[cells])
 influences[,j]<-as.vector(inf[,cells,drop=FALSE]%*%weights)
}
# Universal-base -1 ATT and influence are normalized to zero; keep explicit contrast.
points<-points-points[2];influences<-sweep(influences,1,influences[,2],'-')
covariance<-crossprod(influences)/n^2
se<-sqrt(diag(covariance))
output<-data.frame(event=-2:0,estimate=points,se=se,lo95=points-qnorm(.975)*se,hi95=points+qnorm(.975)*se,
                  cohorts='2006;2007',weights=paste(weights,collapse=';'),target='late-cohort balanced-window ATT; constant cohort-size weights',controls='never-treated',covariates='lpop',reference=-1)
write.csv(output,'results/v3_balanced_event.csv',row.names=FALSE)
write.csv(data.frame(cohort=cohorts,n=as.numeric(counts[as.character(cohorts)]),weight=weights),'results/v3_balanced_cohort_weights.csv',row.names=FALSE)
write.csv(covariance,'results/v3_balanced_event_covariance.csv',row.names=FALSE)
manifest<-list(original_if_sha256=digest::digest(file='runs/mpdta_influence.rds',algo='sha256'),original_data_sha256=digest::digest(file='data/raw/mpdta.csv',algo='sha256'),protocol_sha256=digest::digest(file='docs/V3_PROTOCOL.md',algo='sha256'),code_sha256=digest::digest(file='scripts/v3_balanced.R',algo='sha256'),n_influence_units=n,cohorts=cohorts,weights=weights,events=-2:0,constant_weights=TRUE,new_group_time_fits=FALSE,original_sensitivity_transferred=FALSE,paid_calls=0)
writeLines(toJSON(manifest,auto_unbox=TRUE,pretty=TRUE),'results/v3_balanced_manifest.json')
print(output)
