"""
Vertical calibration test: canonical academic text (Hempel-style).

Purpose:
- Exercise a full vertical slice of the HIL instrument
- Verify non-degenerate, deterministic metric output
- Persist inspectable artifacts
- Produce deterministic 2D and 3D visualizations as read-only projections

This test does NOT:
- validate correctness of philosophy
- classify texts
- assert regime labels
- interpret visual output
"""

from __future__ import annotations

import json
import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest


# ---- Repository root resolution --------------------------------------------

# test file is at: hil/tests/test_calibration_vertical_slice.py
# repo root is therefore two levels up
REPO_ROOT = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---- Configuration ---------------------------------------------------------

CORPUS_PATH = REPO_ROOT / "corpus" / "calibration.md"
ARTIFACT_DIR = REPO_ROOT / "artifacts" / "calibration_run"

EXPECTED_ARTIFACTS = [
    "INPUT_MANIFEST.json",
    "EMBEDDING_SUMMARY.json",
    "FIELD_SUMMARY.json",
    "GRAPH_SUMMARY.json",
    "METRICS.json",
    "STABILITY.json",
    "FIELD_PROJECTION_2D.png",
    "FIELD_PROJECTION_3D.png",
]


# ---- Utilities -------------------------------------------------------------

def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _ensure_clean_dir(path: Path) -> None:
    if path.exists():
        for p in path.iterdir():
            if p.is_file():
                p.unlink()
    else:
        path.mkdir(parents=True, exist_ok=True)


# ---- Test ------------------------------------------------------------------

def test_calibration_vertical_slice():
    """
    End-to-end calibration test.

    The test passes if:
    - the corpus is non-empty
    - embeddings, field, and graph are constructed
    - metrics and stability are finite and non-degenerate
    - deterministic 2D and 3D visualizations are produced
    - artifacts are written
    - results are deterministic across runs
    """

    # ------------------------------------------------------------------
    # 1. Load corpus
    # ------------------------------------------------------------------
    assert CORPUS_PATH.exists(), f"Calibration corpus not found at {CORPUS_PATH}"

    text = CORPUS_PATH.read_text(encoding="utf-8").strip()
    assert len(text) > 0, "Calibration corpus is empty"

    corpus_hash = _hash_bytes(text.encode("utf-8"))

    documents = [
        s.strip()
        for s in text.split("SECTION ")
        if s.strip()
    ]

    assert len(documents) > 1, "Calibration corpus did not split into sections"

    # ------------------------------------------------------------------
    # 2. Prepare output directory
    # ------------------------------------------------------------------
    _ensure_clean_dir(ARTIFACT_DIR)

    # ------------------------------------------------------------------
    # 3. Import core API
    # ------------------------------------------------------------------
    from hil.core.api import (
        build_embedding,
        build_field,
        build_structure,
        compute_diagnostics,
    )

    # ------------------------------------------------------------------
    # 4. Build embedding
    # ------------------------------------------------------------------
    embedding = build_embedding(documents, n_components=64)

    assert embedding.vectors.shape[0] == len(documents)
    assert 1 <= embedding.vectors.shape[1] <= len(documents) - 1
    assert np.isfinite(embedding.vectors).all()

    (ARTIFACT_DIR / "EMBEDDING_SUMMARY.json").write_text(
        json.dumps(
            {
                "num_documents": embedding.vectors.shape[0],
                "dimensions": embedding.vectors.shape[1],
            },
            indent=2,
        )
    )

    # ------------------------------------------------------------------
    # 5. Build field
    # ------------------------------------------------------------------
    field = build_field(embedding)

    (ARTIFACT_DIR / "FIELD_SUMMARY.json").write_text(
        json.dumps(
            {
                "num_elements": field.vectors.shape[0],
                "dimension": field.vectors.shape[1],
            },
            indent=2,
        )
    )

    # ------------------------------------------------------------------
    # 6. Build graph
    # ------------------------------------------------------------------
    graph = build_structure(field)

    (ARTIFACT_DIR / "GRAPH_SUMMARY.json").write_text(
        json.dumps(
            {
                "num_nodes": graph.num_nodes,
                "num_edges": int(graph.src.size),
            },
            indent=2,
        )
    )

    # ------------------------------------------------------------------
    # 7. Compute diagnostics
    # ------------------------------------------------------------------
    metrics = compute_diagnostics(field, graph)

    numeric = [v for v in metrics.values() if isinstance(v, float)]
    assert any(v != 0.0 for v in numeric), "Degenerate diagnostics"

    (ARTIFACT_DIR / "METRICS.json").write_text(
        json.dumps(metrics, indent=2)
    )

    # ------------------------------------------------------------------
    # 7a. Compute stability (leave-one-out)
    # ------------------------------------------------------------------
    from hil.core.metrics.stability import structural_stability_leave_one_out

    stability = structural_stability_leave_one_out(
        field_vectors=field.vectors,
        graph=graph,
    )

    assert isinstance(stability, dict)
    assert len(stability) == field.vectors.shape[0]
    assert all(np.isfinite(v) and v >= 0.0 for v in stability.values())

    (ARTIFACT_DIR / "STABILITY.json").write_text(
        json.dumps(stability, indent=2)
    )

    # ------------------------------------------------------------------
    # 8. 2D visualization
    # ------------------------------------------------------------------
    from hil.viz.project_2d import project_field_2d

    path_2d = ARTIFACT_DIR / "FIELD_PROJECTION_2D.png"

    project_field_2d(
        field_vectors=field.vectors,
        graph=graph,
        output_path=path_2d,
        method="pca",
    )

    assert path_2d.exists()

    # ------------------------------------------------------------------
    # 9. 3D visualization (contract only)
    # ------------------------------------------------------------------
    from hil.viz.project_3d import project_field_3d

    path_3d = ARTIFACT_DIR / "FIELD_PROJECTION_3D.png"

    project_field_3d(
        field_vectors=field.vectors,
        stability=stability,
        output_path=path_3d,
        method="pca",
    )

    assert path_3d.exists()

    # ------------------------------------------------------------------
    # 10. Input manifest
    # ------------------------------------------------------------------
    (ARTIFACT_DIR / "INPUT_MANIFEST.json").write_text(
        json.dumps(
            {
                "corpus_path": str(CORPUS_PATH),
                "corpus_hash": corpus_hash,
                "num_documents": len(documents),
            },
            indent=2,
        )
    )

    # ------------------------------------------------------------------
    # 11. Verify artifacts
    # ------------------------------------------------------------------
    for name in EXPECTED_ARTIFACTS:
        assert (ARTIFACT_DIR / name).exists(), f"Missing artifact: {name}"

    # ------------------------------------------------------------------
    # 12. Determinism checks
    # ------------------------------------------------------------------
    assert compute_diagnostics(field, graph) == metrics

    h1 = _hash_bytes(path_2d.read_bytes())
    project_field_2d(field_vectors=field.vectors, graph=graph, output_path=path_2d)
    h2 = _hash_bytes(path_2d.read_bytes())
    assert h1 == h2

    h1 = _hash_bytes(path_3d.read_bytes())
    project_field_3d(
        field_vectors=field.vectors,
        stability=stability,
        output_path=path_3d,
        method="pca",
    )
    h2 = _hash_bytes(path_3d.read_bytes())
    assert h1 == h2
