# hil/contracts/orchestrator.py
"""
hil.contracts.orchestrator

Contracts for orchestration records and diffs.

These represent procedural provenance, not epistemic authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from hil.contracts.invariants import require_dict, require_list, require_str, require_bool

CONTRACT_VERSION = "v1"


@dataclass(frozen=True)
class StepExecutionRecord:
    step_index: int
    build: str
    input: str
    perturbation: Optional[str]
    start_time_utc: str
    end_time_utc: str
    success: bool
    run_directory: Optional[str]
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_index": int(self.step_index),
            "build": self.build,
            "input": self.input,
            "perturbation": self.perturbation,
            "start_time_utc": self.start_time_utc,
            "end_time_utc": self.end_time_utc,
            "success": bool(self.success),
            "run_directory": self.run_directory,
            "error": self.error,
        }

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "StepExecutionRecord":
        o = require_dict(obj, "StepExecutionRecord")
        return StepExecutionRecord(
            step_index=int(o.get("step_index")),
            build=require_str(o.get("build"), "build"),
            input=require_str(o.get("input"), "input"),
            perturbation=o.get("perturbation"),
            start_time_utc=require_str(o.get("start_time_utc"), "start_time_utc"),
            end_time_utc=require_str(o.get("end_time_utc"), "end_time_utc"),
            success=require_bool(o.get("success"), "success"),
            run_directory=o.get("run_directory"),
            error=o.get("error"),
        )


@dataclass(frozen=True)
class PlanExecutionRecord:
    contract_version: str
    plan_name: str
    started_utc: str
    finished_utc: str
    success: bool
    steps: List[StepExecutionRecord]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "plan_name": self.plan_name,
            "started_utc": self.started_utc,
            "finished_utc": self.finished_utc,
            "success": bool(self.success),
            "steps": [s.to_dict() for s in self.steps],
            "metadata": dict(self.metadata),
        }

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "PlanExecutionRecord":
        o = require_dict(obj, "PlanExecutionRecord")
        steps_raw = require_list(o.get("steps", []), "steps")
        steps = [StepExecutionRecord.from_dict(require_dict(x, "StepExecutionRecord")) for x in steps_raw]
        return PlanExecutionRecord(
            contract_version=require_str(o.get("contract_version"), "contract_version"),
            plan_name=require_str(o.get("plan_name"), "plan_name"),
            started_utc=require_str(o.get("started_utc"), "started_utc"),
            finished_utc=require_str(o.get("finished_utc"), "finished_utc"),
            success=require_bool(o.get("success"), "success"),
            steps=steps,
            metadata=dict(o.get("metadata", {})),
        )


@dataclass(frozen=True)
class RunDiff:
    contract_version: str
    run_a: str
    run_b: str
    metrics: Dict[str, Any]
    field: Dict[str, Any]
    graph: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "contract_version": self.contract_version,
            "run_a": self.run_a,
            "run_b": self.run_b,
            "metrics": dict(self.metrics),
            "field": dict(self.field),
            "graph": dict(self.graph),
        }

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "RunDiff":
        o = require_dict(obj, "RunDiff")
        return RunDiff(
            contract_version=require_str(o.get("contract_version"), "contract_version"),
            run_a=require_str(o.get("run_a"), "run_a"),
            run_b=require_str(o.get("run_b"), "run_b"),
            metrics=dict(o.get("metrics", {})),
            field=dict(o.get("field", {})),
            graph=dict(o.get("graph", {})),
        )


__all__ = [
    "CONTRACT_VERSION",
    "StepExecutionRecord",
    "PlanExecutionRecord",
    "RunDiff",
]
