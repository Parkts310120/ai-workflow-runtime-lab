# Engineering decisions

## D1 — Deterministic provider before model integration

**Decision:** R1 uses `ScriptedProvider` only.

**Why:** The public proof is about authority, budgets, state and auditability. A live model would add network/credential/nondeterminism without strengthening those claims.

**Deferred:** Any live cloud/local-model provider is a separate future review.

## D2 — Standard library first

**Decision:** R1 runtime/tests use Python's standard library.

**Why:** Fewer dependencies make the trust surface and reproducibility easier to inspect. The project is not a framework demonstration.

## D3 — Quality and authority are separate

**Decision:** `DeterministicEvaluator` can pass/reject candidate scope; `AuthorityPolicy` independently decides capability authority.

**Why:** A quality verdict must never become a permission grant.

## D4 — Budgets are application-owned immutable maxima

**Decision:** Runtime budgets are configured in `RunSpec`, enforced by `BudgetGuard`, consumed before provider calls, and cannot be increased by candidate output.

**Why:** Retrying malformed/erroring provider calls must remain bounded.

## D5 — Approval is external to provider output

**Decision:** `ApprovalStore` accepts application-supplied `ApprovalRecord`; provider claims of approval are invalid candidate output.

**Why:** A provider cannot authorize itself.

## D6 — Audit before transition

**Decision:** Required transition metadata is appended before in-memory state changes.

**Why:** Continuing after an unrecorded critical transition would make the proof unauditable; R1 fails closed instead.

## D7 — No real tool adapters in R1

**Decision:** Capability policy reasons about one synthetic read capability but does not execute a tool.

**Why:** This isolates policy correctness from shell/filesystem/network/GitHub/deploy risk.
