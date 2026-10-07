UV ?= $(or $(shell command -v uv),$(HOME)/portfolio/.tools/bin/uv)
.PHONY: setup data quick all test lint figures report readme-numbers clean
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
	$(UV) run python scripts/outputs.py
report:
	$(UV) run python scripts/outputs.py
clean:
	@echo "Remove generated artifacts explicitly after inspecting them; no automatic data deletion."
