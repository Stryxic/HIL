# hil/contracts/causal_invariants.py
"""
hil.contracts.causal_invariants

Formal causal invariants for HIL.

Purpose
-------
These invariants enforce a time-respecting, diagnostic-only causal model:

- Hilbert Processes are acyclic (monotone time / no back edges).
- Hilbert States are reproducible and provenance-complete.
- Core computation is pure: no IO, no network, no hidden randomness.
- Diagnostics are effects (computed from state content), never causes.
- Controlled noise (when used) must be explicit and parameterized.

Design constraints
------------------
- This module is intended for use by CI, tests, and build/process tooling.
- It must not import `hil.core` to avoid boundary leakage.
- It may read artifact directories (this is NOT core).
- It must remain small and auditable.

Status
------
Extension/synthesis (b): downstream enforcement scaffolding, not thesis claims.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Set, Tuple, Union
import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Errors and helpers
# ---------------------------------------------------------------------------

class CausalInvariantError(AssertionError):
    """Raised when a causal invariant is violated."""


def _inv(condition: bool, message: str) -> None:
    if not condition:
        raise CausalInvariantError(f"[hil.causal_invariant] {message}")


def _read_json(path: Path) -> Dict[str, Any]:
    _inv(path.exists(), f"Missing required file: {path.as_posix()}")
    _inv(path.is_file(), f"Expected file, got: {path.as_posix()}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        raise CausalInvariantError(f"[hil.causal_invariant] Failed to parse JSON: {path.as_posix()} :: {e}") from e


def _is_sha256_hex(s: str) -> bool:
    return bool(re.fullmatch(r"[a-fA-F0-9]{64}", s or ""))


# ---------------------------------------------------------------------------
# Artifact schema expectations (lightweight)
# ---------------------------------------------------------------------------

REQUIRED_STATE_ARTIFACTS: Tuple[str, ...] = (
    "INPUT_MANIFEST.json",
    "CONFIG_SNAPSHOT.json",
    "FIELD_SUMMARY.json",
    "GRAPH_SUMMARY.json",
    "METRICS.json",
    "RUN_METADATA.json",
)

# Optional but recommended for stronger guarantees
RECOMMENDED_STATE_ARTIFACTS: Tuple[str, ...] = (
    "ARTIFACT_INDEX.json",
    "DELTA.json",
    "PROCESS_STATE.json",
)

FORBIDDEN_KEYS_IN_DIAGNOSTICS: Tuple[str, ...] = (
    "recommendation",
    "action",
    "label",
    "regime",
    "decision",
    "classify",
    "classification",
)


# ---------------------------------------------------------------------------
# Core purity checks (import scanning)
# ---------------------------------------------------------------------------

FORBIDDEN_IMPORT_SUBSTRINGS_IN_CORE: Tuple[str, ...] = (
    "requests",
    "httpx",
    "urllib",
    "socket",
    "ftplib",
    "paramiko",
    "boto",
    "google.cloud",
    "azure",
    "sqlite3",
    "psycopg",
    "pymongo",
    "redis",
)

FORBIDDEN_IO_CALL_SUBSTRINGS_IN_CORE: Tuple[str, ...] = (
    ".write_text(",
    ".write_bytes(",
    "open(",
    "Path(",
    ".mkdir(",
    ".unlink(",
    ".rmdir(",
    "shutil.",
    "subprocess.",
    "os.system",
)


@dataclass(frozen=True)
class CorePurityScanResult:
    scanned_files: int
    violations: Tuple[str, ...]


def scan_core_purity(core_root: Path) -> CorePurityScanResult:
    """
    Static, best-effort scan to help prevent IO/network in hil/core.

    This is not a security boundary; it's a CI guardrail.
    """
    _inv(core_root.exists(), f"core_root does not exist: {core_root.as_posix()}")
    _inv(core_root.is_dir(), f"core_root must be a directory: {core_root.as_posix()}")

    violations: List[str] = []
    scanned = 0

    for py in core_root.rglob("*.py"):
        scanned += 1
        try:
            txt = py.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            violations.append(f"{py.as_posix()}: unreadable ({e})")
            continue

        lower = txt.lower()

        for token in FORBIDDEN_IMPORT_SUBSTRINGS_IN_CORE:
            if token.lower() in lower:
                violations.append(f"{py.as_posix()}: forbidden import substring '{token}'")

        for token in FORBIDDEN_IO_CALL_SUBSTRINGS_IN_CORE:
            if token in txt:
                # Allow *reading* operations in core only if explicitly exempted (rare).
                violations.append(f"{py.as_posix()}: possible IO/subprocess usage '{token}'")

    return CorePurityScanResult(scanned_files=scanned, violations=tuple(violations))


def assert_core_pure(core_root: Path) -> None:
    """
    Enforce C5/C10 (no hidden IO/network in core) via a static scan.

    Intended use: CI or test.
    """
    result = scan_core_purity(core_root)
    _inv(result.scanned_files > 0, f"No .py files found under core_root: {core_root.as_posix()}")
    _inv(len(result.violations) == 0, "Core purity scan failed:\n- " + "\n- ".join(result.violations))


# ---------------------------------------------------------------------------
# Process DAG invariants (acyclicity)
# ---------------------------------------------------------------------------

def assert_acyclic(edges: Iterable[Tuple[str, str]]) -> None:
    """
    Assert a directed graph is acyclic.

    edges: iterable of (parent, child) pairs
    """
    parents: Dict[str, Set[str]] = {}
    children: Dict[str, Set[str]] = {}

    nodes: Set[str] = set()
    for a, b in edges:
        nodes.add(a)
        nodes.add(b)
        children.setdefault(a, set()).add(b)
        parents.setdefault(b, set()).add(a)

    # Kahn's algorithm
    incoming = {n: len(parents.get(n, set())) for n in nodes}
    queue = [n for n in nodes if incoming[n] == 0]

    visited = 0
    while queue:
        n = queue.pop()
        visited += 1
        for c in children.get(n, set()):
            incoming[c] -= 1
            if incoming[c] == 0:
                queue.append(c)

    _inv(visited == len(nodes), "Process graph contains a cycle (violates monotone causality)")


def edges_from_state_chain(state_ids: Sequence[str], predecessor: Dict[str, Optional[str]]) -> List[Tuple[str, str]]:
    """
    Build edges (prev -> curr) from a predecessor map.

    predecessor[curr] = prev or None
    """
    edges: List[Tuple[str, str]] = []
    for sid in state_ids:
        prev = predecessor.get(sid)
        if prev is not None:
            edges.append((prev, sid))
    return edges


# ---------------------------------------------------------------------------
# Provenance and artifact invariants
# ---------------------------------------------------------------------------

def assert_state_artifacts_present(state_dir: Path) -> None:
    _inv(state_dir.exists() and state_dir.is_dir(), f"state_dir must exist: {state_dir.as_posix()}")
    for name in REQUIRED_STATE_ARTIFACTS:
        _inv((state_dir / name).exists(), f"Missing required artifact: {name} in {state_dir.as_posix()}")


def assert_metrics_diagnostic_only(metrics: Dict[str, Any]) -> None:
    """
    Enforce C9: metrics are numeric (or null) and contain no prescriptive fields.
    """
    _inv(isinstance(metrics, dict), "METRICS must be a JSON object")
    for k, v in metrics.items():
        _inv(isinstance(k, str), "METRICS keys must be strings")
        lk = k.lower()
        for bad in FORBIDDEN_KEYS_IN_DIAGNOSTICS:
            _inv(bad not in lk, f"METRICS contains forbidden/prescriptive key '{k}' (matched '{bad}')")
        _inv(v is None or isinstance(v, (int, float)), f"METRICS['{k}'] must be numeric or null")


def assert_provenance_complete(state_dir: Path) -> None:
    """
    Enforce C4/C6: provenance files exist and contain minimal required fields.
    """
    assert_state_artifacts_present(state_dir)

    inp = _read_json(state_dir / "INPUT_MANIFEST.json")
    cfg = _read_json(state_dir / "CONFIG_SNAPSHOT.json")
    meta = _read_json(state_dir / "RUN_METADATA.json")
    metrics = _read_json(state_dir / "METRICS.json")

    # INPUT_MANIFEST
    _inv("num_documents" in inp, "INPUT_MANIFEST missing 'num_documents'")
    _inv(int(inp["num_documents"]) >= 1, "INPUT_MANIFEST 'num_documents' must be >= 1")
    _inv("corpus_hash" in inp, "INPUT_MANIFEST missing 'corpus_hash'")
    _inv(isinstance(inp["corpus_hash"], str) and len(inp["corpus_hash"]) > 0, "INPUT_MANIFEST 'corpus_hash' must be non-empty")

    # CONFIG_SNAPSHOT: must be JSON object (structure is project-specific)
    _inv(isinstance(cfg, dict), "CONFIG_SNAPSHOT must be a JSON object")

    # RUN_METADATA: should include a fingerprint or allow later addition
    _inv(isinstance(meta, dict), "RUN_METADATA must be a JSON object")
    if "state_fingerprint" in meta:
        _inv(isinstance(meta["state_fingerprint"], str), "RUN_METADATA.state_fingerprint must be a string")
        _inv(_is_sha256_hex(meta["state_fingerprint"]), "RUN_METADATA.state_fingerprint must be sha256 hex")

    # METRICS: diagnostic-only
    assert_metrics_diagnostic_only(metrics)


def compute_state_fingerprint(
    *,
    input_manifest: Dict[str, Any],
    config_snapshot: Dict[str, Any],
    code_identity: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Compute a content-linked fingerprint for a state.

    Deterministic JSON canonicalization (sorted keys) + sha256.
    """
    import hashlib  # local import to keep module import-light

    payload = {
        "input_manifest": input_manifest,
        "config_snapshot": config_snapshot,
        "code_identity": code_identity or {},
    }
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def assert_state_fingerprint_matches(state_dir: Path) -> None:
    """
    Enforce C6 if state_fingerprint is present:
    - it must match the computed fingerprint from manifest/config/code_id.
    """
    assert_state_artifacts_present(state_dir)
    inp = _read_json(state_dir / "INPUT_MANIFEST.json")
    cfg = _read_json(state_dir / "CONFIG_SNAPSHOT.json")
    meta = _read_json(state_dir / "RUN_METADATA.json")

    if "state_fingerprint" not in meta:
        # Not required yet; allow progressive adoption.
        return

    code_id = meta.get("code_identity") if isinstance(meta.get("code_identity"), dict) else {}
    expected = compute_state_fingerprint(input_manifest=inp, config_snapshot=cfg, code_identity=code_id)

    _inv(meta["state_fingerprint"] == expected, "RUN_METADATA.state_fingerprint does not match computed fingerprint")


# ---------------------------------------------------------------------------
# Controlled noise invariants
# ---------------------------------------------------------------------------

def assert_controlled_noise_declared(config_snapshot: Dict[str, Any]) -> None:
    """
    Enforce C7: if noise is used, it must be explicit and parameterized.

    Convention (recommended):
      config_snapshot["noise"] = {
          "type": "...",
          "params": {...},
          "seed": 123
      }

    If "noise" is absent, we assume no perturbation.
    """
    if "noise" not in config_snapshot:
        return

    noise = config_snapshot["noise"]
    _inv(isinstance(noise, dict), "CONFIG_SNAPSHOT.noise must be an object if present")
    _inv("type" in noise and isinstance(noise["type"], str) and noise["type"], "noise.type must be a non-empty string")
    _inv("params" in noise and isinstance(noise["params"], dict), "noise.params must be an object")
    _inv("seed" in noise and isinstance(noise["seed"], int), "noise.seed must be an int")


# ---------------------------------------------------------------------------
# High-level convenience checks for CI
# ---------------------------------------------------------------------------

def assert_state_dir_valid(state_dir: Path) -> None:
    """
    One-stop validation for a state directory:
    - required artifacts exist
    - provenance minimal fields
    - diagnostic-only metrics
    - (optional) fingerprint consistency
    """
    assert_provenance_complete(state_dir)

    cfg = _read_json(state_dir / "CONFIG_SNAPSHOT.json")
    assert_controlled_noise_declared(cfg)

    assert_state_fingerprint_matches(state_dir)


def assert_run_dir_tree(run_dir: Path) -> None:
    """
    Validate a run directory tree under artifacts/runs/<run_id>/.
    This is intentionally light: it checks the directory exists and looks like a state dir.
    """
    _inv(run_dir.exists() and run_dir.is_dir(), f"run_dir must exist: {run_dir.as_posix()}")
    assert_state_dir_valid(run_dir)


__all__ = [
    "CausalInvariantError",
    "CorePurityScanResult",
    "REQUIRED_STATE_ARTIFACTS",
    "RECOMMENDED_STATE_ARTIFACTS",
    "FORBIDDEN_KEYS_IN_DIAGNOSTICS",
    "scan_core_purity",
    "assert_core_pure",
    "assert_acyclic",
    "edges_from_state_chain",
    "assert_state_artifacts_present",
    "assert_metrics_diagnostic_only",
    "assert_provenance_complete",
    "compute_state_fingerprint",
    "assert_state_fingerprint_matches",
    "assert_controlled_noise_declared",
    "assert_state_dir_valid",
    "assert_run_dir_tree",
]
