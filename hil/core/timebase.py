# hil/core/timebase.py

from __future__ import annotations

import time
from typing import Callable, Iterable, Any

import numpy as np


# ---------------------------------------------------------------------
# Type aliases (keep symbolic, do not over-constrain)
# ---------------------------------------------------------------------

MicroSlice = Any
MacroState = np.ndarray
ModuliGrid = Iterable[dict[str, Any]]


# ---------------------------------------------------------------------
# Utility: dispersion metric (instrument-level, explicit)
# ---------------------------------------------------------------------

def macrostate_dispersion(
    macrostates: list[MacroState],
    norm: str = "l2",
) -> float:
    """
    Compute dispersion across macrostates produced by a moduli sweep.
    """
    if len(macrostates) <= 1:
        return 0.0

    stack = np.stack(macrostates, axis=0)
    mean = stack.mean(axis=0)
    diffs = stack - mean

    if norm == "l2":
        return float(np.sqrt((diffs ** 2).sum(axis=1)).max())
    elif norm == "linf":
        return float(np.abs(diffs).max())
    else:
        raise ValueError(f"Unknown norm: {norm}")


# ---------------------------------------------------------------------
# 1. Data floor estimation
# ---------------------------------------------------------------------

def estimate_data_floor(
    *,
    slices: list[MicroSlice],
    build_macrostate: Callable[[MicroSlice, dict[str, Any]], MacroState],
    moduli_grid: ModuliGrid,
    tolerance: float,
    dispersion_norm: str = "l2",
) -> dict:
    """
    Estimate the minimum slice size that yields stable macrostates
    under admissible moduli variation.
    """

    dispersion_curve: list[float] = []

    for idx, slc in enumerate(slices):
        macrostates: list[MacroState] = []

        for params in moduli_grid:
            ms = build_macrostate(slc, params)
            macrostates.append(ms)

        disp = macrostate_dispersion(macrostates, norm=dispersion_norm)
        dispersion_curve.append(disp)

        if disp <= tolerance:
            return {
                "min_slice_index": idx,
                "min_slice_size": getattr(slc, "size", idx),
                "dispersion_curve": dispersion_curve,
            }

    return {
        "min_slice_index": None,
        "min_slice_size": None,
        "dispersion_curve": dispersion_curve,
    }


# ---------------------------------------------------------------------
# 2. Pipeline runtime benchmarking
# ---------------------------------------------------------------------

def benchmark_pipeline_runtime(
    *,
    slice: MicroSlice,
    build_macrostate: Callable[[MicroSlice], MacroState],
    runs: int = 5,
) -> dict:
    """
    Measure compute-limited tick floor.
    """

    timings: list[float] = []

    for _ in range(runs):
        start = time.perf_counter()
        _ = build_macrostate(slice)
        end = time.perf_counter()
        timings.append(end - start)

    arr = np.asarray(timings)

    return {
        "mean_runtime": float(arr.mean()),
        "max_runtime": float(arr.max()),
        "std_runtime": float(arr.std()),
        "runs": runs,
    }


# ---------------------------------------------------------------------
# 3. Tick floor estimation
# ---------------------------------------------------------------------

def estimate_tick_floor(
    *,
    data_floor: dict,
    runtime_stats: dict,
    data_rate: float | None = None,
) -> dict:
    """
    Combine data and compute floors into a minimum viable tick.
    """

    compute_limited = runtime_stats["max_runtime"]

    data_limited = None
    if data_rate is not None and data_floor.get("min_slice_size") is not None:
        data_limited = data_floor["min_slice_size"] / data_rate

    min_tick = compute_limited if data_limited is None else max(
        data_limited, compute_limited
    )

    return {
        "data_limited_tick": data_limited,
        "compute_limited_tick": compute_limited,
        "min_tick": min_tick,
    }


# ---------------------------------------------------------------------
# 4. Tick band recommendation
# ---------------------------------------------------------------------

def recommend_tick_band(
    *,
    min_tick: float,
    multiples: tuple[int, ...] = (1, 2, 5, 10),
) -> dict:
    """
    Recommend a stable operating band based on multiples
    of the minimum viable tick.
    """

    ticks = [m * min_tick for m in multiples]

    return {
        "min_tick": min_tick,
        "recommended_ticks": ticks,
        "multiples": multiples,
    }


# ---------------------------------------------------------------------
# 5. Time–frequency tradeoff diagnostics
# ---------------------------------------------------------------------

def estimate_noise_floor(
    *,
    reference_slices: list[MicroSlice],
    build_macrostate: Callable[[MicroSlice, dict[str, Any]], MacroState],
    moduli_grid: ModuliGrid,
    dispersion_norm: str = "l2",
) -> float:
    """
    Estimate instrument noise floor ε as the maximum macrostate
    dispersion induced by admissible moduli variation within a slice.
    """

    epsilons: list[float] = []

    for slc in reference_slices:
        macrostates = [
            build_macrostate(slc, params)
            for params in moduli_grid
        ]
        eps = macrostate_dispersion(macrostates, norm=dispersion_norm)
        epsilons.append(eps)

    return float(max(epsilons)) if epsilons else 0.0


def compute_resolution_ratios(
    *,
    stream,
    candidate_ticks: list[float],
    build_macrostate: Callable[[MicroSlice], MacroState],
    noise_floor: float,
) -> dict:
    """
    Compute resolution ratios R(Δt) for candidate ticks.
    """

    if noise_floor <= 0:
        raise ValueError("Noise floor must be positive")

    resolution: dict[float, float] = {}

    for dt in candidate_ticks:
        deltas: list[float] = []

        for t in stream.times(dt):
            t0 = int(t)
            t1 = int(t + dt)

            # --- critical guardrail ---
            if not stream.is_valid_index(t0) or not stream.is_valid_index(t1):
                continue
            # --------------------------

            s0 = build_macrostate(stream.slice(t0, dt))
            s1 = build_macrostate(stream.slice(t1, dt))
            deltas.append(float(np.linalg.norm(s1 - s0)))

        mean_delta = float(np.mean(deltas)) if deltas else 0.0
        resolution[dt] = mean_delta / noise_floor

    return resolution



def resolving_tick_band(
    *,
    resolution_ratios: dict[float, float],
    alpha: float,
) -> dict:
    """
    Select resolving ticks based on the time–frequency tradeoff criterion.
    """

    resolving = [
        dt for dt, R in resolution_ratios.items()
        if R >= alpha
    ]

    return {
        "alpha": alpha,
        "resolving_ticks": sorted(resolving),
        "resolution_ratios": resolution_ratios,
    }


# ---------------------------------------------------------------------
# 6. Reporting
# ---------------------------------------------------------------------

def timebase_report(
    *,
    data_floor: dict,
    runtime_stats: dict,
    tick_floor: dict,
    tick_band: dict,
    frequency_diagnostic: dict | None = None,
    covariant_path: dict | None = None,
    version: str = "v3",
) -> dict:

    report = {
        "version": version,
        "data_floor": data_floor,
        "runtime": runtime_stats,
        "tick_floor": tick_floor,
        "recommended_band": tick_band,
    }

    if frequency_diagnostic is not None:
        report["time_frequency"] = frequency_diagnostic

    if covariant_path is not None:
        report["covariant_path"] = covariant_path

    return report

