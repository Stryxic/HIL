# hil/contracts/field_alignment.py
"""
Field Alignment Contract (Executable Stub)

This module defines invariants that must be satisfied before
multi-field comparison, overlay, or joint visualization is permitted.

It does NOT perform alignment.
It only asserts whether alignment is valid.
"""

from __future__ import annotations

from typing import Dict
import numpy as np


def _contract_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.contract.field_alignment] {message}")


def assert_shared_basis(
    *,
    fields: Dict[str, np.ndarray],
    aligned: bool,
) -> None:
    """
    Assert that a collection of fields may be jointly compared.

    Parameters
    ----------
    fields : dict[str, np.ndarray]
        Mapping of field name to vector array.
    aligned : bool
        Explicit declaration that an alignment operator
        has been applied.

    Raises
    ------
    ValueError
        If the contract is violated.
    """
    _contract_invariant(len(fields) >= 2, "at least two fields required")

    dims = {v.shape[1] for v in fields.values()}

    if len(dims) != 1:
        _contract_invariant(
            aligned,
            "fields with differing dimensionality require explicit alignment",
        )

    _contract_invariant(
        aligned or len(dims) == 1,
        "overlay without shared basis or alignment is forbidden",
    )


__all__ = [
    "assert_shared_basis",
]
