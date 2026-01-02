# hil/contracts/assumptions.py
"""
hil.contracts.assumptions

Explicit assumptions about artifact contracts.

This file is documentation-as-code: it should remain short and boring.
It exists to reduce misinterpretation and drift when artifacts evolve.

These are NOT epistemic claims. They are format and scope assumptions.
"""

from __future__ import annotations

ASSUMPTIONS: dict[str, str] = {
    "diagnostic_only": (
        "Artifacts contain numeric diagnostics and provenance only. "
        "They do not encode regimes, classifications, thresholds, or recommendations."
    ),
    "no_hidden_state": (
        "Artifacts are complete for inspection. "
        "No additional implicit state is required to interpret them structurally."
    ),
    "deterministic_serialization": (
        "Serialization must be deterministic given the same in-memory data. "
        "Writers should sort keys and avoid non-deterministic ordering."
    ),
    "no_raw_private_corpus": (
        "Artifacts should not contain full raw corpus text by default. "
        "Prefer references (paths, hashes, counts) over content."
    ),
    "versioned_contracts": (
        "Contracts should include a version marker. "
        "Breaking changes must bump the contract version."
    ),
}
