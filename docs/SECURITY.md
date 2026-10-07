# Security and confidentiality boundary

## R1 trust model

Untrusted inputs include provider responses, synthetic scenario JSON and requested capabilities. Trusted application boundaries are the immutable run configuration, deterministic evaluator, authority policy, external approval store and state-transition rules.

## Deny-by-default authority

`fixture.read` is the only known R1 capability. It is synthetic/read-only. Permission requires:

1. an exact declaration in `RunSpec`;
2. no access escalation;
3. read access only;
4. a legal runtime state;
5. when configured, an exact external approval record.

Unknown, undeclared, write and execute requests are denied. There is no provider-controlled allowlist.

## Human approval boundary

A candidate contains a field used to test hostile provider behavior: `claimed_human_approval`. The deterministic evaluator rejects it. Real approval is represented only by `ApprovalRecord` objects supplied to `ApprovalStore` outside provider output.

R1 does not auto-activate a real external tool after approval because no real tool adapter exists.

## Audit/privacy boundary

The JSONL event schema intentionally excludes:

- prompts/brief text beyond the synthetic scenario file itself;
- provider/model response text;
- credentials and environment dumps;
- raw tool payloads;
- free-form exception messages.

Provider exceptions are persisted only as exception type codes. If required ledger writing fails, execution stops.

## CI boundary

CI is expected to use:

- GitHub-hosted runner;
- Python 3.12;
- `contents: read` permissions only;
- pinned official action commit SHAs;
- no repository write token use;
- no cloud/local model credential;
- no deploy step.

The repository includes a standard-library public-boundary check for tracked sensitive filenames and common secret-like signatures. That check is defense-in-depth, not a guarantee that no secret can ever exist. A separate exact-SHA security/confidentiality and history-aware review remains required before a verified-public promotion.

## Confidentiality

The implementation is clean-room and synthetic. Public files must not contain private project names, private source, private prompts, internal URLs, private telemetry, credentials, machine IDs or private adapter schemas.

## Out of scope

R1 does not claim secure arbitrary code execution, sandboxing, tenant isolation, production authorization, production persistence, remote networking, provider security, deployment security or enterprise readiness.
