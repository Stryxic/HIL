# hil/ci/run_ci.py
"""
Minimal CI runner for HIL.

Assumes:
- correct Conda environment already activated
- repo root as working directory
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def fail(msg: str) -> None:
    raise RuntimeError(f"[HIL CI FAIL] {msg}")


def run_build() -> None:
    cmd = [sys.executable, "-m", "hil.build.hil_build"]
    subprocess.check_call(cmd)


def latest_run_dir(runs_root: Path) -> Path:
    runs = sorted(
        (p for p in runs_root.iterdir() if p.is_dir()),
        key=lambda p: p.name,
    )
    if not runs:
        fail("No runs found in artifacts/runs/")
    return runs[-1]


def load_metrics(run_dir: Path) -> dict:
    return json.loads((run_dir / "METRICS.json").read_text())


def main() -> None:
    repo_root = Path.cwd()
    runs_root = repo_root / "artifacts" / "runs"

    if not runs_root.exists():
        fail("artifacts/runs/ does not exist")

    # First run
    run_build()
    run1 = latest_run_dir(runs_root)
    m1 = load_metrics(run1)

    # Second run (determinism check)
    run_build()
    run2 = latest_run_dir(runs_root)
    m2 = load_metrics(run2)

    if m1 != m2:
        fail("METRICS.json is not deterministic across runs")

    # Verify artifact shape
    subprocess.check_call(
        [sys.executable, "-m", "hil.ci.verify_build_outputs", str(run2)]
    )

    print("[HIL CI PASS] Build, artifacts, and determinism verified")


if __name__ == "__main__":
    main()
