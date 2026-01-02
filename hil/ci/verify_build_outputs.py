# hil/ci/verify_build_outputs.py
"""
Verify that a HIL build run produced the expected artifact tree.

This is a structural and epistemic guard, not a test suite.
"""

from __future__ import annotations

import json
from pathlib import Path


REQUIRED_FILES = [
    "RUN_METADATA.json",
    "INPUT_MANIFEST.json",
    "CONFIG_SNAPSHOT.json",
    "METRICS.json",
    "FIELD_SUMMARY.json",
    "GRAPH_SUMMARY.json",
    "ARTIFACT_INDEX.json",
]

REQUIRED_HTML = [
    "index.html",
    "metrics.html",
    "field.html",
    "graph.html",
    "style.css",
]


def fail(msg: str) -> None:
    raise RuntimeError(f"[HIL CI FAIL] {msg}")


def verify_run(run_dir: Path) -> None:
    if not run_dir.exists():
        fail(f"Run directory does not exist: {run_dir}")

    for fname in REQUIRED_FILES:
        path = run_dir / fname
        if not path.exists():
            fail(f"Missing required file: {fname}")

    html_dir = run_dir / "html"
    if not html_dir.exists():
        fail("Missing html/ directory")

    for fname in REQUIRED_HTML:
        path = html_dir / fname
        if not path.exists():
            fail(f"Missing html file: html/{fname}")

    static_readme = run_dir / "static" / "README.txt"
    if not static_readme.exists():
        fail("Missing static/README.txt")

    # Minimal schema checks (do not over-validate)
    metrics = json.loads((run_dir / "METRICS.json").read_text())
    if "entropy" not in metrics or "coherence" not in metrics:
        fail("METRICS.json missing required fields")

    graph = json.loads((run_dir / "GRAPH_SUMMARY.json").read_text())
    if "num_nodes" not in graph or "num_edges" not in graph:
        fail("GRAPH_SUMMARY.json missing required fields")


def main(run_dir: str) -> None:
    verify_run(Path(run_dir))


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        fail("Usage: verify_build_outputs.py <run_dir>")
    main(sys.argv[1])
