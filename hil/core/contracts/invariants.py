# hil/contracts/invariants.py
"""
hil.contracts.invariants

Small invariant helpers for contract validation.

Keep this strict and tiny: contracts should fail loudly when malformed,
but should not attempt repair or inference.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.contracts invariant] {message}")


def require_str(x: Any, name: str) -> str:
    invariant(isinstance(x, str) and x != "", f"{name} must be a non-empty string")
    return x


def require_int(x: Any, name: str) -> int:
    invariant(isinstance(x, int), f"{name} must be an int")
    return x


def require_float(x: Any, name: str) -> float:
    invariant(isinstance(x, (int, float)), f"{name} must be a float")
    return float(x)


def require_bool(x: Any, name: str) -> bool:
    invariant(isinstance(x, bool), f"{name} must be a bool")
    return x


def require_dict(x: Any, name: str) -> Mapping[str, Any]:
    invariant(isinstance(x, Mapping), f"{name} must be a mapping/dict")
    return x


def require_list(x: Any, name: str) -> Sequence[Any]:
    invariant(isinstance(x, Sequence) and not isinstance(x, (str, bytes)), f"{name} must be a list/sequence")
    return x
