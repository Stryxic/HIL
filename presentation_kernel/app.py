from __future__ import annotations

from fastapi import FastAPI, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime
import uuid

app = FastAPI(
    title="HIL Presentation Kernel",
    version="1.0.0",
    description="Human-gated presentation boundary for HIL diagnostics"
)

# ---------------------------------------------------------------------
# In-memory state (reference only; replace with persistence if needed)
# ---------------------------------------------------------------------

OBSERVED_STATE: Dict[str, Any] = {
    "state": "observed",
    "timestamp": datetime.utcnow().isoformat(),
    "versions": {
        "core_version": "1.0.0",
        "extensions": {
            "thermo": "1.0.0"
        }
    },
    "diagnostics": {
        "hilbert_paths": [],
        "timebase_report": {},
        "info_mass_preview": {}
    }
}

COMMITTED_STATE: Optional[Dict[str, Any]] = None

UI_PREFERENCES: Dict[str, Any] = {}

ARTIFACT_STORE: Dict[str, Dict[str, Any]] = {}

# ---------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------

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


# ---------------------------------------------------------------------
# State Endpoints
# ---------------------------------------------------------------------

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
            "uncommitted": True
        }
    }


# ---------------------------------------------------------------------
# Human-gated consolidation
# ---------------------------------------------------------------------

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
        "diagnostics": OBSERVED_STATE["diagnostics"]
    }

    ARTIFACT_STORE[commit_id] = {
        "report.json": COMMITTED_STATE
    }

    return RefreshResponse(
        commit_id=commit_id,
        committed_at=committed_at,
        artifact_urls={
            "json": f"/api/presentation/v1/downloads/{commit_id}/report.json"
        }
    )


# ---------------------------------------------------------------------
# Deterministic rendering spec
# ---------------------------------------------------------------------

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
            "units": "instrument"
        }
    }


# ---------------------------------------------------------------------
# UI preferences (non-instrumental)
# ---------------------------------------------------------------------

@app.post("/api/presentation/v1/ui/preferences", status_code=204)
def set_ui_preferences(prefs: Dict[str, Any]):
    UI_PREFERENCES.update(prefs)
    return


# ---------------------------------------------------------------------
# Uploads (inert until refresh)
# ---------------------------------------------------------------------

@app.post("/api/presentation/v1/upload", status_code=204)
def upload_file(file: UploadFile = File(...)):
    # Accept file; do nothing instrumentally
    return


# ---------------------------------------------------------------------
# Downloads
# ---------------------------------------------------------------------

@app.get("/api/presentation/v1/downloads/{commit_id}/{artifact}")
def download_artifact(commit_id: str, artifact: str):
    if commit_id not in ARTIFACT_STORE:
        raise HTTPException(status_code=404, detail="Unknown commit")

    artifacts = ARTIFACT_STORE[commit_id]
    if artifact not in artifacts:
        raise HTTPException(status_code=404, detail="Artifact not found")

    return artifacts[artifact]


# ---------------------------------------------------------------------
# LLM interpretation (explicitly non-instrumental)
# ---------------------------------------------------------------------

@app.post(
    "/api/presentation/v1/interpret",
    response_model=InterpretResponse
)
def interpret(req: InterpretRequest):
    return InterpretResponse(
        text=(
            "This is a non-instrumental interpretation. "
            "No measurements were performed. "
            "Artifact referenced: "
            f"{req.artifact}"
        )
    )
