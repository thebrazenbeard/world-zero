# World Zero Scientific Comparison Spine V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the hostile-reviewed scientific comparison spine that supports higher-order causal topology, exact implementation coverage, predictive benchmarks, frozen comparison protocols, and accounting firewalls before modern World Zero sector calibration.

**Architecture:** File-first typed scientific contracts under `src/worldzero/science/` define claims, topologies, family/benchmark manifests, mechanism admissions, partitions, preregistered comparisons and structural result labels. Causal topology uses hyperedge-compatible V2 relations; executable code must emit implementation coverage against the declared topology; run receipts separate scientific-subject identity from numerical execution identity. Energy and regional trade accounting receive explicit reconciliation identities before F3/F5 sector work.

**Tech Stack:** Python 3.12, Pydantic v2, standard-library `json`/`hashlib`, PyYAML, pytest, Ruff, mypy. NumPy/SciPy are not required until numerical-engine/sector work. No database or network dependency in this plan.

**Spec:** `docs/superpowers/specs/2026-09-17-world-zero-scientific-control-plane-design-v2.md`

## Global Constraints

- Current topology schema is `specs/CAUSAL_TOPOLOGY_V2.schema.json`; V1 is superseded provenance.
- Evidence classes are exactly `OBSERVED`, `DERIVED`, `INFERRED`, `HYPOTHESIS`, `DISPUTED`, `UNKNOWN`, `SUPERSEDED`.
- Control modes are exactly `ENDOGENOUS`, `EXOGENOUS_TRAJECTORY`, `INTERVENTION_CONTROLLED`, `ABSENT`.
- `UNKNOWN` remains unknown; never coerce it to `0`, `False`, nominal midpoint or empty string.
- Scientific identity and execution identity are separate digests.
- Confirmatory comparison rules are frozen before execution.
- Predictive benchmarks receive no causal interpretation.
- F7 composition fails closed when mechanism-admission requirements are incomplete.
- Causal topology and implementation coverage must reconcile before qualification-grade runs.
- Energy-sector own use/transition energy and regional physical trade must reconcile exactly once.
- No merge, deployment, provider mutation or predictive qualification is authorized by completing this plan.

---

### Task 1: Scientific vocabulary and deterministic content identities

**Files:**
- Create: `src/worldzero/science/__init__.py`
- Create: `src/worldzero/science/types.py`
- Create: `src/worldzero/science/canonical.py`
- Create: `tests/science/test_types.py`
- Create: `tests/science/test_canonical.py`

**Interfaces:**
- Produces: `EvidenceClass`, `ControlMode`, `StructuralResultLabel`, `BenchmarkResultLabel`, `IdentifiabilityClass`, `AdmissionDisposition`, `canonical_json_bytes(value) -> bytes`, `content_digest(value) -> str`.

- [ ] **Step 1: Write enum RED tests**

```python
from worldzero.science.types import EvidenceClass, ControlMode


def test_evidence_classes_are_exact():
    assert {x.value for x in EvidenceClass} == {
        "OBSERVED", "DERIVED", "INFERRED", "HYPOTHESIS",
        "DISPUTED", "UNKNOWN", "SUPERSEDED",
    }


def test_control_modes_are_exact():
    assert {x.value for x in ControlMode} == {
        "ENDOGENOUS", "EXOGENOUS_TRAJECTORY",
        "INTERVENTION_CONTROLLED", "ABSENT",
    }
```

- [ ] **Step 2: Write canonical-digest RED tests**

```python
from worldzero.science.canonical import content_digest


def test_mapping_key_order_does_not_change_digest():
    assert content_digest({"b": 2, "a": 1}) == content_digest({"a": 1, "b": 2})


def test_semantic_change_changes_digest():
    assert content_digest({"kind": "OBSERVED"}) != content_digest({"kind": "INFERRED"})
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_types.py tests/science/test_canonical.py -q`
Expected: FAIL because package is absent.

- [ ] **Step 4: Implement canonical serialization**

Rules:
- UTF-8;
- sorted mapping keys;
- compact JSON separators;
- list order preserved;
- reject NaN/Infinity;
- Pydantic models dumped with `exclude_none=False`;
- SHA-256 lowercase hex.

- [ ] **Step 5: Run quality gates**

```bash
pytest tests/science/test_types.py tests/science/test_canonical.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/worldzero/science tests/science
git commit -m "feat: add scientific types and stable content identities"
```

---

### Task 2: Claims and upstream evidence-lineage registry

**Files:**
- Create: `src/worldzero/science/claims.py`
- Create: `src/worldzero/science/lineage.py`
- Create: `tests/science/test_claims.py`
- Create: `tests/science/test_lineage.py`
- Create: `specs/CLAIM_RECORD_V1.schema.json`

**Interfaces:**
- Produces: `SourceRef`, `ClaimRecord`, `ClaimRegistry`, `LineageRef`, `LineageRegistry`.

- [ ] **Step 1: Write claim-revision RED test**

```python
from worldzero.science.claims import ClaimRecord, ClaimRegistry


def test_claim_revision_preserves_old_revision():
    registry = ClaimRegistry()
    registry.add(ClaimRecord(
        claim_id="C007", revision=1,
        proposition="Rebound may be material.",
        evidence_class="DISPUTED",
    ))
    registry.add(ClaimRecord(
        claim_id="C007", revision=2,
        proposition="Rebound magnitude is sector- and horizon-sensitive.",
        evidence_class="INFERRED",
        supersedes_revision=1,
    ))
    assert registry.get("C007", 1).proposition == "Rebound may be material."
    assert registry.current("C007").revision == 2
```

- [ ] **Step 2: Write correlated-source lineage RED test**

```python
from worldzero.science.lineage import LineageRegistry, LineageRef


def test_derived_sources_can_share_one_upstream_lineage():
    registry = LineageRegistry([
        LineageRef(source_id="SERIES_A", upstream_lineage_id="ROOT_X"),
        LineageRef(source_id="SERIES_B", upstream_lineage_id="ROOT_X"),
    ])
    assert registry.independent_source_count({"SERIES_A", "SERIES_B"}) == 1
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_claims.py tests/science/test_lineage.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement append-oriented claims**

Required fields:
- `claim_id`, `revision`, `proposition`, `evidence_class`;
- optional scope, sources, rivals, model obligation, downgrade condition, supersedes revision.

Reject duplicate revision IDs and missing superseded revisions.

- [ ] **Step 5: Implement lineage grouping**

`LineageRef` fields:
- `source_id`;
- `upstream_lineage_id`;
- optional `derivation_kind`;
- optional parent source IDs.

`independent_source_count()` counts unique upstream roots, not transformed series count.

- [ ] **Step 6: Export claim schema and commit**

```bash
pytest tests/science/test_claims.py tests/science/test_lineage.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science tests/science specs/CLAIM_RECORD_V1.schema.json
git commit -m "feat: preserve claim revisions and evidence lineage"
```

---

### Task 3: Hyperedge topology V2 and topology integrity

**Files:**
- Create: `src/worldzero/science/topology.py`
- Create: `tests/science/fixtures/minimal_topology_v2.json`
- Create: `tests/science/test_topology_v2.py`
- Use: `specs/CAUSAL_TOPOLOGY_V2.schema.json`

**Interfaces:**
- Produces: `TopologyNode`, `TopologyRelation`, `KillTest`, `CausalTopologyV2`, `CausalTopologyV2.digest()`.

- [ ] **Step 1: Write multi-input relation RED test**

```python
from worldzero.science.topology import CausalTopologyV2


def test_joint_relation_preserves_multi_input_semantics():
    topology = make_topology(
        nodes=["SCARCITY", "INCOME", "INVENTORY", "DEMAND"],
        relation={
            "id": "DEMAND_RESPONSE",
            "inputs": ["SCARCITY", "INCOME", "INVENTORY"],
            "outputs": ["DEMAND"],
            "relation_type": "JOINT_RESPONSE",
            "functional_form_class": "NONLINEAR",
            "polarity": "MIXED",
        },
    )
    assert topology.relations[0].inputs == ("SCARCITY", "INCOME", "INVENTORY")
```

- [ ] **Step 2: Write referential-integrity RED test**

```python
import pytest


def test_topology_rejects_missing_input_node():
    payload = minimal_payload()
    payload["relations"][0]["inputs"] = ["DOES_NOT_EXIST"]
    with pytest.raises(ValueError, match="DOES_NOT_EXIST"):
        CausalTopologyV2.model_validate(payload)
```

- [ ] **Step 3: Write no-self-commit RED test**

```python
def test_topology_contract_has_no_self_referential_source_commit():
    assert "source_commit" not in CausalTopologyV2.model_fields
```

- [ ] **Step 4: Verify RED**

Run: `pytest tests/science/test_topology_v2.py -q`
Expected: FAIL.

- [ ] **Step 5: Implement topology validation**

Validate:
- unique node IDs;
- unique relation IDs;
- every input/output node exists;
- relation scope is present;
- every referenced kill test exists;
- local rival relation IDs exist, external rivals use `family_id:relation_id` syntax;
- no empty input/output arrays.

- [ ] **Step 6: Test digest behavior**

```python
def test_topology_digest_changes_when_functional_class_changes(topology):
    changed = topology.model_copy(deep=True)
    changed.relations[0].functional_form_class = "THRESHOLD"
    assert changed.digest() != topology.digest()
```

- [ ] **Step 7: Run and commit**

```bash
pytest tests/science/test_topology_v2.py -q
ruff check src/worldzero/science/topology.py tests/science/test_topology_v2.py
mypy src/worldzero/science/topology.py
git add src/worldzero/science/topology.py tests/science
git commit -m "feat: represent higher-order causal topology"
```

---

### Task 4: Implementation coverage and relation-level behavioral contracts

**Files:**
- Create: `src/worldzero/science/implementation_coverage.py`
- Create: `tests/science/test_implementation_coverage.py`
- Use: `specs/IMPLEMENTATION_COVERAGE_V1.schema.json`

**Interfaces:**
- Produces: `ImplementationBinding`, `ImplementationCoverage`, `validate_coverage(topology, coverage)`.

- [ ] **Step 1: Write RED missing-binding test**

```python
import pytest


def test_active_relation_without_code_binding_fails(topology, coverage):
    coverage.bindings = [b for b in coverage.bindings if b.topology_object_id != "DEMAND_RESPONSE"]
    with pytest.raises(ValueError, match="DEMAND_RESPONSE"):
        validate_coverage(topology, coverage)
```

- [ ] **Step 2: Write RED undeclared-runtime-relation test**

```python
def test_undeclared_runtime_relation_prevents_pass(coverage):
    coverage.undeclared_runtime_relations = ["HIDDEN_COUPLING"]
    assert coverage.coverage_status != "PASS"
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_implementation_coverage.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement exact coverage reconciliation**

PASS requires:
- every active topology relation bound or explicitly `INTENTIONALLY_EXTERNAL`;
- every required node binding present where implementation binding is declared;
- no undeclared runtime relation IDs;
- no missing declared relation IDs;
- at least one micro-test ID for every endogenous relation.

- [ ] **Step 5: Add polarity/limiting-case micro-test convention**

Document/test convention that relation micro-tests use fixtures such as:

```python
def test_scarcity_price_relation_has_expected_limiting_direction():
    assert price_response(scarcity=0.8, income=1.0, inventory=0.1) > price_response(
        scarcity=0.2, income=1.0, inventory=0.1
    )
```

The framework does not infer causality from this test; it only checks implementation matches declared behavioral direction in the tested limit.

- [ ] **Step 6: Run and commit**

```bash
pytest tests/science/test_implementation_coverage.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science/implementation_coverage.py tests/science
git commit -m "feat: reconcile causal topology with executable bindings"
```

---

### Task 5: Mechanism admission and F7 composition gate

**Files:**
- Create: `src/worldzero/science/mechanisms.py`
- Create: `tests/science/test_mechanisms.py`
- Create: `specs/MECHANISM_ADMISSION_V1.schema.json`

**Interfaces:**
- Produces: `MechanismAdmission`, `MechanismRegistry`, `assert_f7_admissible(...)`.

- [ ] **Step 1: Write RED rival-only mechanism test**

```python
def test_unidentifiable_mechanism_can_remain_rival_only():
    m = MechanismAdmission(
        mechanism_id="THRESHOLD_X",
        proposition="Subsystem may switch regime above stress threshold.",
        evidence_class="HYPOTHESIS",
        identifiability="UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE",
        disposition="RIVAL_FAMILY_ONLY",
        kill_test_id="KT_THRESHOLD_X",
        ablation_expectation="smooth null remains available",
    )
    assert m.disposition.value == "RIVAL_FAMILY_ONLY"
```

- [ ] **Step 2: Write RED F7 rejection test**

```python
import pytest


def test_f7_rejects_missing_holdout_or_invariant_target(incomplete_registry):
    with pytest.raises(ValueError, match="holdout"):
        assert_f7_admissible(["INCOMPLETE"], incomplete_registry)
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_mechanisms.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement V1 admission gate**

F7 requires:
- clarity pass;
- identifiability at least `WEAKLY_IDENTIFIABLE` unless hard-invariant exception;
- kill test;
- holdout/invariant target;
- ablation expectation;
- complexity counts;
- numerical-integrity PASS;
- zero unresolved negative-transfer defects.

Invariant exceptions grant no causal-validation credit.

- [ ] **Step 5: Run/export schema/commit**

```bash
pytest tests/science/test_mechanisms.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science/mechanisms.py tests/science specs/MECHANISM_ADMISSION_V1.schema.json
git commit -m "feat: gate mechanisms before minimal synthesis"
```

---

### Task 6: Causal-family manifests and non-causal predictive benchmarks

**Files:**
- Create: `src/worldzero/science/families.py`
- Create: `src/worldzero/science/benchmarks.py`
- Create: `tests/science/test_families.py`
- Create: `tests/science/test_benchmarks.py`
- Create: `specs/MODEL_FAMILY_V1.schema.json`
- Create: `model_families/F0_WORLD3_CONTROL.yaml`
- Create: `model_families/F1_MARKET_ADAPTIVE.yaml`
- Create: `model_families/F3_NET_ENERGY_MATERIAL.yaml`
- Create: `benchmarks/B0_PERSISTENCE_TREND.yaml`
- Create: `benchmarks/B1_REDUCED_FORM_EMPIRICAL.yaml`

**Interfaces:**
- Produces: `ModelFamilyManifest`, `BenchmarkManifest`, `FamilyRegistry`, `BenchmarkRegistry`.

- [ ] **Step 1: Write RED causal/benchmark namespace test**

```python
def test_benchmark_cannot_claim_causal_topology_digest():
    manifest = BenchmarkManifest(
        benchmark_id="B0_PERSISTENCE_TREND",
        method="PERSISTENCE",
        causal_interpretation=False,
    )
    assert not hasattr(manifest, "topology_digest")
```

- [ ] **Step 2: Write RED F0 forbidden-mechanism test**

```python
import pytest


def test_f0_rejects_market_price_feedback(f0, mechanisms):
    with pytest.raises(ValueError, match="forbidden"):
        f0.validate_enabled_mechanisms({"WORLD3_CORE", "SCARCITY_PRICE_FEEDBACK"}, mechanisms)
```

- [ ] **Step 3: Write RED benchmark holdout-isolation test**

```python
def test_b1_hyperparameter_search_uses_calibration_only(b1_runner, partitions):
    used_ids = b1_runner.hyperparameter_search_observation_ids(partitions)
    assert used_ids.isdisjoint(partitions.final_holdout_ids)
```

- [ ] **Step 4: Verify RED**

Run: `pytest tests/science/test_families.py tests/science/test_benchmarks.py -q`
Expected: FAIL.

- [ ] **Step 5: Implement manifests and seed only F0/F1/F3 + B0/B1**

Do not create decorative empty F2/F4/F5/F6/F7 manifests.

B0 supports preregistered persistence/trend forms.
B1 manifest declares reduced-form method class, feature set, regularization/hyperparameter policy and no causal interpretation.

- [ ] **Step 6: Run/export schema/commit**

```bash
pytest tests/science/test_families.py tests/science/test_benchmarks.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science tests/science specs/MODEL_FAMILY_V1.schema.json model_families benchmarks
git commit -m "feat: compare causal families with cheap predictive benchmarks"
```

---

### Task 7: Observation maps, evidence covariance groups and frozen partitions

**Files:**
- Create: `src/worldzero/science/observations.py`
- Create: `src/worldzero/science/partitions.py`
- Create: `tests/science/test_observations.py`
- Create: `tests/science/test_partitions.py`

**Interfaces:**
- Produces: `ObservationMapping`, `EvidencePartition`, `PartitionSet`, `assert_no_holdout_leakage(...)`.

- [ ] **Step 1: Write RED upstream-lineage preservation test**

```python
def test_observation_mapping_preserves_upstream_lineage():
    mapping = ObservationMapping(
        observable_id="ENERGY_INTENSITY",
        dataset_id="DERIVED_SERIES_A",
        dataset_digest="a" * 64,
        transform_digest="b" * 64,
        upstream_lineage_id="IEA_ROOT_SERIES",
        evidence_class="DERIVED",
        unit="MJ/USD",
    )
    assert mapping.upstream_lineage_id == "IEA_ROOT_SERIES"
```

- [ ] **Step 2: Write RED leakage test**

```python
import pytest


def test_calibration_and_final_holdout_cannot_overlap():
    with pytest.raises(ValueError, match="overlap"):
        assert_no_holdout_leakage({"x", "y"}, {"y", "z"})
```

- [ ] **Step 3: Write RED covariance-group warning test**

```python
def test_shared_covariance_group_is_not_counted_as_independent_confirmation():
    summary = summarize_independence([
        obs("a", covariance_group="ROOT1"),
        obs("b", covariance_group="ROOT1"),
    ])
    assert summary.independent_group_count == 1
```

- [ ] **Step 4: Verify RED**

Run: `pytest tests/science/test_observations.py tests/science/test_partitions.py -q`
Expected: FAIL.

- [ ] **Step 5: Implement partition classes**

Classes:
`CALIBRATION`, `TEMPORAL_HOLDOUT`, `REGIONAL_HOLDOUT`, `VARIABLE_HOLDOUT`, `SHOCK_HOLDOUT`, `NEGATIVE_CONTROL`.

Observation values may not appear in both calibration and qualification holdouts within one comparison protocol.

- [ ] **Step 6: Run and commit**

```bash
pytest tests/science/test_observations.py tests/science/test_partitions.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science/observations.py src/worldzero/science/partitions.py tests/science
git commit -m "feat: preserve observation lineage and holdout isolation"
```

---

### Task 8: Frozen comparison protocols and post-hoc-change rejection

**Files:**
- Create: `src/worldzero/science/comparison_protocol.py`
- Create: `tests/science/test_comparison_protocol.py`
- Use: `specs/COMPARISON_PROTOCOL_V1.schema.json`

**Interfaces:**
- Produces: `ComparisonSubject`, `MetricSpec`, `DecisionRule`, `ComparisonProtocol`, `ComparisonProtocol.digest()`.

- [ ] **Step 1: Write RED minimum-subject test**

```python
import pytest
from pydantic import ValidationError


def test_protocol_requires_at_least_two_subjects():
    with pytest.raises(ValidationError):
        make_protocol(subjects=[subject("F0_WORLD3_CONTROL")])
```

- [ ] **Step 2: Write RED frozen-mutation test**

```python
import pytest


def test_frozen_protocol_rejects_metric_change(protocol):
    frozen = protocol.freeze()
    with pytest.raises(TypeError):
        frozen.metrics[0].threshold = 0.25
```

- [ ] **Step 3: Write RED exploratory-downgrade test**

```python
def test_protocol_frozen_after_result_inspection_is_exploratory():
    protocol = make_protocol(frozen_before_execution=False)
    assert protocol.qualification_mode == "EXPLORATORY"
```

- [ ] **Step 4: Verify RED**

Run: `pytest tests/science/test_comparison_protocol.py -q`
Expected: FAIL.

- [ ] **Step 5: Implement schema-compatible protocol and digest**

Bind claim, subjects, partitions, metrics, decision rules, missing-subject policy, identifiability gate and confirmatory/exploratory status.

- [ ] **Step 6: Run and commit**

```bash
pytest tests/science/test_comparison_protocol.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science/comparison_protocol.py tests/science
git commit -m "feat: freeze comparison rules before holdout execution"
```

---

### Task 9: Exact subject/execution receipts and structural comparison

**Files:**
- Create: `src/worldzero/receipts/__init__.py`
- Create: `src/worldzero/receipts/run_receipt.py`
- Create: `src/worldzero/science/comparison.py`
- Create: `tests/receipts/test_run_receipt.py`
- Create: `tests/science/test_comparison.py`
- Create: `specs/RUN_RECEIPT_V1.schema.json`

**Interfaces:**
- Produces: `ScientificSubjectIdentity`, `ExecutionIdentity`, `RunReceipt`, `FamilyRunResult`, `ClaimComparison`.

- [ ] **Step 1: Write RED solver-identity separation test**

```python
def test_solver_change_only_changes_execution_identity(base_receipt):
    a = base_receipt.with_solver("EULER")
    b = base_receipt.with_solver("RK45")
    assert a.subject.digest() == b.subject.digest()
    assert a.execution.digest() != b.execution.digest()
    assert a.digest() != b.digest()
```

- [ ] **Step 2: Write RED missing-subject robustness test**

```python
import pytest


def test_robust_label_requires_every_frozen_subject(protocol, results_without_f3):
    with pytest.raises(ValueError, match="F3_NET_ENERGY_MATERIAL"):
        compare(protocol, results_without_f3)
```

- [ ] **Step 3: Write RED family-sensitive test**

```python
def test_disagreeing_valid_causal_families_are_family_sensitive(protocol, results):
    results["F1_MARKET_ADAPTIVE"].direction = "SUPPORTED"
    results["F3_NET_ENERGY_MATERIAL"].direction = "NOT_SUPPORTED"
    comparison = compare(protocol, results)
    assert comparison.structural_label.value == "FAMILY_SENSITIVE"
```

- [ ] **Step 4: Write RED benchmark-superior test**

```python
def test_benchmark_can_outperform_all_causal_families(protocol, results):
    results["B1_REDUCED_FORM_EMPIRICAL"].metrics["RMSE"] = 0.5
    results["F0_WORLD3_CONTROL"].metrics["RMSE"] = 1.0
    results["F1_MARKET_ADAPTIVE"].metrics["RMSE"] = 0.9
    comparison = compare(protocol, results)
    assert comparison.benchmark_labels["B1_REDUCED_FORM_EMPIRICAL"] == "BENCHMARK_SUPERIOR_ON_HISTORICAL_HOLDOUT"
```

- [ ] **Step 5: Verify RED**

Run: `pytest tests/receipts/test_run_receipt.py tests/science/test_comparison.py -q`
Expected: FAIL.

- [ ] **Step 6: Implement identities and conservative comparison rules**

Scientific subject binds:
- Git tree/commit;
- topology digest for causal families;
- manifest digest;
- implementation-coverage digest for causal families;
- dataset/parameter/region/scenario/observation-map digests;
- partition IDs;
- comparison-protocol digest.

Execution binds solver/timestep/tolerance/seed/environment.

- [ ] **Step 7: Run/export schema/commit**

```bash
pytest tests/receipts/test_run_receipt.py tests/science/test_comparison.py -q
ruff check src/worldzero/receipts src/worldzero/science tests
mypy src/worldzero/receipts src/worldzero/science
git add src/worldzero/receipts src/worldzero/science tests specs/RUN_RECEIPT_V1.schema.json
git commit -m "feat: bind exact subjects and compare structural rivals"
```

---

### Task 10: Energy and regional-trade accounting firewalls

**Files:**
- Create: `src/worldzero/accounting/__init__.py`
- Create: `src/worldzero/accounting/energy.py`
- Create: `src/worldzero/accounting/trade.py`
- Create: `tests/accounting/test_energy_reconciliation.py`
- Create: `tests/accounting/test_trade_reconciliation.py`

**Interfaces:**
- Produces: `EnergyAccount`, `EnergyReconciliation`, `TradeFlow`, `TradeReconciliation`.

- [ ] **Step 1: Write RED energy one-count test**

```python
def test_energy_sector_own_use_is_counted_once():
    account = EnergyAccount(
        gross=100.0,
        conversion_loss=10.0,
        sector_own_use=8.0,
        final_energy=82.0,
    )
    assert account.reconcile().difference == 0.0
```

- [ ] **Step 2: Write RED double-count detector**

```python
import pytest


def test_embodied_transition_energy_cannot_be_subtracted_twice():
    with pytest.raises(ValueError, match="double-count"):
        reconcile_transition_energy(
            sector_own_use=8.0,
            embodied_energy=5.0,
            industrial_energy_demand_includes_embodied=5.0,
            subtract_embodied_again=True,
        )
```

- [ ] **Step 3: Write RED regional trade conservation test**

```python
def test_trade_routing_conserves_global_physical_stock():
    flows = [
        TradeFlow(origin="A", destination="B", amount=10.0, loss=1.0),
        TradeFlow(origin="B", destination="C", amount=4.0, loss=0.5),
    ]
    result = reconcile_trade(flows)
    assert result.total_origin_debits == result.total_destination_credits + result.total_losses
```

- [ ] **Step 4: Verify RED**

Run: `pytest tests/accounting -q`
Expected: FAIL.

- [ ] **Step 5: Implement minimal accounting-only objects**

Do not implement F3/F5 sector behavior yet. These modules provide reconciliation identities consumed later by energy/trade sectors.

- [ ] **Step 6: Run full spine suite and commit**

```bash
pytest tests/science tests/receipts tests/accounting -q
ruff check src tests
mypy src/worldzero
git add src/worldzero/accounting tests/accounting
git commit -m "feat: add energy and trade accounting firewalls"
```

---

## V2 plan self-review

Spec coverage:

- higher-order topology: Task 3;
- no self-referential commit binding: Task 3 + Task 9;
- implementation coverage: Task 4;
- claim/source lineage: Task 2;
- mechanism admission/F7: Task 5;
- non-causal benchmarks: Task 6;
- observation covariance/holdout isolation: Task 7;
- frozen comparison protocol: Task 8;
- subject vs execution identity: Task 9;
- family-sensitive and benchmark-superior outcomes: Task 9;
- net-energy/trade double-count firewalls: Task 10.

The old scientific-control-plane plan is historical V1 and must not be used for new implementation. The original broader sector plan remains downstream after this V2 spine and World3 F0 baseline are green.

No placeholders remain. F2/F4/F5/F6 detailed sector implementation is intentionally excluded; each should receive its own later plan only when evidence/kill tests justify implementation.
