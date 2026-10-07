# Architecture

## Goal

R1 demonstrates a bounded workflow runtime in which provider output is data, not authority. The implementation intentionally separates lifecycle, quality evaluation, capability policy, human approval and audit history.

## Components

### `RunSpec`
Immutable run intent: synthetic task, declared capability scope and hard budgets. Defaults are two iterations and four provider calls. R1 rejects configuration above four iterations or eight provider calls.

### `WorkflowEngine`
Owns the generator/reviewer control loop. It checks budgets before provider calls, invokes deterministic evaluation, asks the authority policy about every requested capability, records transitions before applying them, and returns a structured terminal result.

### `BudgetGuard`
Tracks iteration and provider-call counters. Maxima are read-only after construction. An attempted provider call consumes budget before the provider is invoked, so malformed output and provider exceptions cannot become free retries.

### `ScriptedProvider`
A deterministic sequence of candidate/review responses. It exists for public proof, tests and examples. It has no network, shell, filesystem, repository or deployment adapter.

### `DeterministicEvaluator`
Checks candidate type, objective, forbidden access, provider-claimed approval and budget-expansion attempts. Evaluation is a quality/scope gate only; it does not grant capability authority.

### `AuthorityPolicy`
Deny-by-default. R1 knows only `fixture.read`, and only read access can be allowed. Unknown, undeclared, escalated, write and execute requests fail closed. When a declaration requires human approval, the policy consults the external `ApprovalStore` using exact run/capability/access scope.

### `ApprovalStore`
Holds explicit records supplied by application code. Provider output cannot write records into this store. A rejection is a terminal policy outcome; absence of a required record produces `AWAITING_HUMAN`.

### `EventLedger`
Receives an event before each state transition. `JsonlEventLedger` appends one structured JSON object per line. Its schema contains run IDs, states, counters and bounded decision/failure codes. There is no free-form prompt, model output or exception-message field.

## State model

```text
CREATED -> RUNNING -> CANDIDATE_READY -> REVIEWED -> VERIFIED
              |              |
              |              +-> RUNNING (bounded revision)
              |              +-> AWAITING_HUMAN
              |              +-> BUDGET_EXHAUSTED / FAILED
              +-> AWAITING_HUMAN
              +-> REJECTED
              +-> AUTHORITY_DENIED
              +-> BUDGET_EXHAUSTED
              +-> FAILED
```

Terminal states do not resume silently.

## One iteration

1. Begin an iteration if the hard iteration budget permits it.
2. Consume provider-call budget **before** generation.
3. Treat returned data as untrusted candidate input.
4. Deterministically evaluate shape/scope.
5. Evaluate each capability request through authority policy.
6. Record and apply `CANDIDATE_READY` only when evaluation/authority permit it.
7. Consume provider-call budget **before** reviewer invocation.
8. Provider review can request bounded revision or quality pass; it cannot grant authority.
9. A pass moves through `REVIEWED` to `VERIFIED` with audited transitions.

## Audit ordering

For a required transition, the event is appended before in-memory state changes. If the ledger append fails, the runtime returns `FAILED / audit_failure` and does not invoke later provider work. This is deliberate fail-closed behavior.
