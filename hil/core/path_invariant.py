# hil/core/path_covariant.py

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable, Any, List

import numpy as np

from hil.core.stream import StreamProtocol


# ---------------------------------------------------------------------
# Symbolic aliases
# ---------------------------------------------------------------------

MicroSlice = Any
TimeIndex = Any


# ---------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class CovariantPath:
    anchors: List[TimeIndex]          # ordered anchors
    sigmas: np.ndarray                # shape (m, k)
    ds: np.ndarray                    # shape (m-1,)
    s: np.ndarray                     # shape (m,)


@dataclass(frozen=True)
class PathBands:
    sigma_center: np.ndarray          # shape (m, k)
    sigma_dispersion: np.ndarray      # shape (m,)


# ---------------------------------------------------------------------
# 1. Path construction
# ---------------------------------------------------------------------

def build_path(
    *,
    stream: StreamProtocol,
    dt: float,
    build_macrostate: Callable[[MicroSlice], np.ndarray],
    anchors: List[TimeIndex] | None = None,
    require_pair_valid: bool = True,
) -> CovariantPath:
    """
    Build an irregular-time covariant path and its arc-length parameterization.
    """

    if anchors is None:
        anchors = list(stream.times(dt))

    valid_anchors: List[TimeIndex] = []

    for t in anchors:
        if not stream.is_valid_time(t):
            continue
        if require_pair_valid:
            try:
                t_next = t + dt
            except Exception:
                continue
            if not stream.is_valid_time(t_next):
                continue
        valid_anchors.append(t)

    sigmas: List[np.ndarray] = []

    for t in valid_anchors:
        slc = stream.slice(t, dt)
        sigma = build_macrostate(slc)
        sigmas.append(np.asarray(sigma, dtype=float))

    if len(sigmas) == 0:
        return CovariantPath([], np.empty((0, 0)), np.empty((0,)), np.empty((0,)))

    sigmas_arr = np.stack(sigmas, axis=0)

    if len(sigmas_arr) == 1:
        return CovariantPath(
            anchors=valid_anchors,
            sigmas=sigmas_arr,
            ds=np.empty((0,)),
            s=np.zeros((1,)),
        )

    deltas = sigmas_arr[1:] - sigmas_arr[:-1]
    ds = np.linalg.norm(deltas, axis=1)
    s = np.concatenate(([0.0], np.cumsum(ds)))

    return CovariantPath(
        anchors=valid_anchors,
        sigmas=sigmas_arr,
        ds=ds,
        s=s,
    )


# ---------------------------------------------------------------------
# 2. Reparameterization (formal boundary)
# ---------------------------------------------------------------------

def reparameterize_arclength(
    *,
    path: CovariantPath,
) -> CovariantPath:
    """
    Return the same path, guaranteed arc-length parameterization.
    (Currently identity; included for formal completeness.)
    """
    return path


# ---------------------------------------------------------------------
# 3. Covariant geometric observables
# ---------------------------------------------------------------------

def covariant_metrics(
    *,
    path: CovariantPath,
    curvature_eps: float = 1e-12,
) -> dict:
    """
    Compute reparameterization-invariant geometric observables.
    """

    m = path.sigmas.shape[0]
    k = path.sigmas.shape[1] if m > 0 else 0

    metrics: dict[str, Any] = {
        "m": m,
        "k": k,
        "arc_length_L": float(path.ds.sum()) if path.ds.size else 0.0,
    }

    if m <= 1:
        metrics.update(
            {
                "diameter_D": 0.0,
                "total_turning_K": 0.0,
                "turning_angles": [],
                "curvature_proxy": [],
            }
        )
        return metrics

    # Diameter
    D = 0.0
    for i in range(m):
        for j in range(i + 1, m):
            d = float(np.linalg.norm(path.sigmas[j] - path.sigmas[i]))
            if d > D:
                D = d

    metrics["diameter_D"] = D

    # Turning angles and curvature
    turning_angles: List[float] = []
    curvature: List[float] = []

    for i in range(1, m - 1):
        v_prev = path.sigmas[i] - path.sigmas[i - 1]
        v_next = path.sigmas[i + 1] - path.sigmas[i]

        n_prev = np.linalg.norm(v_prev)
        n_next = np.linalg.norm(v_next)

        if n_prev < curvature_eps or n_next < curvature_eps:
            continue

        u_prev = v_prev / n_prev
        u_next = v_next / n_next

        cos_theta = float(np.clip(np.dot(u_prev, u_next), -1.0, 1.0))
        theta = float(np.arccos(cos_theta))
        turning_angles.append(theta)

        denom = n_prev + n_next
        if denom > curvature_eps:
            curvature.append(theta / denom)

    metrics["turning_angles"] = turning_angles
    metrics["total_turning_K"] = float(np.sum(turning_angles)) if turning_angles else 0.0
    metrics["curvature_proxy"] = curvature

    return metrics


# ---------------------------------------------------------------------
# 4. Moduli-stabilized uncertainty bands
# ---------------------------------------------------------------------

def path_bands(
    *,
    stream: StreamProtocol,
    dt: float,
    anchors: List[TimeIndex],
    build_macrostate_param: Callable[[MicroSlice, dict[str, Any]], np.ndarray],
    moduli_grid: Iterable[dict[str, Any]],
    center: str = "median",
    dispersion_norm: str = "l2",
) -> PathBands:
    """
    Compute per-anchor center macrostate and dispersion across moduli.
    """

    sigma_centers: List[np.ndarray] = []
    sigma_disp: List[float] = []

    for t in anchors:
        macrostates: List[np.ndarray] = []
        for params in moduli_grid:
            slc = stream.slice(t, dt)
            macrostates.append(
                np.asarray(build_macrostate_param(slc, params), dtype=float)
            )

        stack = np.stack(macrostates, axis=0)

        if center == "median":
            center_sigma = np.median(stack, axis=0)
        elif center == "mean":
            center_sigma = stack.mean(axis=0)
        else:
            raise ValueError(f"Unknown center: {center}")

        diffs = stack - center_sigma

        if dispersion_norm == "l2":
            disp = float(np.sqrt((diffs ** 2).sum(axis=1)).max())
        elif dispersion_norm == "linf":
            disp = float(np.abs(diffs).max())
        else:
            raise ValueError(f"Unknown norm: {dispersion_norm}")

        sigma_centers.append(center_sigma)
        sigma_disp.append(disp)

    return PathBands(
        sigma_center=np.stack(sigma_centers, axis=0),
        sigma_dispersion=np.asarray(sigma_disp, dtype=float),
    )


# ---------------------------------------------------------------------
# 5. Coordinate-dependent rates (explicitly non-covariant)
# ---------------------------------------------------------------------

def coordinate_dependent_rates(
    *,
    path: CovariantPath,
    time_map: Callable[[TimeIndex], float],
    eps_time: float = 1e-12,
) -> dict:
    """
    Compute rates per unit time using an explicit time_map.
    """

    if path.ds.size == 0:
        return {
            "dtau": [],
            "speed": [],
            "mean_speed": 0.0,
            "max_speed": 0.0,
        }

    taus = [time_map(t) for t in path.anchors]
    taus = np.asarray(taus, dtype=float)

    dtau = taus[1:] - taus[:-1]

    speed: List[float] = []
    for d, t in zip(path.ds, dtau):
        if t > eps_time:
            speed.append(float(d / t))

    return {
        "dtau": dtau.tolist(),
        "speed": speed,
        "mean_speed": float(np.mean(speed)) if speed else 0.0,
        "max_speed": float(np.max(speed)) if speed else 0.0,
    }


# ---------------------------------------------------------------------
# 6. Reporting
# ---------------------------------------------------------------------

def path_report(
    *,
    path: CovariantPath,
    covariant: dict,
    bands: PathBands | None = None,
    coordinate_dependent: dict | None = None,
    version: str = "v1",
) -> dict:
    """
    JSON-serializable artifact for a covariant path.
    """

    report: dict[str, Any] = {
        "version": version,
        "anchors": [str(a) for a in path.anchors],
        "sigmas": path.sigmas.tolist(),
        "arc_length_s": path.s.tolist(),
        "covariant_metrics": covariant,
    }

    if bands is not None:
        report["bands"] = {
            "sigma_center": bands.sigma_center.tolist(),
            "sigma_dispersion": bands.sigma_dispersion.tolist(),
        }

    if coordinate_dependent is not None:
        report["coordinate_dependent"] = coordinate_dependent

    return report
