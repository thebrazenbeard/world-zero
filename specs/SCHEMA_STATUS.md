# World Zero Schema Status

Date: 2026-09-17

## Current

- `CAUSAL_TOPOLOGY_V2.schema.json` — current causal-topology design candidate. Supports higher-order `inputs[] -> outputs[]` relations, explicit functional-form class, upstream source-lineage references and optional implementation bindings. Exact Git/source binding remains external to topology content.
- `CLAIM_RECORD_V1.schema.json` — current append-oriented claim-record contract.
- `COMPARISON_PROTOCOL_V1.schema.json` — current comparison preregistration contract.
- `IMPLEMENTATION_COVERAGE_V1.schema.json` — current topology-to-executable coverage contract. Executable validation fails closed on missing/undeclared active relations, digest mismatch, binding drift, and missing endogenous micro-tests; a stored `coverage_status=PASS` is not sufficient by itself.
- `MECHANISM_ADMISSION_V1.schema.json` — current mechanism-admission evidence packet. F7 composition is additionally guarded in executable code: an F7 candidate must satisfy semantic clarity, identifiability or an explicit hard-invariant exception, survive its preregistered kill test, demonstrate holdout/invariant and ablation value, document structural-rival analysis, justify complexity, pass numerical integrity, and carry no unresolved negative-transfer defect.

## Superseded

- `CAUSAL_TOPOLOGY_V1.schema.json` — superseded before implementation. Preserved as provenance. V1 was pairwise-only and its first cut contained a self-referential `source_commit` design error; that field was removed during review, but the pairwise limitation remained sufficient reason to supersede the schema with V2.

Superseded schemas are not deleted. New implementation work must target the current schema named above unless a later exact artifact explicitly supersedes it.
