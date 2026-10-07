"""V2 simulation only; preserves DGP1 and all empirical replications."""

from pathlib import Path

from causal_ml_lab.sparse import run

print(run(Path.cwd()))
