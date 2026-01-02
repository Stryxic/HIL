# hil/orchestrator/plans.py
"""
hil.orchestrator.plans

Declarative run plans for the HIL orchestrator.

This module defines:
- what constitutes a valid orchestration plan
- how plans are represented and validated

This module does NOT:
- execute plans
- interpret results
- branch on outcomes
- contain procedural logic

Plans are inert data structures. Execution is handled elsewhere.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _plan_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"[hil.orchestrator.plan invariant] {message}")


# ---------------------------------------------------------------------------
# Plan step
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class PlanStep:
    """
    A single step in an orchestration plan.

    A step describes ONE build invocation with explicit, declared parameters.
    It does not contain logic, conditions, or branching.
    """

    build: str
    input: str

    perturbation: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _plan_invariant(
            isinstance(self.build, str) and self.build,
            "build must be a non-empty string",
        )
        _plan_invariant(
            isinstance(self.input, str) and self.input,
            "input must be a non-empty string",
        )
        _plan_invariant(
            self.perturbation is None or isinstance(self.perturbation, str),
            "perturbation must be a string or None",
        )
        _plan_invariant(
            isinstance(self.parameters, dict),
            "parameters must be a dictionary",
        )


# ---------------------------------------------------------------------------
# Plan
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Plan:
    """
    Declarative orchestration plan.

    A plan is an ordered list of steps that a runner may execute.
    """

    name: str
    steps: List[PlanStep]

    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _plan_invariant(
            isinstance(self.name, str) and self.name,
            "plan name must be a non-empty string",
        )
        _plan_invariant(
            isinstance(self.steps, list) and len(self.steps) > 0,
            "plan must contain at least one step",
        )
        _plan_invariant(
            all(isinstance(s, PlanStep) for s in self.steps),
            "all steps must be PlanStep instances",
        )
        _plan_invariant(
            isinstance(self.metadata, dict),
            "metadata must be a dictionary",
        )


# ---------------------------------------------------------------------------
# Example plans (for reference only)
# ---------------------------------------------------------------------------

def example_self_sensitivity_plan() -> Plan:
    """
    Example plan demonstrating a minimal self-sensitivity check.

    This function exists for documentation and testing purposes only.
    It does not imply execution semantics.
    """
    return Plan(
        name="self-sensitivity-check",
        description="Run the same self-corpus build twice, once with a declared perturbation.",
        steps=[
            PlanStep(
                build="hil_build",
                input="self",
            ),
            PlanStep(
                build="hil_build",
                input="self",
                perturbation="shuffle-order",
            ),
        ],
        metadata={
            "purpose": "illustrative",
            "epistemic_status": "diagnostic-only",
        },
    )


__all__ = [
    "Plan",
    "PlanStep",
    "example_self_sensitivity_plan",
]
