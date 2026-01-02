# hil/orchestrator/runner.py
"""
hil.orchestrator.runner

Plan execution engine for the HIL orchestrator.

This module:
- executes declarative plans step-by-step
- invokes sanctioned build entrypoints
- records procedural execution metadata

This module does NOT:
- interpret epistemic results
- branch on metric values
- apply thresholds or criteria
- modify plans at runtime
- persist hidden state between runs
"""

from __future__ import annotations

import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any

from hil.orchestrator.plans import Plan, PlanStep


# ---------------------------------------------------------------------------
# Invariants
# ---------------------------------------------------------------------------

def _runner_invariant(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(f"[hil.orchestrator.runner invariant] {message}")


# ---------------------------------------------------------------------------
# Execution record types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class StepExecutionRecord:
    """
    Record of a single plan step execution.
    """
    step_index: int
    build: str
    input: str
    perturbation: str | None
    start_time_utc: str
    end_time_utc: str
    success: bool
    run_directory: str | None
    error: str | None = None


@dataclass(frozen=True)
class PlanExecutionRecord:
    """
    Record of an entire plan execution.
    """
    plan_name: str
    started_utc: str
    finished_utc: str
    steps: List[StepExecutionRecord]
    success: bool
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_timestamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _invoke_build(build: str) -> None:
    """
    Invoke a build entrypoint.

    Currently supports:
    - hil_build

    Extension must be explicit and human-approved.
    """
    if build != "hil_build":
        raise RuntimeError(f"Unsupported build entrypoint: {build}")

    # Use the current interpreter to respect active environment (e.g. Conda)
    cmd = [sys.executable, "-m", "hil.build.hil_build"]
    subprocess.check_call(cmd)


def _latest_run_dir(artifacts_root: Path) -> Path:
    runs = sorted(
        (p for p in artifacts_root.iterdir() if p.is_dir()),
        key=lambda p: p.name,
    )
    _runner_invariant(len(runs) > 0, "no run directories found after build")
    return runs[-1]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_plan(
    plan: Plan,
    *,
    repo_root: Path | None = None,
) -> PlanExecutionRecord:
    """
    Execute a declarative orchestration plan.

    This function:
    - executes each step in order
    - records execution metadata
    - returns a procedural record

    It does NOT:
    - interpret results
    - compute diffs
    - decide success beyond execution completion
    """
    repo_root = repo_root or Path.cwd()
    artifacts_root = repo_root / "artifacts" / "runs"

    _runner_invariant(
        artifacts_root.exists(),
        "artifacts/runs directory does not exist",
    )

    started = _utc_timestamp()
    step_records: List[StepExecutionRecord] = []

    for idx, step in enumerate(plan.steps):
        step_start = _utc_timestamp()
        run_dir: str | None = None
        success = False
        error: str | None = None

        try:
            _invoke_build(step.build)
            latest = _latest_run_dir(artifacts_root)
            run_dir = str(latest)
            success = True
        except Exception as e:
            error = str(e)
            success = False

        step_end = _utc_timestamp()

        step_records.append(
            StepExecutionRecord(
                step_index=idx,
                build=step.build,
                input=step.input,
                perturbation=step.perturbation,
                start_time_utc=step_start,
                end_time_utc=step_end,
                success=success,
                run_directory=run_dir,
                error=error,
            )
        )

        if not success:
            break  # stop execution on failure

    finished = _utc_timestamp()
    overall_success = all(s.success for s in step_records)

    return PlanExecutionRecord(
        plan_name=plan.name,
        started_utc=started,
        finished_utc=finished,
        steps=step_records,
        success=overall_success,
        metadata={
            "epistemic_status": "procedural-only",
        },
    )


__all__ = [
    "run_plan",
    "PlanExecutionRecord",
    "StepExecutionRecord",
]
