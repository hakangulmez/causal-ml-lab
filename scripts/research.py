"""Original local research; quick is synthetic and entirely offline."""

import os

os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("OMP_NUM_THREADS", "1")
import argparse
import json
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

from causal_ml_lab.pipeline import COVARIATES, run


def synthetic(n=240):
    rng = np.random.default_rng(20261007)
    x = rng.normal(size=(n, len(COVARIATES)))
    frame = pd.DataFrame(x, columns=COVARIATES)
    frame["e401"] = rng.binomial(1, 0.5, n)
    frame["net_tfa"] = 1000 * frame.e401 + 200 * x[:, 1] + rng.normal(0, 300, n)
    return frame


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--quick", action="store_true")
    args = parser.parse_args()
    root = Path.cwd()
    if args.quick:
        (root / ".cache").mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="offline-", dir=root / ".cache") as d:
            result = run(Path(d), quick=True, synthetic=synthetic())
            print(
                json.dumps(
                    dict(
                        synthetic=True,
                        network_calls=0,
                        paid_calls=0,
                        seconds=result["elapsed_seconds"],
                    )
                )
            )
    else:
        print(json.dumps(run(root)))
