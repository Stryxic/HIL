# hil/contracts/artifacts.py
"""
hil.contracts.artifacts

Contracts for build artifacts emitted under artifacts/runs/<run_id>/.

These dataclasses define:
- minimal schema
- deterministic JSON-safe dict conversion
- strict validation on load

No IO is performed here (read/write belongs to build/orchestrator code).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from hil.contracts.invariants import (
    invariant,
    require_bool,
    require_dict,
    require_float,
    require_int,
    require_list,
    require_str,
)

# ---------------------------------------------------------------------
# Common
# ---------------------------------------------------------------------

CONTRACT_VERSION = "v1"


def _sorted_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    # Deterministic key ordering for JSON writers that preserve insertion order.
    return {k: d[k] for k in sorted(d.keys())}


# ---------------------------------------------------------------------
# Core artifact contracts
# ---------------------------------------------------------------------

@dataclass(frozen=True)
class RunMetadata:
    contract_version: str
    run_id: str
    created_utc: str
    tool_version: str
    python: str
    platform: str
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        d = {
            "contract_version": self.contract_version,
            "run_id": self.run_id,
            "created_utc": self.created_utc,
            "tool_version": self.tool_version,
            "python": self.python,
            "platform": self.platform,
            "notes": self.notes,
        }
        return _sorted_dict(d)

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "RunMetadata":
        o = require_dict(obj, "RunMetadata")
        return RunMetadata(
            contract_version=require_str(o.get("contract_version"), "contract_version"),
            run_id=require_str(o.get("run_id"), "run_id"),
            created_utc=require_str(o.get("created_utc"), "created_utc"),
            tool_version=require_str(o.get("tool_version"), "tool_version"),
            python=require_str(o.get("python"), "python"),
            platform=require_str(o.get("platform"), "platform"),
            notes=o.get("notes") if o.get("notes") is None else require_str(o.get("notes"), "notes"),
        )


@dataclass(frozen=True)
class InputItem:
    path: str
    kind: str
    sha256: Optional[str] = None
    bytes: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return _sorted_dict(
            {
                "path": self.path,
                "kind": self.kind,
                "sha256": self.sha256,
                "bytes": self.bytes,
            }
        )

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "InputItem":
        o = require_dict(obj, "InputItem")
        return InputItem(
            path=require_str(o.get("path"), "path"),
            kind=require_str(o.get("kind"), "kind"),
            sha256=o.get("sha256") if o.get("sha256") is None else require_str(o.get("sha256"), "sha256"),
            bytes=o.get("bytes") if o.get("bytes") is None else require_int(o.get("bytes"), "bytes"),
        )


@dataclass(frozen=True)
class InputManifest:
    contract_version: str
    corpus_name: str
    items: List[InputItem] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _sorted_dict(
            {
                "contract_version": self.contract_version,
                "corpus_name": self.corpus_name,
                "items": [i.to_dict() for i in self.items],
            }
        )

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "InputManifest":
        o = require_dict(obj, "InputManifest")
        items_raw = require_list(o.get("items", []), "items")
        items = [InputItem.from_dict(require_dict(x, "InputItem")) for x in items_raw]
        return InputManifest(
            contract_version=require_str(o.get("contract_version"), "contract_version"),
            corpus_name=require_str(o.get("corpus_name"), "corpus_name"),
            items=items,
        )


@dataclass(frozen=True)
class ConfigSnapshot:
    contract_version: str
    embedding: Dict[str, Any]
    structure: Dict[str, Any]
    metrics: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return _sorted_dict(
            {
                "contract_version": self.contract_version,
                "embedding": dict(self.embedding),
                "structure": dict(self.structure),
                "metrics": dict(self.metrics),
            }
        )

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "ConfigSnapshot":
        o = require_dict(obj, "ConfigSnapshot")
        return ConfigSnapshot(
            contract_version=require_str(o.get("contract_version"), "contract_version"),
            embedding=dict(require_dict(o.get("embedding", {}), "embedding")),
            structure=dict(require_dict(o.get("structure", {}), "structure")),
            metrics=dict(require_dict(o.get("metrics", {}), "metrics")),
        )


@dataclass(frozen=True)
class FieldSummary:
    contract_version: str
    num_items: int
    dim: int
    centroid_norm: float

    def to_dict(self) -> Dict[str, Any]:
        return _sorted_dict(
            {
                "contract_version": self.contract_version,
                "num_items": int(self.num_items),
                "dim": int(self.dim),
                "centroid_norm": float(self.centroid_norm),
            }
        )

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "FieldSummary":
        o = require_dict(obj, "FieldSummary")
        return FieldSummary(
            contract_version=require_str(o.get("contract_version"), "contract_version"),
            num_items=require_int(o.get("num_items"), "num_items"),
            dim=require_int(o.get("dim"), "dim"),
            centroid_norm=require_float(o.get("centroid_norm"), "centroid_norm"),
        )


@dataclass(frozen=True)
class GraphSummary:
    contract_version: str
    num_nodes: int
    num_edges: int
    total_weight: float

    def to_dict(self) -> Dict[str, Any]:
        return _sorted_dict(
            {
                "contract_version": self.contract_version,
                "num_nodes": int(self.num_nodes),
                "num_edges": int(self.num_edges),
                "total_weight": float(self.total_weight),
            }
        )

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "GraphSummary":
        o = require_dict(obj, "GraphSummary")
        return GraphSummary(
            contract_version=require_str(o.get("contract_version"), "contract_version"),
            num_nodes=require_int(o.get("num_nodes"), "num_nodes"),
            num_edges=require_int(o.get("num_edges"), "num_edges"),
            total_weight=require_float(o.get("total_weight"), "total_weight"),
        )


@dataclass(frozen=True)
class Metrics:
    contract_version: str
    entropy: float
    coherence: float
    stability: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return _sorted_dict(
            {
                "contract_version": self.contract_version,
                "entropy": float(self.entropy),
                "coherence": float(self.coherence),
                "stability": self.stability if self.stability is None else float(self.stability),
            }
        )

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "Metrics":
        o = require_dict(obj, "Metrics")
        return Metrics(
            contract_version=require_str(o.get("contract_version"), "contract_version"),
            entropy=require_float(o.get("entropy"), "entropy"),
            coherence=require_float(o.get("coherence"), "coherence"),
            stability=o.get("stability") if o.get("stability") is None else require_float(o.get("stability"), "stability"),
        )


@dataclass(frozen=True)
class ArtifactIndex:
    contract_version: str
    run_id: str
    files: List[str]
    html: List[str] = field(default_factory=list)
    static: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return _sorted_dict(
            {
                "contract_version": self.contract_version,
                "run_id": self.run_id,
                "files": list(self.files),
                "html": list(self.html),
                "static": list(self.static),
            }
        )

    @staticmethod
    def from_dict(obj: Mapping[str, Any]) -> "ArtifactIndex":
        o = require_dict(obj, "ArtifactIndex")
        files = [require_str(x, "files[i]") for x in require_list(o.get("files", []), "files")]
        html = [require_str(x, "html[i]") for x in require_list(o.get("html", []), "html")]
        static = [require_str(x, "static[i]") for x in require_list(o.get("static", []), "static")]
        return ArtifactIndex(
            contract_version=require_str(o.get("contract_version"), "contract_version"),
            run_id=require_str(o.get("run_id"), "run_id"),
            files=files,
            html=html,
            static=static,
        )


__all__ = [
    "CONTRACT_VERSION",
    "RunMetadata",
    "InputItem",
    "InputManifest",
    "ConfigSnapshot",
    "FieldSummary",
    "GraphSummary",
    "Metrics",
    "ArtifactIndex",
]
