# PR #2 Late-Slice Recovery Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Recover the useful PR #2 capabilities that landed while PR #4 integration was already in progress, without importing PR #2's divergent alternate scientific-control implementation.

**Architecture:** Start from canonical `main@a82d023cfaf21ef1fd922476509f6be4b1c525ab`. Port only additive contracts and implementations: run receipts, conservative comparison evaluation, energy reconciliation, trade reconciliation, and the missing benchmark schema artifact. Existing canonical comparison protocols, scientific types, manifests, partitions, coverage, CI, and dependency metadata remain authoritative.

**Tech Stack:** Python 3.12, Pydantic 2.13.4, pytest 9.0.2, Ruff 0.16.8, mypy 2.3.1, JSON Schema 2020-12.

**Spec:** `docs/superpowers/specs/2026-09-17-world-zero-scientific-control-plane-design-v2.md`

## Global Constraints

- Preserve canonical `main` behavior unless a new failing recovery test requires a bounded addition.
- Do not wholesale merge or cherry-pick PR #2's modified overlapping scientific modules.
- Causal-family identities require topology and implementation-coverage digests; predictive benchmarks must not claim causal topology.
- Benchmark outcomes never alter causal structural labels.
- Accounting helpers must fail closed on explicit double counting or physical non-conservation.
- Qualification remains software-contract/build evidence only, not scientific validity.

---
### Task 1: Exact Run-Receipt Identity

**Files:**
- Create: `tests/receipts/test_run_receipt.py`
- Create: `src/worldzero/receipts/__init__.py`
- Create: `src/worldzero/receipts/run_receipt.py`
- Create: `specs/RUN_RECEIPT_V1.schema.json`

**Interfaces:**
- Produces `ScientificSubjectIdentity`, `ExecutionIdentity`, and `RunReceipt`.
- Each identity exposes `digest() -> str`; `RunReceipt.with_solver(name: str) -> RunReceipt` changes only execution identity.

- [ ] Copy only the late PR #2 receipt tests onto the recovery branch.
- [ ] Run `python -m pytest tests/receipts/test_run_receipt.py -q` and verify RED from missing `worldzero.receipts`.
- [ ] Implement immutable Pydantic identity models with canonical content digests and causal/benchmark validation.
- [ ] Add the static `RUN_RECEIPT_V1` schema matching the runtime contract.
- [ ] Run the focused receipt tests and schema parse; require PASS.
- [ ] Commit as `feat: recover exact run receipt identities`.

### Task 2: Conservative Comparison Evaluation

**Files:**
- Create: `tests/science/test_comparison.py`
- Create: `src/worldzero/science/comparison.py`
- Modify: `src/worldzero/science/__init__.py`

**Interfaces:**
- Produces `FamilyRunResult`, `ComparisonResult`, and `compare(protocol, results)`.
- Consumes canonical `ComparisonProtocol`/`ComparisonSubject` and `StructuralResultLabel`.
- [ ] Copy only the late PR #2 comparison tests onto the recovery branch.
- [ ] Run `python -m pytest tests/science/test_comparison.py -q` and verify RED from missing evaluator.
- [ ] Implement the minimum evaluator that requires the frozen subject set, derives causal-family structural labels only from valid causal families, and evaluates predictive benchmarks separately.
- [ ] Preserve canonical post-hoc/exploratory protocol semantics; do not replace `comparison_protocol.py`.
- [ ] Run focused comparison tests plus existing comparison-protocol tests; require PASS.
- [ ] Commit as `feat: recover conservative comparison evaluator`.

### Task 3: Energy Accounting Firewall

**Files:**
- Create: `tests/accounting/test_energy_reconciliation.py`
- Create: `src/worldzero/accounting/__init__.py`
- Create: `src/worldzero/accounting/energy.py`

**Interfaces:**
- Produces `EnergyAccount.reconcile()` and `reconcile_transition_energy(...)`.
- Reconciliation exposes gross-accounted difference and explicit embodied-energy accounting fields.

- [ ] Copy the late PR #2 energy reconciliation tests.
- [ ] Run the focused test and verify RED from missing accounting package.
- [ ] Implement conservation reconciliation and explicit double-count rejection with non-negative validated inputs.
- [ ] Run focused tests; require PASS.
- [ ] Commit as `feat: recover energy accounting firewall`.

### Task 4: Trade Conservation Firewall

**Files:**
- Create: `tests/accounting/test_trade_reconciliation.py`
- Create: `src/worldzero/accounting/trade.py`
- Modify: `src/worldzero/accounting/__init__.py`

**Interfaces:**
- Produces validated `TradeFlow` and `reconcile_trade(flows)`.
- Reconciliation exposes origin debits, destination credits, total losses, and conservation difference.

- [ ] Copy the late PR #2 trade reconciliation tests.
- [ ] Run the focused test and verify RED from missing trade module.
- [ ] Implement non-negative flows, `loss <= amount`, regional aggregation, and global conservation accounting.
- [ ] Run focused tests; require PASS.
- [ ] Commit as `feat: recover trade conservation firewall`.

### Task 5: Static Benchmark Contract and Whole-Tree Qualification

**Files:**
- Create: `tests/science/test_benchmark_schema.py`
- Create: `specs/BENCHMARK_V1.schema.json`
- Modify: `specs/SCHEMA_STATUS.md`

**Interfaces:**
- Static schema must represent canonical `BenchmarkManifest` without changing runtime benchmark semantics.

- [ ] Write a failing schema test requiring `BENCHMARK_V1.schema.json`, its schema-version constant, non-causal interpretation, and final-holdout firewall.
- [ ] Run the focused test and verify RED because the schema artifact is absent.
- [ ] Add the schema artifact and record its status without replacing stronger canonical schema files.
- [ ] Run the full suite, Ruff, mypy, `uv lock --check`, both wheelhouse verifiers, and JSON/YAML parse gates.
- [ ] Reconstruct a fresh Windows offline environment and rerun the full suite/Ruff/mypy there.
- [ ] Commit as `schema: recover benchmark static contract`.
- [ ] Collision-check remote state, push the recovery branch, open a PR against current `main`, and require ordinary merge-subject CI plus literal-head Linux/Windows offline qualification before any merge.