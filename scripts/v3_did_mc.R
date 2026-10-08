# Strict time/completion-only extension of the original R DiD experiment.
.libPaths(c(normalizePath('.R-library'),.libPaths()))
suppressPackageStartupMessages({library(did);library(fixest);library(jsonlite);library(digest)})
if(file.exists('results/v3_r_did_mc_manifest.json')) {
 saved<-jsonlite::fromJSON('results/v3_r_did_mc_manifest.json')
 stopifnot(saved$protocol_sha256==digest::digest(file='docs/V3_PROTOCOL.md',algo='sha256'))
 message('Existing budgeted R block retained; no additional simulation executed')
 quit(save='no',status=0)
}
start <- Sys.time();deadline <- start+600
private <- 'runs/v3_mc';dir.create(private,recursive=TRUE,showWarnings=FALSE)
old <- read.csv('runs/did_mc_private.csv')
stopifnot(length(unique(old$rep))==100)
compute_rep <- function(rep) {
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

 data.frame(rep=rep,method=c('TWFE','CS','SunAbraham'),estimate=points,se=errors,truth=truth,covered=abs(points-truth)<=1.96*errors,seed=20261007+rep,draw_sha256=digest::digest(list(y=p$y,D=p$D,g=p$g),algo='sha256'))
}
rows <- list();failures <- list();replays <- list()
# Catch an in-progress estimator at the wall-clock deadline. No partial rep enters.
budget_call <- function(rep) {
 remaining <- as.numeric(difftime(deadline,Sys.time(),units='secs'))
 if(remaining<=0)stop('fixed deadline reached')
 setTimeLimit(elapsed=remaining,transient=TRUE)
 on.exit(setTimeLimit(cpu=Inf,elapsed=Inf,transient=FALSE))
 compute_rep(rep)
}
verified <- TRUE
for(rep in c(1,100)) {
 out <- tryCatch(budget_call(rep),error=function(e)e)
 if(inherits(out,'error')){failures[[length(failures)+1]]<-list(rep=rep,reason=conditionMessage(out));verified<-FALSE;break}
 previous <- old[old$rep==rep,]
 previous <- previous[match(out$method,previous$method),]
 stopifnot(max(abs(previous$estimate-out$estimate))<1e-8,max(abs(previous$se-out$se))<1e-8)
 replays[[length(replays)+1]]<-list(rep=rep,matched=TRUE,seed=20261007+rep)
}
if(verified) {
 old$seed<-20261007+old$rep;old$draw_sha256<-NA_character_;old$execution<-'verified V2 reuse'
 for(rep in unique(old$rep)) {
 set.seed(20261007+rep)
 n <- 300;periods <- 1:8
 cohorts <- sample(c(0,3,5,7),n,replace=TRUE)
 p <- expand.grid(time=periods,id=1:n);p <- p[order(p$id,p$time),]
 p$g <- cohorts[p$id];p$D <- as.integer(p$g>0 & p$time>=p$g)
 p$effect <- p$D*(p$time-p$g+1)*(1+.7*(p$g==5)+1.5*(p$g==7))
 p$y <- rnorm(n)[p$id]+.15*p$time+p$effect+rnorm(nrow(p),sd=.5)

 old$draw_sha256[old$rep==rep]<-digest::digest(list(y=p$y,D=p$D,g=p$g),algo='sha256')
 }
 rows[[1]]<-old
 for(rep in 101:1000) {
  if(Sys.time()>=deadline)break
  out<-tryCatch(budget_call(rep),error=function(e)e)
  if(inherits(out,'error')) {
    failures[[length(failures)+1]]<-list(rep=rep,reason=conditionMessage(out))
    if(Sys.time()>=deadline)break
    next
  }
  if(Sys.time()>=deadline){failures[[length(failures)+1]]<-list(rep=rep,reason='unfinished at fixed deadline; excluded');break}
  out$execution<-'new V3 repetition';rows[[length(rows)+1]]<-out
  temporary<-file.path(private,'r_did.tmp');write.csv(do.call(rbind,rows),temporary,row.names=FALSE);file.rename(temporary,file.path(private,'r_did.csv'))
  if(rep%%25==0)cat('R DiD completed',rep,'elapsed',as.numeric(difftime(Sys.time(),start,units='secs')),'seconds\n')
 }
}
frame<-if(length(rows))do.call(rbind,rows) else data.frame()
if(nrow(frame)>0) {
 counts<-table(frame$rep);frame<-frame[frame$rep %in% as.numeric(names(counts[counts==3])),]
 write.csv(frame,file.path(private,'r_did.csv'),row.names=FALSE)
 z<-qnorm(.975)
 summary<-do.call(rbind,lapply(split(frame,frame$method),function(part) {
  error<-part$estimate-part$truth;n<-nrow(part);coverage<-mean(part$covered);denom<-1+z^2/n;center<-(coverage+z^2/(2*n))/denom;half<-z*sqrt(coverage*(1-coverage)/n+z^2/(4*n^2))/denom
  data.frame(method=unique(part$method),repetitions=n,bias=mean(error),rmse=sqrt(mean(error^2)),mc_se=sd(error)/sqrt(n),coverage=coverage,coverage_mc_se=sqrt(coverage*(1-coverage)/n),coverage_lo95=max(0,center-half),coverage_hi95=min(1,center+half))
 }))
 write.csv(summary,'results/v3_r_did_mc.csv',row.names=FALSE)
}
completed<-if(nrow(frame))length(unique(frame$rep)) else 0
manifest<-list(block='R_DiD',budget_seconds=600,target_repetitions=1000,completed_repetitions=completed,verified_reused_repetitions=min(100,completed),new_completed_repetitions=max(0,completed-100),replay_checks=replays,failures=failures,elapsed_seconds=as.numeric(difftime(Sys.time(),start,units='secs')),seed_sequence='20261007+rep, rep1..1000',protocol_sha256=digest::digest(file='docs/V3_PROTOCOL.md',algo='sha256'),code_sha256=digest::digest(file='scripts/v3_did_mc.R',algo='sha256'),paid_calls=0,stop_rule='time or completion only; unfinished rep excluded')
writeLines(toJSON(manifest,auto_unbox=TRUE,pretty=TRUE),'results/v3_r_did_mc_manifest.json')
cat(toJSON(manifest,auto_unbox=TRUE,pretty=TRUE),'\n')
