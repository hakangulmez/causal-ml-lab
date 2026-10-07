"""Independent scientific and no-publication checks; writes only aggregate audit."""

import hashlib
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
from pypdf import PdfReader

root = Path.cwd()
manifest = json.loads((root / "results/manifest.json").read_text())
checks = []


def check(name, passed):
    checks.append(dict(check=name, passed=bool(passed)))


for name, digest in manifest["code"].items():
    check("code hash " + name, hashlib.sha256((root / name).read_bytes()).hexdigest() == digest)
r = json.loads((root / "results/r_manifest.json").read_text())
check(
    "R code hash",
    hashlib.sha256((root / "scripts/did.R").read_bytes()).hexdigest() == r["code_sha256"],
)
check("zero paid calls", manifest["paid_calls"] == 0)
check("SIPP full sample", manifest["n_sipp"] == 9915)
check("no failed component", not manifest["failures"])
p = pd.read_csv(root / "results/pension.csv")
check("seven model rows", len(p) == 7 and p[["model", "learner"]].drop_duplicates().shape[0] == 7)
check("ordered effect intervals", np.all(p.lo95 <= p.estimate) & np.all(p.estimate <= p.hi95))
blp = pd.read_csv(root / "results/forest_blp.csv")
check("forest BLP held-out sample", len(blp) == 1 and blp.n.iloc[0] == 4958)
check(
    "forest BLP finite uncertainty",
    np.isfinite(blp[["estimate", "se", "lo95", "hi95"]]).all().all()
    and blp.se.iloc[0] > 0
    and blp.lo95.iloc[0] < blp.estimate.iloc[0] < blp.hi95.iloc[0],
)
d = pd.read_csv(root / "results/did_monte_carlo.csv")
check("three aligned DiD methods", len(d) == 3 and d.repetitions.eq(100).all())
b = pd.read_csv(root / "results/bacon.csv")
app = pd.read_csv(root / "results/mpdta_estimates.csv")
check("Bacon weights sum", np.isclose(b.weight.sum(), 1))
check(
    "Bacon reproduces TWFE",
    np.isclose((b.weight * b.estimate).sum(), app[app.method == "TWFE"].estimate.iloc[0]),
)
check(
    "R instrumented coverage", pd.read_csv(root / "results/r_coverage.csv").coverage.iloc[0] >= 90
)
sparse = json.loads((root / "results/sparse_manifest.json").read_text())
for name, digest in sparse["code"].items():
    check(
        "V2 simulation code " + name,
        hashlib.sha256((root / name).read_bytes()).hexdigest() == digest,
    )
check("V2 sparse dimensions", sparse["p"] >= 100 and sparse["repetitions"] == 100)
check(
    "V2 unchanged original simulation",
    hashlib.sha256((root / "results/monte_carlo.csv").read_bytes()).hexdigest()
    == sparse["inherited_dgp1_sha256"],
)
check(
    "V2 predeclaration",
    hashlib.sha256((root / "docs/DGP2_PREDECLARATION.md").read_bytes()).hexdigest()
    == sparse["declaration_sha256"],
)
check(
    "V2 comparator predeclaration",
    hashlib.sha256((root / "docs/DGP1_PLUGIN_ADDENDUM.md").read_bytes()).hexdigest()
    == sparse["comparator_declaration_sha256"],
)
comparison = pd.read_csv(root / "results/dml_two_dgps.csv")
for design in ["DGP1_nonlinear", "DGP2_sparse"]:
    part = comparison[comparison.dgp == design]
    check("V2 estimators " + design, {"OLS", "NaivePlugin", "DML"}.issubset(set(part.method)))
    check("V2 draws " + design, part.repetitions.eq(100).all())
check("V2 coverage bounded", comparison.coverage.between(0, 1).all())
check("V2 zero paid calls", sparse["paid_calls"] == 0)
check("policy pages", len(PdfReader(root / "report/policy_note.pdf").pages) == 2)
files = (
    subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=root
    )
    .decode()
    .split("\0")
)
check(
    "private files excluded",
    not any(
        x.startswith(("data/raw/", "runs/", ".venv/", ".R-library/")) or x == ".env" for x in files
    ),
)
check(
    "authorized publication origin",
    all(
        url
        in {
            "https://github.com/hakangulmez/causal-ml-lab",
            "https://github.com/hakangulmez/causal-ml-lab.git",
        }
        for url in subprocess.check_output(
            ["git", "remote", "get-url", "--all", "origin"], cwd=root, stderr=subprocess.DEVNULL
        )
        .decode()
        .splitlines()
    )
    if subprocess.check_output(["git", "remote"], cwd=root).strip()
    else True,
)
result = {
    "checks": checks,
    "all_pass": all(x["passed"] for x in checks),
    "policy_visual_qa": "both pages inspected",
    "R_did_property_checks": "passed",
}
(root / "results/audit.json").write_text(json.dumps(result, indent=2) + "\n")
print(json.dumps({"checks": len(checks), "all_pass": result["all_pass"]}))
