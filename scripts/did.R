# Original analysis is callable for instrumented statistical coverage.
run_did <- function() {
# Original causal demonstrations; no thesis code or data.
.libPaths(c(normalizePath('.R-library'),.libPaths()))
suppressPackageStartupMessages({library(did);library(fixest);library(HonestDiD);library(bacondecomp)})
dir.create('data/raw',recursive=TRUE,showWarnings=FALSE)
dir.create('runs',showWarnings=FALSE)
dir.create('results',showWarnings=FALSE)
r_code_sha <- digest::digest(file='scripts/did.R',algo='sha256')
set.seed(20261007)
data(mpdta,package='did')
write.csv(mpdta,'data/raw/mpdta.csv',row.names=FALSE)
stopifnot(nrow(mpdta)==2500,length(unique(mpdta$countyreal))==500)
mpdta$D <- as.integer(mpdta$first.treat>0 & mpdta$year>=mpdta$first.treat)
tw <- feols(lemp~D|countyreal+year,data=mpdta,cluster=~countyreal)
att <- att_gt(yname='lemp',tname='year',idname='countyreal',gname='first.treat',xformla=~lpop,data=mpdta,control_group='nevertreated',base_period='universal',bstrap=FALSE,cband=FALSE)
agg <- aggte(att,type='simple',bstrap=FALSE,cband=FALSE)
application <- data.frame(method=c('TWFE','CS_simple'),estimate=c(coef(tw)['D'],agg$overall.att),se=c(se(tw)['D'],agg$overall.se))
application$lo95 <- application$estimate-1.96*application$se
application$hi95 <- application$estimate+1.96*application$se
write.csv(application,'results/mpdta_estimates.csv',row.names=FALSE)
write.csv(data.frame(cohort=att$group,time=att$t,ATT=att$att,se=att$se),'results/mpdta_group_time.csv',row.names=FALSE)
event <- aggte(att,type='dynamic',min_e=-2,max_e=2,bstrap=FALSE,cband=FALSE,na.rm=TRUE)
events <- data.frame(event=event$egt,estimate=event$att.egt,se=event$se.egt)
events$lo95 <- events$estimate-1.96*events$se;events$hi95 <- events$estimate+1.96*events$se
write.csv(events,'results/mpdta_event.csv',row.names=FALSE)
saveRDS(list(att=att,event=event),'runs/mpdta_influence.rds')
# Retain full estimator objects privately. Sparse pretrends limit sensitivity.
tryCatch({
 keep <- event$egt != -1
 e <- event$egt[keep];b <- event$att.egt[keep]
 inf <- event$inf.function$dynamic.inf.func.e[,keep,drop=FALSE]
 covariance <- crossprod(inf)/nrow(inf)^2
 pre <- sum(e<0);post <- sum(e>=0)
 stopifnot(pre>0,post>0,all(is.finite(covariance)))
 l <- rep(0,post);l[1] <- 1
 bounds <- createSensitivityResults_relativeMagnitudes(betahat=b,sigma=covariance,numPrePeriods=pre,numPostPeriods=post,Mbarvec=c(0,.5,1,2),l_vec=l,alpha=.05)
 write.csv(as.data.frame(bounds),'results/honestdid.csv',row.names=FALSE)
},error=function(e)writeLines(paste('HonestDiD incomplete:',conditionMessage(e)),'results/honestdid_failure.txt'))
# Goodman-Bacon decomposition of the unadjusted TWFE specification.
tryCatch({
 decomposition <- bacon(lemp~D,data=mpdta,id_var='countyreal',time_var='year',quiet=TRUE)
 write.csv(decomposition,'results/bacon.csv',row.names=FALSE)
 stopifnot(abs(sum(decomposition$weight)-1)<1e-6,abs(sum(decomposition$weight*decomposition$estimate)-coef(tw)['D'])<1e-6)
},error=function(e)writeLines(paste('Bacon incomplete:',conditionMessage(e)),'results/bacon_failure.txt'))
# Same DGP and treated-person-time ATT target for all three Monte Carlo estimators.
mc <- list()
for (rep in 1:100) {
 set.seed(20261007+rep)
 n <- 300;periods <- 1:8
 cohorts <- sample(c(0,3,5,7),n,replace=TRUE)
 p <- expand.grid(time=periods,id=1:n);p <- p[order(p$id,p$time),]
 p$g <- cohorts[p$id];p$D <- as.integer(p$g>0 & p$time>=p$g)
 p$effect <- p$D*(p$time-p$g+1)*(1+.7*(p$g==5)+1.5*(p$g==7))
 p$y <- rnorm(n)[p$id]+.15*p$time+p$effect+rnorm(nrow(p),sd=.5)
 truth <- mean(p$effect[p$D==1])
 twfe <- feols(y~D|id+time,data=p,cluster=~id)
 cs <- att_gt(yname='y',tname='time',idname='id',gname='g',xformla=~1,data=p,control_group='nevertreated',base_period='universal',bstrap=FALSE,cband=FALSE)
 csagg <- aggte(cs,type='simple',bstrap=FALSE,cband=FALSE)
 sa <- feols(y~sunab(g,time)|id+time,data=p,cluster=~id)
 saagg <- aggregate(sa,'ATT')
 points <- c(coef(twfe)['D'],csagg$overall.att,saagg[1,'Estimate'])
 errors <- c(se(twfe)['D'],csagg$overall.se,saagg[1,'Std. Error'])
 mc[[rep]] <- data.frame(rep=rep,method=c('TWFE','CS','SunAbraham'),estimate=points,se=errors,truth=truth,covered=abs(points-truth)<=1.96*errors)
 if(rep%%10==0)cat('DiD Monte Carlo',rep,'of 100\n')
}
mc <- do.call(rbind,mc);write.csv(mc,'runs/did_mc_private.csv',row.names=FALSE)
summary <- do.call(rbind,lapply(split(mc,mc$method),function(z){e=z$estimate-z$truth;data.frame(method=unique(z$method),repetitions=nrow(z),bias=mean(e),rmse=sqrt(mean(e^2)),mc_se=sd(e)/sqrt(length(e)),coverage=mean(z$covered))}))
stopifnot(nrow(summary)==3,all(summary$repetitions==100))
write.csv(summary,'results/did_monte_carlo.csv',row.names=FALSE)
# Independent estimator property checks on the noiseless homogeneous case.
p$effect <- 2*p$D;p$y <- .15*p$time+p$effect
check <- feols(y~D|id+time,data=p)
stopifnot(abs(coef(check)['D']-2)<1e-8)
cat('R estimator checks passed\n')

writeLines(jsonlite::toJSON(list(code_sha256=r_code_sha,seed=20261007,mpdta_rows=nrow(mpdta),versions=sapply(c('did','fixest','HonestDiD','bacondecomp'),function(x)as.character(packageVersion(x)))),auto_unbox=TRUE,pretty=TRUE),'results/r_manifest.json')

}
if(sys.nframe()==0) run_did()
