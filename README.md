# AI Workflow Runtime Lab

A clean-room public proof of **bounded AI-workflow engineering**. The project focuses on a narrower question than “how autonomous can an agent be?”:

> How can application code treat provider output as untrusted input while keeping iteration, authority, approval and audit boundaries explicit?

R1 is deliberately deterministic. It uses a `ScriptedProvider`, synthetic fixtures and Python 3.12 standard-library code so the safety and lifecycle mechanisms are inspectable without a live model, cloud API, local model server or paid dependency.

## What R1 proves

- the application owns the generator/reviewer loop;
- iteration and provider-call budgets are hard bounds checked before work;
- provider output cannot expand configured budgets;
- a deterministic evaluator is separate from authority;
- authority is deny-by-default and only the synthetic `fixture.read` capability can be considered;
- undeclared, unknown, escalated, write and execute requests are denied;
- human approval records live outside provider output;
- provider text cannot synthesize approval;
- run transitions are explicit and terminal states cannot silently resume;
- required audit-write failure stops execution;
- the event ledger persists bounded operational metadata, not prompts or provider response text;
- success, authority denial and budget exhaustion are reproducible without network access.

## Architecture

```text
synthetic RunSpec
      |
      v
 WorkflowEngine --------------------+
      |                              |
      +--> BudgetGuard               |
      +--> ScriptedProvider          |
      +--> DeterministicEvaluator    |
      +--> AuthorityPolicy           |
      +--> ApprovalStore             |
      +--> EventLedger               |
      |                              |
      +------------------------------+
      v
 terminal RunState
```

The evaluator can reject candidate quality/scope. It cannot grant capability authority. The provider can suggest work and review a candidate. It cannot mutate policy, budgets or the external approval store.

See [Architecture](docs/ARCHITECTURE.md), [Security](docs/SECURITY.md), [Decisions](docs/DECISIONS.md) and [Evidence](docs/EVIDENCE.md).

## Run the deterministic examples

No dependency installation is required.

```bash
PYTHONPATH=src python -m runtime_lab.cli examples/read_only_success.json
PYTHONPATH=src python -m runtime_lab.cli examples/authority_denial.json
PYTHONPATH=src python -m runtime_lab.cli examples/budget_exhaustion.json
```

To persist sanitized transition metadata locally:

```bash
PYTHONPATH=src python -m runtime_lab.cli examples/read_only_success.json \
  --ledger .runtime-lab/events.jsonl
```

## Verify

```bash
python -m compileall -q src tests scripts
PYTHONPATH=src python -m unittest discover -s tests -v
python scripts/check_public_boundary.py
```

CI runs the same deterministic verification under Python 3.12 with `contents: read` only and no model/API credentials.

## R1 limitations

This repository is **not** a production agent platform and does not claim production readiness. R1 intentionally has no:

- live LLM, cloud-provider or local-model adapter;
- arbitrary shell, filesystem, network, GitHub, merge or deploy tool;
- autonomous scheduler/background worker;
- production persistence or distributed queue;
- multi-tenant authorization or high-availability design;
- automatic activation after a human approval record;
- business-impact, scale, latency, cost-savings or model-quality claim.

The only executable capability policy surface is synthetic/read-only. A `verified` run state means the deterministic R1 lifecycle completed; it is not a security certification, production certification or permission to deploy.

## Clean-room disclosure

This repository was started with new public history and independently implemented for this portfolio proof. It does not import private repository history, private source code, prompts, adapters, private telemetry, internal URLs, credentials, organization names or machine-specific runtime details.
