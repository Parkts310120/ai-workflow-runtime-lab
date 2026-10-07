# Evidence contract

R1 should be evaluated from inspectable mechanisms and executed verification, not from autonomy claims.

## Mechanism-to-proof map

| Claim | Inspect | Verification focus |
|---|---|---|
| Loop is bounded | `budgets.py`, `engine.py` | iteration/call exhaustion; check-before-call |
| Provider cannot expand budget | `evaluator.py` | requested budget expansion rejected |
| Authority is deny-by-default | `policy.py` | unknown/undeclared/escalated/write/execute denied |
| Approval is external | `approvals.py`, `evaluator.py` | provider claim rejected; exact record required |
| State is explicit | `state_machine.py` | valid/invalid/terminal transitions |
| Audit is sanitized/fail-closed | `ledger.py`, `engine.py` | no prompt/output fields; ledger failure halts |
| Examples are deterministic | `examples/`, `scenario.py` | stable success/denial/exhaustion results |

## Local verification commands

```bash
python -m compileall -q src tests scripts
PYTHONPATH=src python -m unittest discover -s tests -v
PYTHONPATH=src python -m runtime_lab.cli examples/read_only_success.json
PYTHONPATH=src python -m runtime_lab.cli examples/authority_denial.json
PYTHONPATH=src python -m runtime_lab.cli examples/budget_exhaustion.json
python scripts/check_public_boundary.py
```

A test count, CI-green statement, QA disposition or Security disposition is evidence only after the corresponding command/run/review actually occurs on the identified candidate SHA.

## Required promotion evidence

Before describing R1 as verified public-main proof:

- exact public candidate SHA;
- deterministic test command and observed result;
- exact-SHA read-only CI success;
- deterministic example success/authority-denial/budget-exhaustion evidence;
- Independent QA against that SHA;
- Security/confidentiality review against that SHA;
- history-aware secret review with method/limitations documented;
- human/Queen merge approval;
- verified merge provenance to default branch;
- fresh post-merge `main` CI success.

## Claims not unlocked by R1

Even a fully green R1 does not prove production readiness, arbitrary secure code execution, enterprise autonomy, distributed scalability, high availability, model superiority, cost savings, production persistence or business impact.
