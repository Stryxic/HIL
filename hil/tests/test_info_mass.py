# tests/test_info_mass.py

import numpy as np
import pytest

from hil.core.path_invariant import CovariantPath
from hil.extensions.thermo.info_mass import (
    thresholded_increments,
    informational_mass,
    informational_mass_density,
    informational_energy,
    informational_temperature,
    informational_free_energy,
    path_entropy,
)


# ---------------------------------------------------------------------
# Dummy entropy backend (deterministic, non-semantic)
# ---------------------------------------------------------------------

class ConstantEntropyBackend:
    def __init__(self, value: float):
        self.value = value

    def entropy(self, sigma: np.ndarray) -> float:
        return float(self.value)


# ---------------------------------------------------------------------
# Helper: build simple covariant paths
# ---------------------------------------------------------------------

def make_path(points: list[list[float]]) -> CovariantPath:
    sigmas = np.asarray(points, dtype=float)
    if len(sigmas) <= 1:
        ds = np.empty((0,))
        s = np.zeros((len(sigmas),))
    else:
        deltas = sigmas[1:] - sigmas[:-1]
        ds = np.linalg.norm(deltas, axis=1)
        s = np.concatenate(([0.0], np.cumsum(ds)))

    return CovariantPath(
        anchors=list(range(len(sigmas))),
        sigmas=sigmas,
        ds=ds,
        s=s,
    )


# ---------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------

def test_noise_dominance_zero_mass_when_below_noise():
    """
    If all structural change is below the noise floor,
    informational mass must be zero.
    """
    path = make_path([[0.0], [0.01], [0.02]])
    noise = 0.1

    mass = informational_mass(
        path=path,
        noise=noise,
        alpha=1.0,
    )

    assert mass == 0.0


def test_mass_increases_when_noise_decreases():
    """
    Reducing the noise floor must not reduce informational mass.
    """
    path = make_path([[0.0], [1.0], [2.0]])

    mass_high_noise = informational_mass(
        path=path,
        noise=1.5,
        alpha=1.0,
    )

    mass_low_noise = informational_mass(
        path=path,
        noise=0.1,
        alpha=1.0,
    )

    assert mass_low_noise >= mass_high_noise


def test_covariance_under_resampling():
    """
    Informational mass must be invariant under monotone reparameterization
    (resampling of anchors).
    """
    dense = make_path([[0.0], [1.0], [2.0], [3.0]])
    sparse = make_path([[0.0], [2.0], [3.0]])

    noise = 0.1

    mass_dense = informational_mass(
        path=dense,
        noise=noise,
        alpha=1.0,
    )

    mass_sparse = informational_mass(
        path=sparse,
        noise=noise,
        alpha=1.0,
    )

    assert mass_dense == pytest.approx(mass_sparse, rel=1e-6)


def test_mass_density_bounds():
    """
    Informational mass density must lie in [0, 1].
    """
    path = make_path([[0.0], [1.0], [2.0]])
    noise = 0.1

    rho = informational_mass_density(
        path=path,
        noise=noise,
        alpha=1.0,
    )

    assert 0.0 <= rho <= 1.0


def test_energy_scales_linearly_with_mass():
    """
    Informational energy must scale linearly with informational mass.
    """
    path = make_path([[0.0], [1.0]])
    noise = 0.0

    mass = informational_mass(
        path=path,
        noise=noise,
        alpha=1.0,
    )

    energy = informational_energy(
        mass=mass,
        scale=2.5,
    )

    assert energy == pytest.approx(2.5 * mass)


def test_temperature_reflects_noise_level():
    """
    Informational temperature must increase with noise.
    """
    low_noise_T = informational_temperature(
        noise=0.1,
        scale=1.0,
    )

    high_noise_T = informational_temperature(
        noise=1.0,
        scale=1.0,
    )

    assert high_noise_T > low_noise_T


def test_entropy_independent_of_path_parameterization():
    """
    Path entropy depends on sigma values, not on time spacing.
    """
    dense = make_path([[0.0], [1.0], [2.0]])
    sparse = make_path([[0.0], [2.0]])

    backend = ConstantEntropyBackend(value=1.23)

    H_dense = path_entropy(
        path=dense,
        entropy_backend=backend,
    )

    H_sparse = path_entropy(
        path=sparse,
        entropy_backend=backend,
    )

    assert H_dense == pytest.approx(H_sparse, rel=1e-6)


def test_free_energy_decreases_with_entropy():
    """
    Increasing entropy at fixed mass and temperature must
    decrease informational free energy.
    """
    mass = 10.0
    temperature = 1.0

    F_low_H = informational_free_energy(
        mass=mass,
        entropy=1.0,
        temperature=temperature,
    )

    F_high_H = informational_free_energy(
        mass=mass,
        entropy=5.0,
        temperature=temperature,
    )

    assert F_low_H > F_high_H
