from pathlib import Path

from causal_ml_lab.v3_diagnostics import run

if __name__ == "__main__":
    run(Path(__file__).resolve().parents[1])
