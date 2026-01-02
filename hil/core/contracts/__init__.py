# hil/contracts/__init__.py
"""
hil.contracts

JSON-safe artifact contracts used by build/orchestrator layers.

These are NOT epistemic authorities.
They are exchange formats for:
- build artifacts
- run provenance
- numeric diagnostics
- diffs

Invariants:
- Diagnostic, not prescriptive
- Deterministic serialization
- No IO in contract code (serialization only)
"""
