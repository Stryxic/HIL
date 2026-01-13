from __future__ import annotations

import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone


# =====================================================================
# Configuration
# =====================================================================

# Resolve repo root deterministically (script lives in scripts/)
SCRIPT_PATH = Path(__file__).resolve()
REPO_ROOT = SCRIPT_PATH.parent.parent

OUT = REPO_ROOT / "internal_corpus_manifest.json"
HASH_ALGO = "sha256"

# Explicit exclusions (instrument policy)
EXCLUDE_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".venv",
    "node_modules",
}

EXCLUDE_FILES = {
    "internal_corpus_manifest.json",  # prevent self-hashing loop
}


# =====================================================================
# Hash utility
# =====================================================================

def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# =====================================================================
# Manifest generation
# =====================================================================

def should_exclude(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS:
            return True
    if path.name in EXCLUDE_FILES:
        return True
    return False


def main() -> None:
    files: list[dict[str, object]] = []

    for path in sorted(REPO_ROOT.rglob("*")):
        if not path.is_file():
            continue
        if should_exclude(path):
            continue

        rel = path.relative_to(REPO_ROOT).as_posix()
        size = path.stat().st_size
        digest = sha256_file(path)

        files.append(
            {
                "path": rel,
                "size_bytes": size,
                "sha256": digest,
            }
        )

    manifest = {
        "corpus_name": "HIL Core v1.0 Internal Calibration Corpus",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "root": ".",
        "hash_algorithm": HASH_ALGO,
        "file_count": len(files),
        "files": files,
    }

    OUT.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {OUT} ({len(files)} files)")


if __name__ == "__main__":
    main()
