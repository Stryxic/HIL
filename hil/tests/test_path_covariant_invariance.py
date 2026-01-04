# tests/test_path_covariant_invariance.py

import numpy as np
import pytest

from hil.core.path_invariant import (
    build_path,
    covariant_metrics,
)


# ---------------------------------------------------------------------
# Dummy infrastructure (deterministic, geometry-friendly)
# ---------------------------------------------------------------------

class DummySlice:
    def __init__(self, value: float):
        self.value = value


class DummyStream:
    """
    Deterministic stream with monotonically increasing structure.
    """

    def __init__(self, slices):
        self._slices = slices

    def times(self, dt):
        # Integer anchors
        return list(range(len(self._slices)))

    def slice(self, t, dt):
        return self._slices[t]

    def is_valid_time(self, t):
        return isinstance(t, int) and 0 <= t < len(self._slices)


def build_macrostate(slice_obj: DummySlice) -> np.ndarray:
    """
    Embed value into a simple 2D curve so curvature is non-zero.
    """
    x = slice_obj.value
    return np.array([x, x ** 2], dtype=float)


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_covariant_path_invariance_under_resampling():
    """
    Covariant metrics must be invariant (within tolerance) under
    monotone reparameterization / resampling of anchors.
    """

    # Build deterministic underlying stream
    values = [0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
    slices = [DummySlice(v) for v in values]
    stream = DummyStream(slices)

    # Dense sampling
    dense_anchors = list(range(len(values)))

    # Sparse (monotone reparameterization)
    sparse_anchors = [0, 2, 4, 5]

    path_dense = build_path(
        stream=stream,
        dt=1.0,
        build_macrostate=build_macrostate,
        anchors=dense_anchors,
    )

    path_sparse = build_path(
        stream=stream,
        dt=1.0,
        build_macrostate=build_macrostate,
        anchors=sparse_anchors,
    )

    metrics_dense = covariant_metrics(path=path_dense)
    metrics_sparse = covariant_metrics(path=path_sparse)

    # -----------------------------------------------------------------
    # Invariance assertions
    # -----------------------------------------------------------------

    # Diameter must be invariant
    assert metrics_dense["diameter_D"] == pytest.approx(
        metrics_sparse["diameter_D"],
        rel=1e-6,
    )

    # Arc length: dense >= sparse (undersampling shortens path)
    assert metrics_dense["arc_length_L"] >= metrics_sparse["arc_length_L"]

    # Turning (total curvature) should be close if sampling resolves curvature
    assert abs(
        metrics_dense["total_turning_K"] -
        metrics_sparse["total_turning_K"]
    ) < 1e-6


def test_covariant_metrics_independent_of_anchor_spacing():
    """
    Same geometric curve, different anchor spacing → same invariants.
    """

    values = [0.0, 1.0, 2.0, 3.0]
    slices = [DummySlice(v) for v in values]
    stream = DummyStream(slices)

    anchors_a = [0, 1, 2, 3]
    anchors_b = [0, 2, 3]

    path_a = build_path(
        stream=stream,
        dt=1.0,
        build_macrostate=build_macrostate,
        anchors=anchors_a,
    )

    path_b = build_path(
        stream=stream,
        dt=1.0,
        build_macrostate=build_macrostate,
        anchors=anchors_b,
    )

    m_a = covariant_metrics(path=path_a)
    m_b = covariant_metrics(path=path_b)

    assert m_a["diameter_D"] == pytest.approx(m_b["diameter_D"], rel=1e-6)
    assert m_a["total_turning_K"] == pytest.approx(
        m_b["total_turning_K"],
        rel=1e-6,
    )


def test_path_with_single_anchor_is_well_defined():
    """
    Degenerate path must not crash and must yield zero geometry.
    """

    slices = [DummySlice(1.0)]
    stream = DummyStream(slices)

    path = build_path(
        stream=stream,
        dt=1.0,
        build_macrostate=build_macrostate,
        anchors=[0],
    )

    metrics = covariant_metrics(path=path)

    assert metrics["arc_length_L"] == 0.0
    assert metrics["diameter_D"] == 0.0
    assert metrics["total_turning_K"] == 0.0
