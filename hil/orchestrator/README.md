# HIL Orchestrator

## Purpose and Scope

The HIL Orchestrator is a procedural coordination layer for the Hilbert Information Lab (HIL).

Its sole purpose is to sequence, compare, and record executions of the HIL epistemic pipeline without participating in epistemic judgment.

The orchestrator exists to manage how runs are executed and compared, not to decide what the results mean or what should happen next.

---

## What the Orchestrator Is

The orchestrator is:

- A run sequencer (executes builds in a declared order)
- A boundary manager (defines where runs start and stop)
- A diff producer (reports numeric and structural differences between runs)
- A procedural record keeper (what ran, when, and with what inputs)

It operates strictly downstream of the epistemic core.

---

## What the Orchestrator Is Not

The orchestrator is explicitly not:

- an epistemic authority
- a decision-maker
- a classifier or regime assigner
- an optimiser or tuner
- a feedback controller
- an agent
- a governance engine
- a policy system
- an adaptive or self-modifying system

It must never decide whether results are good, bad, healthy, unhealthy, stable, or unstable.

Any such interpretation belongs to humans or external institutions, not to HIL.

---

## Architectural Position

The orchestrator sits outside the epistemic core:

hil/core         -> defines epistemic quantities
hil/build        -> executes single diagnostic runs
hil/orchestrator -> sequences and compares runs

Hard separation rules:

- The orchestrator must not import from hil.core.metrics.*
- The orchestrator must not modify core parameters automatically
- The orchestrator must not bypass artifact generation
- The orchestrator must not store hidden state between runs

It interacts with the system only through:
- hil.core.api
- artifact files produced by builds

---

## Design Philosophy

The orchestrator is diagnostic, declarative, and restrained.

Key principles:

- Declarative execution  
  Runs are defined by explicit plans, not conditional logic.

- Artifact-first  
  Every run must produce inspectable artifacts.  
  No silent execution is permitted.

- Comparison without interpretation  
  The orchestrator may compute diffs, but never conclusions.

- Human-in-the-loop by default  
  Any action beyond execution and comparison must be initiated externally.

---

## Allowed Responsibilities

The orchestrator MAY:

- Execute multiple builds in a defined order
- Run the same build multiple times
- Apply explicit, declared perturbations to inputs
- Compare artifacts across runs
- Emit numeric or structural diffs
- Record procedural metadata about runs

The orchestrator MAY NOT:

- Branch execution based on metric values
- Choose thresholds or criteria
- Label regimes or states
- Trigger downstream actions
- Modify the epistemic core
- Call external models or services

---

## Example (Conceptual Only)

A valid orchestrator plan might look like:

{
  "name": "self-sensitivity-check",
  "steps": [
    { "build": "hil_build", "input": "self" },
    { "build": "hil_build", "input": "self", "perturbation": "shuffle-order" }
  ]
}

The orchestrator's role is to:
1. Execute both steps
2. Collect artifacts
3. Report differences

It does not decide whether the difference is acceptable.

---

## Relationship to CI

CI answers:

"Did the system behave identically?"

The orchestrator answers:

"How did the system behave differently?"

CI enforces identity and restraint.  
The orchestrator surfaces variation for inspection.

Neither replaces the other.

---

## Implementation Status

As of this version:

- The orchestrator is designed but not implemented
- This README serves as a binding contract, not a roadmap
- Any future implementation must conform to the constraints defined here

Absence of code is intentional.

---

## Extension and Federation

If orchestration is extended in the future:

- It must remain optional
- It must remain local or federated (no central authority)
- It must not accumulate epistemic power
- It must preserve inspectability and exit

Federation, if any, applies to execution coordination, not epistemic control.

---

## Final Statement

The HIL Orchestrator exists to make execution legible, not to make decisions.

If you find yourself wanting the orchestrator to decide, judge, optimise, enforce, or govern, then the design has already failed.

---

End of Orchestrator README
