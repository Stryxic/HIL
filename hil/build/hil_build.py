# hil/build/hil_build.py
"""
hil.build.hil_build

Single-entry build script for the first HIL diagnostic run.

This script:
- constructs a bounded run context,
- loads an explicit self-corpus,
- executes the epistemic core pipeline,
- writes diagnostic artifacts to disk,
- and optionally serves a local-only static HTML view.

Invariants:
- Diagnostic only (no labels, no thresholds, no decisions)
- Deterministic given fixed inputs
- Local-only (no federation, no external hosting)
- No persistence beyond artifact writing
- No mutation of source materials
"""

from __future__ import annotations

import json
import hashlib
import os
import sys
import time
import platform
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# --- Core imports (epistemic kernel) -----------------------------------------
from hil.core.api import (
    build_embedding,
    build_field,
    build_structure,
    compute_diagnostics,
)

# --- Configuration (explicit, human-readable) --------------------------------

EMBEDDING_CONFIG = {
    "method": "lsa",
    "dimensions": 300,
}

STRUCTURE_CONFIG = {
    "method": "temporary_scaffold",
    "notes": "fully connected or trivial structure for sanity run",
}

METRICS_CONFIG = {
    "entropy": "structural",
    "coherence": "centroid_cosine",
    "stability": None,
}

# --- Helpers -----------------------------------------------------------------

def utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def git_commit_hash() -> str | None:
    try:
        return (
            subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL)
            .decode()
            .strip()
        )
    except Exception:
        return None


# --- Corpus loading ----------------------------------------------------------

def load_self_corpus(repo_root: Path) -> List[str]:
    """
    Load a bounded, explicit self-corpus.

    This is not crawling. It is a mirror of selected, declared files.
    """
    targets = [
        repo_root / "README.md",
        repo_root / "CHARTER.md",
        repo_root / "ROADMAP.md",
        repo_root / "NON_CLAIMS.md",
    ]

    documents: List[str] = []
    for p in targets:
        if p.exists():
            documents.append(p.read_text(encoding="utf-8"))
    return documents


def build_input_manifest(repo_root: Path) -> Dict[str, Any]:
    files = []
    for rel in ["README.md", "CHARTER.md", "ROADMAP.md", "NON_CLAIMS.md"]:
        p = repo_root / rel
        if p.exists():
            files.append(
                {
                    "path": rel,
                    "sha256": sha256_file(p),
                }
            )

    return {
        "corpus_type": "self",
        "files": files,
    }


# --- Artifact writers --------------------------------------------------------

def write_json(path: Path, obj: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, sort_keys=True)


# --- Main build --------------------------------------------------------------

def main() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    run_id = time.strftime("run_%Y%m%d_%H%M%S", time.gmtime())
    run_root = repo_root / "artifacts" / "runs" / run_id

    html_dir = run_root / "html"
    static_dir = run_root / "static"

    # Create directories
    html_dir.mkdir(parents=True, exist_ok=False)
    static_dir.mkdir(parents=True, exist_ok=False)

    # ------------------------------------------------------------------
    # RUN_METADATA.json
    # ------------------------------------------------------------------
    run_metadata = {
        "run_id": run_id,
        "timestamp_utc": utc_timestamp(),
        "hil_version": "sanity-kernel",
        "git_commit": git_commit_hash(),
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
    }
    write_json(run_root / "RUN_METADATA.json", run_metadata)

    # ------------------------------------------------------------------
    # INPUT_MANIFEST.json
    # ------------------------------------------------------------------
    input_manifest = build_input_manifest(repo_root)
    write_json(run_root / "INPUT_MANIFEST.json", input_manifest)

    # ------------------------------------------------------------------
    # CONFIG_SNAPSHOT.json
    # ------------------------------------------------------------------
    config_snapshot = {
        "embedding": EMBEDDING_CONFIG,
        "structure": STRUCTURE_CONFIG,
        "metrics": METRICS_CONFIG,
    }
    write_json(run_root / "CONFIG_SNAPSHOT.json", config_snapshot)

    # ------------------------------------------------------------------
    # Load corpus and run epistemic core
    # ------------------------------------------------------------------
    documents = load_self_corpus(repo_root)

    embedding = build_embedding(
        documents,
        n_components=EMBEDDING_CONFIG["dimensions"],
    )
    field = build_field(embedding)
    graph = build_structure(field)
    diagnostics = compute_diagnostics(field, graph)

    # ------------------------------------------------------------------
    # METRICS.json
    # ------------------------------------------------------------------
    write_json(run_root / "METRICS.json", diagnostics)

    # ------------------------------------------------------------------
    # FIELD_SUMMARY.json
    # ------------------------------------------------------------------
    field_summary = {
        "num_elements": int(field.vectors.shape[0]),
        "dimensions": int(field.vectors.shape[1]),
        "centroid_norm": float(
            (field.vectors.mean(axis=0) ** 2).sum() ** 0.5
        ),
        "mean_vector_norm": float(
            ((field.vectors ** 2).sum(axis=1) ** 0.5).mean()
        ),
    }
    write_json(run_root / "FIELD_SUMMARY.json", field_summary)

    # ------------------------------------------------------------------
    # GRAPH_SUMMARY.json
    # ------------------------------------------------------------------
    graph_summary = {
        "num_nodes": graph.num_nodes,
        "num_edges": graph.num_edges,
    }
    write_json(run_root / "GRAPH_SUMMARY.json", graph_summary)

    # ------------------------------------------------------------------
    # ARTIFACT_INDEX.json
    # ------------------------------------------------------------------
    artifact_index = {
        "run_id": run_id,
        "artifacts": {
            "metrics": "METRICS.json",
            "field": "FIELD_SUMMARY.json",
            "graph": "GRAPH_SUMMARY.json",
            "html": "html/index.html",
        },
    }
    write_json(run_root / "ARTIFACT_INDEX.json", artifact_index)

    # ------------------------------------------------------------------
    # HTML scaffold (static placeholders)
    # ------------------------------------------------------------------
    (html_dir / "index.html").write_text(
        "<h1>HIL Sanity Run</h1><p>See metrics.html, field.html, graph.html</p>",
        encoding="utf-8",
    )
    (html_dir / "metrics.html").write_text("<pre>METRICS.json</pre>", encoding="utf-8")
    (html_dir / "field.html").write_text("<pre>FIELD_SUMMARY.json</pre>", encoding="utf-8")
    (html_dir / "graph.html").write_text("<pre>GRAPH_SUMMARY.json</pre>", encoding="utf-8")
    (html_dir / "style.css").write_text("body { font-family: sans-serif; }", encoding="utf-8")

    # ------------------------------------------------------------------
    # static/README.txt
    # ------------------------------------------------------------------
    (static_dir / "README.txt").write_text(
        "This directory contains artifacts generated by hil_build.\n"
        "These files are diagnostic outputs, not conclusions or recommendations.\n"
        "They are intended for human inspection only.\n",
        encoding="utf-8",
    )

    print(f"[HIL BUILD COMPLETE] Artifacts written to: {run_root}")


if __name__ == "__main__":
    main()
