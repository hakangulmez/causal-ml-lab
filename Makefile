UV ?= $(or $(shell command -v uv),$(HOME)/portfolio/.tools/bin/uv)
PYTHON ?= $(UV) run python
.PHONY: policy-note setup data quick all test lint figures report readme-numbers clean
setup:
	$(UV) sync --locked
	Rscript scripts/setup_r.R
quick:
	$(UV) run python scripts/research.py --quick
lint:
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run mypy src
test:
	$(UV) run pytest
	Rscript scripts/test_r.R
all:
	$(UV) run python scripts/research.py
	$(UV) run python scripts/run_sparse.py
	$(UV) run python scripts/outputs.py
data:
	@echo "Runtime acquisition is part of make all; private data never committed."
figures readme-numbers:
	$(PYTHON) scripts/public_presentation.py
report:
	$(PYTHON) scripts/technical_report.py
policy-note:
	$(PYTHON) scripts/public_presentation.py
clean:
	@echo "Remove generated artifacts explicitly after inspecting them; no automatic data deletion."

.PHONY: v3-diagnostics v3-mc v3-balanced v3-outputs
v3-diagnostics:
	$(PYTHON) scripts/v3_diagnostics.py
v3-mc:
	OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 $(PYTHON) scripts/v3_mc.py nonlinear
	OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 VECLIB_MAXIMUM_THREADS=1 $(PYTHON) scripts/v3_mc.py sparse
	Rscript scripts/v3_did_mc.R
v3-balanced:
	Rscript scripts/v3_balanced.R
v3-outputs:
	$(PYTHON) scripts/public_presentation.py
