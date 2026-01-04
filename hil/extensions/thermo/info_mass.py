# hil/extensions/thermo/info_mass.py

from __future__ import annotations

from typing import Protocol, Any
import numpy as np

from hil.core.path_invariant import CovariantPath


# ---------------------------------------------------------------------
# Symbolic aliases
# ---------------------------------------------------------------------

HilbertPath = CovariantPath
NoiseBand = float | np.ndarray
Mass = float
Energy = float
Entropy = float


# ---------------------------------------------------------------------
# Fiber entropy backend protocol
# ---------------------------------------------------------------------

class FiberEntropyBackend(Protocol):
    """
    Backend defining entropy over the deconsolidation fiber μ_σ.

    Implementations MUST:
    - declare their reference measure externally,
    - be deterministic for fixed inputs,
    - not depend on time parameterization.
    """

    def entropy(self, sigma: np.ndarray) -> float:
        ...


# ---------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------

def _broadcast_noise(
    noise: NoiseBand,
    length: int,
) -> np.ndarray:
    """
    Broadcast scalar or vector noise to a vector of given length.
    """
    if np.isscalar(noise):
        return np.full(length, float(noise))
    noise_arr = np.asarray(noise, dtype=float)
    if noise_arr.shape != (length,):
        raise ValueError(
            f"Noise must be scalar or shape ({length},), got {noise_arr.shape}"
        )
    return noise_arr


# ---------------------------------------------------------------------
# 1. Thresholded structural increments
# ---------------------------------------------------------------------

def thresholded_increments(
    *,
    path: HilbertPath,
    noise: NoiseBand,
    alpha: float = 1.0,
) -> np.ndarray:
    """
    Compute noise-thresholded arc-length increments:

        Δs_i^(α) = max(0, ||Δσ_i|| − α ε_i)
    """

    if path.ds.size == 0:
        return np.empty((0,), dtype=float)

    eps = _broadcast_noise(noise, len(path.ds))
    return np.maximum(0.0, path.ds - alpha * eps)


# ---------------------------------------------------------------------
# 2. Informational mass
# ---------------------------------------------------------------------

def informational_mass(
    *,
    path: HilbertPath,
    noise: NoiseBand,
    alpha: float = 1.0,
) -> Mass:
    """
    Covariant informational mass.

    Semantics:
    - Scalar `noise` is an ABSOLUTE resolution threshold.
      The path must exceed α·ε in total arc-length to resolve structure.
    - Vector `noise` is a per-segment uncertainty budget and is summed.

    Definition:
        S = Σ ||Δσ||
        If scalar ε:
            M = max(0, S − α·ε)
        If vector ε_i:
            M = max(0, S − α·Σ ε_i)
    """

    S = float(path.ds.sum())
    if S == 0.0:
        return 0.0

    if np.isscalar(noise):
        eps = float(noise)
        return float(max(0.0, S - alpha * eps))

    eps = np.asarray(noise, dtype=float)
    if eps.shape != (len(path.ds),):
        raise ValueError(
            f"Noise must be scalar or shape ({len(path.ds)},), got {eps.shape}"
        )

    return float(max(0.0, S - alpha * float(eps.sum())))




# ---------------------------------------------------------------------
# 3. Informational mass density
# ---------------------------------------------------------------------

def informational_mass_density(
    *,
    path: HilbertPath,
    noise: NoiseBand,
    alpha: float = 1.0,
    delta: float = 1e-12,
) -> float:
    """
    Fraction of total arc-length that is noise-certified.
    """

    total = float(path.ds.sum())
    mass = informational_mass(
        path=path,
        noise=noise,
        alpha=alpha,
    )
    return float(mass / (total + delta))


# ---------------------------------------------------------------------
# 4. Informational energy
# ---------------------------------------------------------------------

def informational_energy(
    *,
    mass: Mass,
    scale: float = 1.0,
) -> Energy:
    """
    Linear informational energy model:

        U = λ M_info
    """
    return float(scale * mass)


# ---------------------------------------------------------------------
# 5. Path entropy (covariant aggregation)
# ---------------------------------------------------------------------

def path_entropy(
    *,
    path: HilbertPath,
    entropy_backend: FiberEntropyBackend,
    delta: float = 1e-12,
) -> Entropy:
    """
    Entropy per unit structural change, aggregated covariantly.
    """

    m = path.sigmas.shape[0]
    if m == 0:
        return 0.0

    # Compute per-anchor entropies
    H = np.array(
        [float(entropy_backend.entropy(s)) for s in path.sigmas],
        dtype=float,
    )

    # Covariant weights via arc-length
    weights = np.zeros_like(H)

    if path.ds.size == 0:
        # Single anchor: uniform weight
        weights[:] = 1.0
    else:
        # Interior points
        weights[0] = path.ds[0] / 2.0
        weights[-1] = path.ds[-1] / 2.0
        for i in range(1, m - 1):
            weights[i] = (path.ds[i - 1] + path.ds[i]) / 2.0

    total_length = float(path.ds.sum())
    return float(np.dot(weights, H) / (total_length + delta))


# ---------------------------------------------------------------------
# 6. Informational temperature
# ---------------------------------------------------------------------

def informational_temperature(
    *,
    noise: NoiseBand,
    scale: float = 1.0,
    mode: str = "mean",
) -> float:
    """
    Map noise floor to informational temperature.

        T = τ · ε̄
    """

    if np.isscalar(noise):
        eps = float(noise)
    else:
        noise_arr = np.asarray(noise, dtype=float)
        if mode == "mean":
            eps = float(noise_arr.mean())
        elif mode == "max":
            eps = float(noise_arr.max())
        else:
            raise ValueError(f"Unknown mode: {mode}")

    return float(scale * eps)


# ---------------------------------------------------------------------
# 7. Informational free energy
# ---------------------------------------------------------------------

def informational_free_energy(
    *,
    mass: Mass,
    entropy: Entropy,
    temperature: float,
    energy_scale: float = 1.0,
) -> float:
    """
    Informational free energy:

        F = U − T H
    """
    U = informational_energy(
        mass=mass,
        scale=energy_scale,
    )
    return float(U - temperature * entropy)


# ---------------------------------------------------------------------
# 8. Reporting
# ---------------------------------------------------------------------

def info_mass_report(
    *,
    path: HilbertPath,
    noise: NoiseBand,
    alpha: float,
    mass: Mass,
    energy: Energy | None = None,
    entropy: Entropy | None = None,
    temperature: float | None = None,
    free_energy: float | None = None,
    version: str = "v1",
) -> dict[str, Any]:
    """
    Deterministic, serializable diagnostic artifact.
    """

    report: dict[str, Any] = {
        "version": version,
        "alpha": alpha,
        "arc_length": float(path.ds.sum()),
        "informational_mass": float(mass),
    }

    if energy is not None:
        report["informational_energy"] = float(energy)

    if entropy is not None:
        report["entropy"] = float(entropy)

    if temperature is not None:
        report["temperature"] = float(temperature)

    if free_energy is not None:
        report["free_energy"] = float(free_energy)

    return report
