from __future__ import annotations

from contextlib import asynccontextmanager
from datetime import datetime
import hashlib
import json
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Set

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.routing import APIRoute
from pydantic import BaseModel, Field


# =====================================================================
# Paths (deterministic)
# =====================================================================

BASE_DIR = Path(__file__).resolve().parent          # .../presentation_kernel
REPO_ROOT = BASE_DIR.parent                         # .../ (repo root)
STATIC_DIR = BASE_DIR / "static"

INTERNAL_MANIFEST_PATH = REPO_ROOT / "internal_corpus_manifest.json"
REPRODUCIBILITY_ROOT = REPO_ROOT / "reproducibility"

REGISTRY_JSON_PATH = REPRODUCIBILITY_ROOT / "metric_registry.json"
REGISTRY_YAML_PATH = REPRODUCIBILITY_ROOT / "metric_registry.yaml"

# Ensure HIL core is importable when running uvicorn from presentation_kernel/
# Deterministic, read-only: does not mutate repo state.
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


# =====================================================================
# Helpers (I/O + hashing)
# =====================================================================

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _read_text(path: Path, *, max_bytes: int = 5_000_000) -> str:
    # Safe deterministic read; max_bytes is a hard cap.
    data = path.read_bytes()
    if len(data) > max_bytes:
        data = data[:max_bytes]
    return data.decode("utf-8", errors="replace")


# =====================================================================
# Metric Registry (startup invariant)
# =====================================================================

class RegistryError(RuntimeError):
    pass


_ALLOWED_AUTHORITIES: Set[str] = {
    "trust-anchor",
    "invariant",
    "instrument",
    "human-gated",
    "transport",
    "interpretive",
}


def load_metric_registry() -> dict[str, Any]:
    """
    Load registry from JSON (preferred) or YAML (fallback).
    Registry is a reproducibility artifact: it MUST exist before startup.
    """
    if REGISTRY_JSON_PATH.exists():
        try:
            return json.loads(_read_text(REGISTRY_JSON_PATH))
        except Exception as e:
            raise RegistryError(f"Failed to parse metric registry JSON: {e}") from e

    if REGISTRY_YAML_PATH.exists():
        # Optional dependency; if YAML is present but PyYAML isn't installed,
        # we fail explicitly.
        try:
            import yaml  # type: ignore
        except Exception as e:
            raise RegistryError(
                "metric_registry.yaml present but PyYAML not installed. "
                "Install pyyaml or provide metric_registry.json."
            ) from e
        try:
            return yaml.safe_load(_read_text(REGISTRY_YAML_PATH))
        except Exception as e:
            raise RegistryError(f"Failed to parse metric registry YAML: {e}") from e

    raise RegistryError(
        "Metric registry missing.\n"
        "This violates the HIL reproducibility invariant:\n"
        "All exposed metrics must be declared before instrument startup.\n"
        f"Expected one of:\n - {REGISTRY_JSON_PATH}\n - {REGISTRY_YAML_PATH}"
    )


def collect_exposed_api_endpoints(app: FastAPI) -> Set[str]:
    """
    Only count machine-facing API endpoints (schema-visible, APIRoute)
    under /api/presentation/v1.
    """
    endpoints: Set[str] = set()
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        if not route.include_in_schema:
            continue
        if route.path.startswith("/api/presentation/v1/"):
            endpoints.add(route.path)
    return endpoints


def validate_metric_registry(app: FastAPI) -> None:
    registry = load_metric_registry()

    # Required top-level invariants (hardened)
    if registry.get("status") != "frozen":
        raise RegistryError("Metric registry must have status='frozen' before startup.")
    if registry.get("scope") != "HIL Core":
        raise RegistryError("Metric registry scope mismatch: expected scope='HIL Core'.")
    if "metrics" not in registry or not isinstance(registry["metrics"], list):
        raise RegistryError("Metric registry invalid: expected 'metrics' as a list.")

    metrics: list[dict[str, Any]] = registry["metrics"]

    # Build lookup tables
    registry_ids: Set[str] = set()
    registry_endpoints: Dict[str, dict[str, Any]] = {}

    for m in metrics:
        metric_id = m.get("metric_id")
        endpoint = m.get("endpoint")
        authority = m.get("authority")

        if not isinstance(metric_id, str) or not metric_id.strip():
            raise RegistryError("Invalid metric entry: missing/invalid metric_id.")
        if not isinstance(endpoint, str) or not endpoint.strip():
            raise RegistryError(f"Invalid metric entry '{metric_id}': missing/invalid endpoint.")
        if not isinstance(authority, str) or authority not in _ALLOWED_AUTHORITIES:
            raise RegistryError(
                f"Invalid metric entry '{metric_id}': authority must be one of "
                f"{sorted(_ALLOWED_AUTHORITIES)}."
            )

        if metric_id in registry_ids:
            raise RegistryError(f"Duplicate metric_id in registry: {metric_id}")
        registry_ids.add(metric_id)

        # Enforce 1:1 endpoint->metric for now
        if endpoint in registry_endpoints:
            raise RegistryError(
                f"Duplicate endpoint in registry: {endpoint} "
                f"(metric_id={metric_id}, existing_metric_id={registry_endpoints[endpoint].get('metric_id')})"
            )
        registry_endpoints[endpoint] = m

    # 1) Every exposed API endpoint must be declared
    exposed = collect_exposed_api_endpoints(app)
    for path in sorted(exposed):
        if path not in registry_endpoints:
            raise RegistryError(f"Exposed endpoint not in metric registry: {path}")

    # 2) Registry must not claim endpoints that do not exist
    for endpoint in sorted(registry_endpoints.keys()):
        if endpoint.startswith("/api/presentation/v1/") and endpoint not in exposed:
            raise RegistryError(f"Registry declares endpoint not exposed by app: {endpoint}")

    # 3) Dependency closure (dependencies refer to known metric_ids)
    for m in metrics:
        deps = m.get("dependencies", [])
        if deps is None:
            deps = []
        if not isinstance(deps, list):
            raise RegistryError(f"Metric '{m.get('metric_id')}' dependencies must be a list.")
        for dep in deps:
            if dep not in registry_ids:
                raise RegistryError(
                    f"Metric '{m.get('metric_id')}' depends on unknown metric_id '{dep}'."
                )

    # 4) Authority vs path discipline (tight + explicit)
    for endpoint, m in registry_endpoints.items():
        authority = m.get("authority")

        # Internal endpoints are trust anchors or invariants only.
        if "/internal/" in endpoint:
            if authority not in ("trust-anchor", "invariant"):
                raise RegistryError(f"{endpoint}: authority must be 'trust-anchor' or 'invariant'.")

        # Observed state must be instrument authority.
        if endpoint.endswith("/observed"):
            if authority != "instrument":
                raise RegistryError(f"{endpoint}: authority must be 'instrument'.")

        # Committed state is human-gated.
        if endpoint.endswith("/committed"):
            if authority != "human-gated":
                raise RegistryError(f"{endpoint}: authority must be 'human-gated'.")

        # Refresh is always human-gated.
        if endpoint.endswith("/refresh"):
            if authority != "human-gated":
                raise RegistryError(f"{endpoint}: authority must be 'human-gated'.")

        # Downloads are transport (not measurement).
        if endpoint.startswith("/api/presentation/v1/downloads/"):
            if authority != "transport":
                raise RegistryError(f"{endpoint}: authority must be 'transport'.")

        # Interpret is explicitly non-instrumental.
        if endpoint.endswith("/interpret"):
            if authority != "interpretive":
                raise RegistryError(f"{endpoint}: authority must be 'interpretive'.")


# =====================================================================
# Lifespan (startup invariant)
# =====================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    validate_metric_registry(app)
    yield


# =====================================================================
# Application
# =====================================================================

app = FastAPI(
    title="HIL Presentation Kernel",
    version="1.0.0",
    description="Human-gated presentation boundary for HIL diagnostics",
    lifespan=lifespan,
)

# =====================================================================
# Static landing page (human-facing)
# =====================================================================

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
def homepage():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=500, detail=f"Missing static homepage: {index_path}")
    return FileResponse(str(index_path))


# =====================================================================
# In-memory state (reference-only)
# =====================================================================

OBSERVED_STATE: Dict[str, Any] = {
    "state": "observed",
    "timestamp": datetime.utcnow().isoformat(),
    "versions": {
        "core_version": "1.0.0",
        "extensions": {"thermo": "1.0.0"},
    },
    "diagnostics": {
        "hilbert_paths": [],
        "timebase_report": {},
        "info_mass_preview": {},
    },
}

COMMITTED_STATE: Optional[Dict[str, Any]] = None
UI_PREFERENCES: Dict[str, Any] = {}
ARTIFACT_STORE: Dict[str, Dict[str, Any]] = {}


# =====================================================================
# Internal calibration (self-measurement, read-only)
# =====================================================================

def load_internal_manifest() -> dict[str, Any]:
    if not INTERNAL_MANIFEST_PATH.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Internal corpus manifest not found at {INTERNAL_MANIFEST_PATH}",
        )
    try:
        manifest = json.loads(_read_text(INTERNAL_MANIFEST_PATH))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse manifest: {e}") from e

    # Hardening: repo-root manifests must declare root="."
    if manifest.get("root", ".") != ".":
        raise HTTPException(status_code=500, detail="Manifest invalid: expected root='.' (repo root).")

    return manifest


def verify_manifest(manifest: dict[str, Any]) -> Tuple[bool, list[dict[str, Any]]]:
    files = manifest.get("files", [])
    if not isinstance(files, list):
        raise HTTPException(status_code=500, detail="Manifest invalid: 'files' must be a list")

    verified = True
    errors: list[dict[str, Any]] = []

    for entry in files:
        rel_path = entry.get("path")
        expected_hash = entry.get("sha256")

        if not rel_path or not expected_hash:
            verified = False
            errors.append({"path": rel_path or "<missing>", "error": "manifest_entry_invalid"})
            continue

        file_path = REPO_ROOT / rel_path
        if not file_path.exists():
            verified = False
            errors.append({"path": rel_path, "error": "missing"})
            continue
        if not file_path.is_file():
            verified = False
            errors.append({"path": rel_path, "error": "not_a_file"})
            continue

        actual_hash = sha256_file(file_path)
        if actual_hash != expected_hash:
            verified = False
            errors.append(
                {
                    "path": rel_path,
                    "error": "hash_mismatch",
                    "expected": expected_hash,
                    "actual": actual_hash,
                }
            )

    return verified, errors


@app.get("/api/presentation/v1/internal/calibration")
def internal_calibration():
    """
    Read-only integrity check of the frozen internal corpus manifest.
    """
    manifest = load_internal_manifest()
    verified, errors = verify_manifest(manifest)

    return {
        "corpus": manifest.get("corpus_name", "internal_corpus"),
        "generated_at": manifest.get("generated_at"),
        "hash_algorithm": manifest.get("hash_algorithm", "sha256"),
        "root": manifest.get("root", "."),
        "file_count": manifest.get("file_count", len(manifest.get("files", []))),
        "status": "verified" if verified else "invalid",
        "errors": errors,
        "diagnostics": {"note": "This endpoint performs integrity verification only."},
    }


# =====================================================================
# Internal timebase invariant (read-only)
# =====================================================================

def _read_internal_text_corpus(max_bytes: int = 200_000) -> str:
    """
    Deterministic “internal corpus” material:
    prefer documentation-like files.
    """
    candidates = [
        REPO_ROOT / "README.md",
        REPO_ROOT / "HIL_Core_Paper.tex",
        REPO_ROOT / "HIL_Core_Paper_with_Appendix.tex",
        REPO_ROOT / "CORE_INVARIANTS.md",
        REPO_ROOT / "EXTENSIONS_GUIDE.md",
        REPO_ROOT / "VERSIONING.md",
    ]
    for p in candidates:
        if p.exists() and p.is_file():
            return p.read_text(encoding="utf-8", errors="replace")[:max_bytes]

    md_files = sorted(
        [p for p in REPO_ROOT.rglob("*.md") if p.is_file()],
        key=lambda x: x.as_posix(),
    )
    if md_files:
        return md_files[0].read_text(encoding="utf-8", errors="replace")[:max_bytes]

    return ""


@app.get("/api/presentation/v1/internal/timebase")
def internal_timebase():
    """
    Certified timebase invariant computed deterministically from internal text.

    - Read-only
    - Requires calibration verified
    - Returns: Δt_min + recommended band (instrument-only)
    """
    manifest = load_internal_manifest()
    verified, errors = verify_manifest(manifest)
    if not verified:
        raise HTTPException(status_code=409, detail={"status": "invalid", "errors": errors})

    try:
        import numpy as np
        from hil.core.timebase import (
            estimate_data_floor,
            benchmark_pipeline_runtime,
            estimate_tick_floor,
            recommend_tick_band,
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to import HIL core timebase. "
                f"(sys.path includes REPO_ROOT={REPO_ROOT}) Error: {e}"
            ),
        ) from e

    text = _read_internal_text_corpus()
    if not text:
        raise HTTPException(status_code=500, detail="No internal text material available to calibrate timebase")

    class TextSlice:
        def __init__(self, size: int, text_: str):
            self.size = size
            self.text = text_

    sizes = [256, 512, 1024, 2048, 4096, 8192]
    slices = [TextSlice(size=s, text_=text[: min(len(text), s)]) for s in sizes if s <= len(text)]
    if not slices:
        slices = [TextSlice(size=len(text), text_=text)]

    def build_macrostate_with_params(slc: TextSlice, params: dict[str, Any]):
        scale = float(params.get("scale", 1.0))
        checksum = sum(ord(c) for c in slc.text) % 10_000
        return np.array([scale * float(len(slc.text)), float(checksum)], dtype=float)

    def build_macrostate(slc: TextSlice):
        checksum = sum(ord(c) for c in slc.text) % 10_000
        return np.array([float(len(slc.text)), float(checksum)], dtype=float)

    moduli_grid = [{"scale": 1.00}, {"scale": 1.01}, {"scale": 0.99}]
    tolerance = 8.0

    data_floor = estimate_data_floor(
        slices=slices,
        build_macrostate=build_macrostate_with_params,
        moduli_grid=moduli_grid,
        tolerance=tolerance,
        dispersion_norm="l2",
    )

    runtime_stats = benchmark_pipeline_runtime(
        slice=slices[data_floor.get("min_slice_index", 0) or 0],
        build_macrostate=build_macrostate,
        runs=7,
    )

    tick_floor = estimate_tick_floor(
        data_floor=data_floor,
        runtime_stats=runtime_stats,
        data_rate=None,
    )

    tick_band = recommend_tick_band(
        min_tick=float(tick_floor["min_tick"]),
        multiples=(1, 2, 5, 10),
    )

    report = {
        "version": "poc-timebase-v1",
        "generated_at": datetime.utcnow().isoformat(),
        "source": "internal_text_material",
        "data_floor": data_floor,
        "runtime": runtime_stats,
        "tick_floor": tick_floor,
        "recommended_band": tick_band,
    }

    # Mirror into observed state (latest observation)
    OBSERVED_STATE["diagnostics"]["timebase_report"] = report
    OBSERVED_STATE["timestamp"] = datetime.utcnow().isoformat()

    return report


# =====================================================================
# Models
# =====================================================================

class RefreshRequest(BaseModel):
    user_confirmation: bool = Field(..., const=True)
    label: Optional[str] = None
    notes: Optional[str] = None


class RefreshResponse(BaseModel):
    status: str = Field("committed", const=True)
    commit_id: str
    committed_at: str
    artifact_urls: Dict[str, str]


class InterpretRequest(BaseModel):
    artifact: str
    prompt: str


class InterpretResponse(BaseModel):
    mode: str = Field("interpretation", const=True)
    binding: str = Field("non-instrumental", const=True)
    text: str


# =====================================================================
# State Endpoints (machine-facing)
# =====================================================================

@app.get("/api/presentation/v1/observed")
def get_observed():
    return OBSERVED_STATE


@app.get("/api/presentation/v1/committed")
def get_committed():
    if COMMITTED_STATE is None:
        raise HTTPException(status_code=404, detail="No committed state yet")
    return COMMITTED_STATE


@app.get("/api/presentation/v1/delta")
def get_delta():
    if COMMITTED_STATE is None:
        raise HTTPException(status_code=404, detail="No committed state to diff against")
    return {
        "from_commit": COMMITTED_STATE["commit_id"],
        "to_state": "observed",
        "delta": {
            "note": "Structural delta computation is extension-defined",
            "uncommitted": True,
        },
    }


# =====================================================================
# Human-gated consolidation
# =====================================================================

@app.post("/api/presentation/v1/refresh", response_model=RefreshResponse)
def refresh(req: RefreshRequest):
    global COMMITTED_STATE

    if req.user_confirmation is not True:
        raise HTTPException(status_code=400, detail="Explicit confirmation required")

    commit_id = f"cmt-{uuid.uuid4().hex[:8]}"
    committed_at = datetime.utcnow().isoformat()

    COMMITTED_STATE = {
        "state": "committed",
        "commit_id": commit_id,
        "committed_at": committed_at,
        "versions": OBSERVED_STATE["versions"],
        "diagnostics": OBSERVED_STATE["diagnostics"],
    }

    ARTIFACT_STORE[commit_id] = {"report.json": COMMITTED_STATE}

    return RefreshResponse(
        commit_id=commit_id,
        committed_at=committed_at,
        artifact_urls={"json": f"/api/presentation/v1/downloads/{commit_id}/report.json"},
    )


# =====================================================================
# Deterministic rendering spec
# =====================================================================

@app.get("/api/presentation/v1/render/spec")
def render_spec():
    return {
        "type": "hilbert_paths",
        "coordinate_space": "R^k",
        "paths": OBSERVED_STATE["diagnostics"].get("hilbert_paths", []),
        "bands": [],
        "annotations": [],
        "render_rules": {
            "interpolation": "none",
            "smoothing": False,
            "units": "instrument",
        },
    }

@app.get("/api/presentation/v1/render/seed")
def render_seed():
    manifest = load_internal_manifest()
    verified, errors = verify_manifest(manifest)

    # Default fallbacks (must be deterministic)
    timebase = OBSERVED_STATE["diagnostics"].get("timebase_report") or {}

    # If timebase not yet computed this run, compute it deterministically
    # by calling internal_timebase() logic OR require user to hit /internal/timebase first.
    # For a PoC: if empty, provide a “safe null seed”.
    if not timebase:
        q_cal = 1.0 if verified else 0.3
        return {
            "type": "hil_seed_v1",
            "coordinate_space": "R^3",
            "origin": [0.0, 0.0, 0.0],
            "seed": {
                "core": {"radius": 0.25, "quality": q_cal},
                "rings": [{"radius": 0.75, "thickness": 0.03, "phase": 0.0, "quality": q_cal}],
                "poles": [
                    {"pos": [0.0, 0.0, 1.0], "radius": 0.06, "quality": q_cal},
                    {"pos": [0.0, 0.0, -1.0], "radius": 0.06, "quality": q_cal},
                ],
            },
            "labels": {"calibration_status": "verified" if verified else "invalid"},
            "render_rules": {"interpolation": "none", "smoothing": False, "units": "instrument"},
        }

    # ---- If timebase exists: map to geometry (you can refine later) ----
    tick_min = float(timebase.get("tick_floor", {}).get("min_tick", 1.0))
    band = timebase.get("recommended_band", {})  # keep whatever structure you already emit

    err_count = len(errors)
    q_cal = 1.0 if verified else max(0.0, 1.0 - 0.15 * min(err_count, 6))

    # Very simple bounded mapping (stable)
    r_core = 0.22 if tick_min > 1 else 0.30
    ring1 = 0.65 if tick_min > 1 else 0.55
    pole_z = 1.1 if tick_min > 1 else 0.9

    return {
        "type": "hil_seed_v1",
        "coordinate_space": "R^3",
        "origin": [0.0, 0.0, 0.0],
        "seed": {
            "core": {"radius": r_core, "quality": q_cal},
            "rings": [
                {"radius": ring1, "thickness": 0.04, "phase": 0.0, "quality": q_cal},
                {"radius": ring1 + 0.25, "thickness": 0.03, "phase": 1.2, "quality": q_cal},
            ],
            "poles": [
                {"pos": [0.0, 0.0, pole_z], "radius": 0.06, "quality": q_cal},
                {"pos": [0.0, 0.0, -pole_z], "radius": 0.06, "quality": q_cal},
            ],
        },
        "labels": {
            "calibration_status": "verified" if verified else "invalid",
            "calibration_errors": err_count,
            "tick_min": tick_min,
            "recommended_band": band,
        },
        "render_rules": {"interpolation": "none", "smoothing": False, "units": "instrument"},
    }


# =====================================================================
# UI preferences (explicitly non-instrumental)
# =====================================================================

@app.post("/api/presentation/v1/ui/preferences", status_code=204)
def set_ui_preferences(prefs: Dict[str, Any]):
    UI_PREFERENCES.update(prefs)
    return


# =====================================================================
# Uploads (inert until refresh)
# =====================================================================

@app.post("/api/presentation/v1/upload", status_code=204)
def upload_file(file: UploadFile = File(...)):
    return


# =====================================================================
# Downloads (transport)
# =====================================================================

@app.get("/api/presentation/v1/downloads/{commit_id}/{artifact}")
def download_artifact(commit_id: str, artifact: str):
    if commit_id not in ARTIFACT_STORE:
        raise HTTPException(status_code=404, detail="Unknown commit")

    artifacts = ARTIFACT_STORE[commit_id]
    if artifact not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return artifacts[artifact]


# =====================================================================
# LLM interpretation (explicitly non-instrumental)
# =====================================================================

@app.post("/api/presentation/v1/interpret", response_model=InterpretResponse)
def interpret(req: InterpretRequest):
    return InterpretResponse(
        text=(
            "This is a non-instrumental interpretation. "
            "No measurements were performed. "
            "Artifact referenced: "
            f"{req.artifact}"
        )
    )
