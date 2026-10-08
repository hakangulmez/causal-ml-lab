import sys
from pathlib import Path

from causal_ml_lab.v3_mc import run_block

if __name__ == "__main__":
    run_block(Path(__file__).resolve().parents[1], sys.argv[1])
