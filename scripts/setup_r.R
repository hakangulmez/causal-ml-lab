# Install pinned primary research packages into this repository only.
lib <- normalizePath('.R-library',mustWork=FALSE)
dir.create(lib,showWarnings=FALSE,recursive=TRUE)
.libPaths(c(lib,.libPaths()))
versions <- c(did='2.3.0',HonestDiD='0.2.6',fixest='0.13.2',bacondecomp='0.1.1',lazyeval='0.2.2',covr='3.6.5')
db <- available.packages(repos="https://cloud.r-project.org")
deps <- unique(unlist(tools::package_dependencies(names(versions),db=db,recursive=TRUE)))
missing <- deps[!vapply(deps,requireNamespace,logical(1),quietly=TRUE)]
if(length(missing)) install.packages(missing,lib=lib,repos="https://cloud.r-project.org")
for (name in names(versions)) {
  if (file.exists(file.path(lib,name,'DESCRIPTION'))) next
  # Dependencies already available are read-only; missing ones use this same lib.
  url <- sprintf('https://cran.r-project.org/src/contrib/%s_%s.tar.gz',name,versions[[name]])
  file <- tempfile(fileext='.tar.gz')
  ok <- tryCatch({download.file(url,file,quiet=TRUE);TRUE},error=function(e)FALSE)
  if (!ok) {
    url <- sprintf('https://cran.r-project.org/src/contrib/Archive/%s/%s_%s.tar.gz',name,name,versions[[name]])
    download.file(url,file,quiet=TRUE)
  }
  install.packages(file,repos=NULL,type='source',lib=lib)
  if (!requireNamespace(name,quietly=TRUE)) stop(paste('Package load failed',name))
}
cat('Repository R environment ready\n')
