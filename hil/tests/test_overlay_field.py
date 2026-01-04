# hil/tests/test_overlay_field.py
"""
Overlay operator test: calibration vs trust.

Purpose:
- Verify that independently built fields (potentially differing dimensionality)
  can be aligned and overlaid deterministically via overlay operators.
- Produce overlay artifacts (2D + 3D) as inspectable outputs.

This test does NOT:
- interpret the overlays
- compare corpora semantically
- assert regimes, labels, or thresholds
"""

from __future__ import annotations

import sys
import json
import hashlib
from pathlib import Path

import numpy as np


# ---- Repository root resolution --------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# ---- Utilities -------------------------------------------------------------

def _hash_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


# ---- Test ------------------------------------------------------------------

def test_overlay_fields():
    artifacts = REPO_ROOT / "artifacts"

    cal = artifacts / "calibration_run"
    tru = artifacts / "trust_run"

    assert cal.exists(), "calibration_run artifacts missing"
    assert tru.exists(), "trust_run artifacts missing"

    # ------------------------------------------------------------------
    # Rebuild fields via core API (instrument-consistent)
    # ------------------------------------------------------------------
    from hil.core.api import build_embedding, build_field

    def rebuild_field(corpus_path: Path) -> np.ndarray:
        assert corpus_path.exists(), f"Missing corpus: {corpus_path}"
        text = corpus_path.read_text(encoding="utf-8")
        docs = [s.strip() for s in text.split("SECTION ") if s.strip()]
        assert len(docs) >= 2, "Corpus did not split into multiple sections"
        emb = build_embedding(docs, n_components=64)
        return build_field(emb).vectors

    fields = {
        "calibration": rebuild_field(REPO_ROOT / "corpus" / "calibration.md"),
        "trust": rebuild_field(REPO_ROOT / "corpus" / "trust.md"),
    }

    # Sanity: fields may differ in dimensionality (this is allowed)
    for name, v in fields.items():
        assert v.ndim == 2
        assert v.shape[0] >= 1
        assert v.shape[1] >= 1
        assert np.isfinite(v).all(), f"{name} contains non-finite values"

    # ------------------------------------------------------------------
    # Load stability artifacts (per-field, no cross-normalization)
    # ------------------------------------------------------------------
    stability = {
        "calibration": json.loads((cal / "STABILITY.json").read_text(encoding="utf-8")),
        "trust": json.loads((tru / "STABILITY.json").read_text(encoding="utf-8")),
    }

    # ------------------------------------------------------------------
    # Produce overlays
    # ------------------------------------------------------------------
    from hil.viz.overlay_project_2d import overlay_fields_2d
    from hil.viz.overlay_project_3d import overlay_fields_3d

    out_2d = artifacts / "OVERLAY_2D.png"
    out_3d = artifacts / "OVERLAY_3D.png"

    overlay_fields_2d(fields=fields, output_path=out_2d)
    overlay_fields_3d(fields=fields, stability=stability, output_path=out_3d)

    assert out_2d.exists(), "OVERLAY_2D.png not created"
    assert out_3d.exists(), "OVERLAY_3D.png not created"

    # ------------------------------------------------------------------
    # Determinism check (render hash stable across repeated runs)
    # ------------------------------------------------------------------
    h2d_1 = _hash_bytes(out_2d.read_bytes())
    h3d_1 = _hash_bytes(out_3d.read_bytes())

    overlay_fields_2d(fields=fields, output_path=out_2d)
    overlay_fields_3d(fields=fields, stability=stability, output_path=out_3d)

    h2d_2 = _hash_bytes(out_2d.read_bytes())
    h3d_2 = _hash_bytes(out_3d.read_bytes())

    assert h2d_1 == h2d_2, "2D overlay is not deterministic"
    assert h3d_1 == h3d_2, "3D overlay is not deterministic"
