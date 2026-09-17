# World Zero Scientific Comparison Spine Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the solver-independent scientific comparison spine that binds evidence, claims, causal topology, model families, mechanism admission, exact run identity and structural-comparison results before World Zero begins modern-sector calibration.

**Architecture:** Typed Pydantic/domain objects under `src/worldzero/science/` validate machine-readable scientific state independently from numerical sector code. Canonical serialization produces stable digests for topologies, manifests and receipts; family composition and F7 admission fail closed on missing evidence/kill-test state; validation compares exact rival subjects without reducing them to one universal score.

**Tech Stack:** Python 3.12, Pydantic v2, standard-library `hashlib`/`json`, PyYAML only where human-authored YAML is accepted, pytest, Ruff, mypy. No database, network dependency or simulation optimizer is required for this plan.

**Spec:** `docs/superpowers/specs/2026-09-17-world-zero-scientific-control-plane-design.md`

## Global Constraints

- Evidence classes are exactly `OBSERVED`, `DERIVED`, `INFERRED`, `HYPOTHESIS`, `DISPUTED`, `UNKNOWN`, `SUPERSEDED`.
- Scenario/control modes are exactly `ENDOGENOUS`, `EXOGENOUS_TRAJECTORY`, `INTERVENTION_CONTROLLED`, `ABSENT`.
- `UNKNOWN` is preserved as unknown; it must never be silently coerced to zero, false or a nominal default.
- Topology/model-family/manifest identities are deterministic content digests over canonical serialization.
- Scientific identity is independent of solver choice; changing a solver changes execution receipt identity, not topology identity.
- F7 composition fails closed when a mechanism lacks required admission state.
- A result cannot be labeled `ROBUST_ACROSS_FAMILIES` unless every declared rival family in the comparison set produced a valid result.
- Holdout observations must never enter calibration inputs.
- No task in this plan merges PRs, deploys services, downloads live datasets or makes predictive-qualification claims.

---

### Task 1: Scientific vocabulary, canonical serialization and digest primitives

**Files:**
- Create: `src/worldzero/science/__init__.py`
- Create: `src/worldzero/science/types.py`
- Create: `src/worldzero/science/canonical.py`
- Create: `tests/science/test_types.py`
- Create: `tests/science/test_canonical.py`

**Interfaces:**
- Produces: `EvidenceClass`, `ControlMode`, `StructuralResultLabel`, `IdentifiabilityClass`, `AdmissionDisposition`, `canonical_json_bytes(value) -> bytes`, `content_digest(value) -> str`.

- [ ] **Step 1: Write RED enum and UNKNOWN-preservation tests**

```python
from worldzero.science.types import EvidenceClass, ControlMode


def test_unknown_is_explicit_evidence_class():
    assert EvidenceClass.UNKNOWN.value == "UNKNOWN"


def test_control_modes_are_closed_set():
    assert {m.value for m in ControlMode} == {
        "ENDOGENOUS",
        "EXOGENOUS_TRAJECTORY",
        "INTERVENTION_CONTROLLED",
        "ABSENT",
    }
```

- [ ] **Step 2: Write RED canonical-digest tests**

```python
from worldzero.science.canonical import content_digest


def test_digest_ignores_mapping_key_order():
    assert content_digest({"b": 2, "a": 1}) == content_digest({"a": 1, "b": 2})


def test_digest_changes_when_semantics_change():
    assert content_digest({"polarity": "POSITIVE"}) != content_digest({"polarity": "NEGATIVE"})
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_types.py tests/science/test_canonical.py -q`
Expected: FAIL because the package does not exist.

- [ ] **Step 4: Implement minimal enums and canonical serializer**

Canonical JSON rules:
- UTF-8;
- sorted mapping keys;
- compact separators `(',', ':')`;
- reject NaN/Infinity;
- preserve list order;
- serialize Pydantic models from `model_dump(mode="json", exclude_none=False)`;
- SHA-256 hex digest.

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
git commit -m "feat: add scientific vocabulary and canonical digests"
```

---

### Task 2: Claim registry with append-oriented revision lineage

**Files:**
- Create: `src/worldzero/science/claims.py`
- Create: `tests/science/test_claim_registry.py`
- Create: `specs/CLAIM_RECORD_V1.schema.json`

**Interfaces:**
- Produces: `SourceRef`, `ClaimRecord`, `ClaimRegistry`, `ClaimRegistry.add_revision(...)`, `ClaimRegistry.current(claim_id)`.

- [ ] **Step 1: Write RED source/evidence validation tests**

```python
import pytest
from pydantic import ValidationError
from worldzero.science.claims import ClaimRecord


def test_claim_requires_evidence_class_and_proposition():
    with pytest.raises(ValidationError):
        ClaimRecord(claim_id="C006")
```

- [ ] **Step 2: Write RED non-rewrite lineage test**

```python
from worldzero.science.claims import ClaimRecord, ClaimRegistry
from worldzero.science.types import EvidenceClass


def test_revision_preserves_prior_record():
    registry = ClaimRegistry()
    first = ClaimRecord(
        claim_id="C007",
        revision=1,
        proposition="Economy-wide rebound may be material.",
        evidence_class=EvidenceClass.DISPUTED,
    )
    registry.add(first)
    second = registry.add_revision(
        claim_id="C007",
        proposition="Economy-wide rebound remains material but bounded by sector.",
        evidence_class=EvidenceClass.INFERRED,
        supersedes_revision=1,
    )
    assert registry.get("C007", 1) == first
    assert registry.current("C007") == second
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_claim_registry.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement exact record semantics**

`ClaimRecord` fields:
- `claim_id: str`
- `revision: int >= 1`
- `proposition: str`
- `evidence_class: EvidenceClass`
- `scope: str | None`
- `sources: tuple[SourceRef, ...]`
- `rival_interpretations: tuple[str, ...]`
- `model_obligation: str | None`
- `downgrade_condition: str | None`
- `supersedes_revision: int | None`

Reject duplicate `(claim_id, revision)` and revisions whose `supersedes_revision` does not exist.

- [ ] **Step 5: Export JSON Schema and round-trip it in test**

```python
def test_claim_json_schema_has_closed_evidence_enum():
    schema = ClaimRecord.model_json_schema()
    serialized = json.dumps(schema)
    assert "OBSERVED" in serialized
    assert "UNKNOWN" in serialized
```

Write `specs/CLAIM_RECORD_V1.schema.json` from the frozen Pydantic schema after tests pass.

- [ ] **Step 6: Run and commit**

```bash
pytest tests/science/test_claim_registry.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science/claims.py tests/science/test_claim_registry.py specs/CLAIM_RECORD_V1.schema.json
git commit -m "feat: add append-oriented scientific claim registry"
```

---

### Task 3: Causal topology parser, referential integrity and stable topology digest

**Files:**
- Create: `src/worldzero/science/topology.py`
- Create: `tests/science/fixtures/minimal_topology.json`
- Create: `tests/science/test_topology.py`
- Use: `specs/CAUSAL_TOPOLOGY_V1.schema.json`

**Interfaces:**
- Produces: `TopologyNode`, `TopologyRelation`, `KillTestRef`, `CausalTopology`, `CausalTopology.digest()`.

- [ ] **Step 1: Write RED dangling-edge test**

```python
import pytest
from worldzero.science.topology import CausalTopology


def test_topology_rejects_relation_to_missing_node():
    payload = {
        "schema_version": "CAUSAL_TOPOLOGY_V1",
        "topology_id": "bad",
        "model_family": "F0_WORLD3_CONTROL",
        "source_commit": "0" * 40,
        "nodes": [{
            "id": "A",
            "kind": "STOCK",
            "control_mode": "ENDOGENOUS",
            "evidence_class": "OBSERVED",
            "scope": {"spatial": "GLOBAL"},
        }],
        "relations": [{
            "id": "A_TO_B",
            "from": "A",
            "to": "B",
            "relation_type": "CAUSES",
            "polarity": "POSITIVE",
            "evidence_class": "HYPOTHESIS",
            "control_mode": "ENDOGENOUS",
            "scope": {"spatial": "GLOBAL"},
            "uncertainty": {"kind": "STRUCTURAL"},
        }],
        "kill_tests": [{"id": "KT1", "claim_or_mechanism": "x", "test": "y", "failure_meaning": "z"}],
    }
    with pytest.raises(ValueError, match="missing node B"):
        CausalTopology.model_validate(payload)
```

- [ ] **Step 2: Write RED semantic-digest tests**

```python
def test_relation_polarity_changes_topology_digest(minimal_topology):
    a = minimal_topology
    b = minimal_topology.model_copy(deep=True)
    b.relations[0].polarity = "NEGATIVE"
    assert a.digest() != b.digest()


def test_formatting_does_not_change_topology_digest(minimal_topology):
    payload = json.loads(minimal_topology.model_dump_json(indent=4))
    assert minimal_topology.digest() == CausalTopology.model_validate(payload).digest()
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_topology.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement schema-compatible topology models**

Validate:
- unique node IDs;
- unique relation IDs;
- relation `from` and `to` nodes exist;
- every `kill_test_id` referenced by a relation exists;
- every rival relation ID refers to a relation in this topology or is explicitly external using `family_id:relation_id` syntax;
- source commit is 40 lowercase hex characters.

- [ ] **Step 5: Freeze minimal fixture and run tests**

Run:
```bash
pytest tests/science/test_topology.py -q
ruff check src/worldzero/science/topology.py tests/science/test_topology.py
mypy src/worldzero/science/topology.py
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/worldzero/science/topology.py tests/science
git commit -m "feat: validate and digest causal topologies"
```

---

### Task 4: Mechanism admission packets and F7 fail-closed gate

**Files:**
- Create: `src/worldzero/science/mechanisms.py`
- Create: `tests/science/test_mechanism_admission.py`
- Create: `specs/MECHANISM_ADMISSION_V1.schema.json`

**Interfaces:**
- Produces: `MechanismAdmission`, `MechanismRegistry`, `assert_f7_admissible(mechanism_ids, registry)`.

- [ ] **Step 1: Write RED UNKNOWN/identifiability behavior tests**

```python
from worldzero.science.mechanisms import MechanismAdmission


def test_unidentifiable_mechanism_can_exist_without_f7_admission():
    mechanism = MechanismAdmission(
        mechanism_id="REBOUND",
        proposition="Efficiency can induce additional demand.",
        evidence_class="DISPUTED",
        identifiability="UNIDENTIFIABLE_WITH_CURRENT_EVIDENCE",
        disposition="RIVAL_FAMILY_ONLY",
        kill_test_id="KT_REBOUND_001",
        holdout_target="post-efficiency energy demand",
        ablation_expectation="energy demand falls when rebound is disabled",
    )
    assert mechanism.disposition.value == "RIVAL_FAMILY_ONLY"
```

- [ ] **Step 2: Write RED F7 rejection test**

```python
import pytest
from worldzero.science.mechanisms import assert_f7_admissible


def test_f7_rejects_mechanism_without_required_kill_test(registry_with_incomplete_mechanism):
    with pytest.raises(ValueError, match="kill test"):
        assert_f7_admissible(["INCOMPLETE"], registry_with_incomplete_mechanism)
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_mechanism_admission.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement the V1 admission object**

Required for `F7_ADMITTED`:
- nonempty proposition;
- evidence class;
- identifiability at least `WEAKLY_IDENTIFIABLE` unless `invariant_required=True`;
- nonempty null/rival description;
- kill-test ID;
- holdout target or invariant target;
- ablation expectation;
- complexity-state count and calibrated-parameter count;
- numerical-integrity status `PASS`;
- unresolved negative-transfer count `0`.

`RIVAL_FAMILY_ONLY` is allowed with weaker state and must not be auto-promoted.

- [ ] **Step 5: Export schema, run quality gates and commit**

```bash
pytest tests/science/test_mechanism_admission.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science/mechanisms.py tests/science/test_mechanism_admission.py specs/MECHANISM_ADMISSION_V1.schema.json
git commit -m "feat: enforce mechanism admission and F7 gates"
```

---

### Task 5: Rival model-family manifests and composition validation

**Files:**
- Create: `src/worldzero/science/families.py`
- Create: `tests/science/test_family_manifest.py`
- Create: `specs/MODEL_FAMILY_V1.schema.json`
- Create: `model_families/F0_WORLD3_CONTROL.yaml`
- Create: `model_families/F1_MARKET_ADAPTIVE.yaml`
- Create: `model_families/F3_NET_ENERGY_MATERIAL.yaml`

**Interfaces:**
- Produces: `ModelFamilyManifest`, `FamilyRegistry`, `validate_family_composition(...)`.

- [ ] **Step 1: Write RED forbidden-mechanism test**

```python
import pytest
from worldzero.science.families import validate_family_composition


def test_world3_control_rejects_market_price_mechanism(f0_manifest, mechanism_registry):
    with pytest.raises(ValueError, match="forbidden"):
        validate_family_composition(
            f0_manifest,
            enabled_mechanisms={"WORLD3_CORE", "SCARCITY_PRICE_FEEDBACK"},
            mechanism_registry=mechanism_registry,
        )
```

- [ ] **Step 2: Write RED topology-binding test**

```python
def test_family_manifest_binds_exact_topology_digest(minimal_topology):
    manifest = make_family_manifest(topology_digest=minimal_topology.digest())
    assert manifest.topology_digest == minimal_topology.digest()
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_family_manifest.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement family manifest semantics**

Fields:
- `family_id`
- `topology_id`
- `topology_digest`
- `enabled_sectors`
- `required_mechanisms`
- `forbidden_mechanisms`
- `parameter_schema_version`
- `observation_map_version`
- `region_set_id`
- `required_hostile_controls`
- `qualification_status`

For F7, call `assert_f7_admissible()` for every required mechanism.

- [ ] **Step 5: Seed only three family YAML files**

Seed F0, F1 and F3 because they are enough to exercise structurally different controls. Do not create empty decorative manifests for F2/F4/F5/F6/F7 until their topology/mechanism packets exist.

- [ ] **Step 6: Run, export schema and commit**

```bash
pytest tests/science/test_family_manifest.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science/families.py tests/science/test_family_manifest.py specs/MODEL_FAMILY_V1.schema.json model_families
git commit -m "feat: add rival model-family manifests"
```

---

### Task 6: Observation maps, calibration/holdout partitions and leakage guards

**Files:**
- Create: `src/worldzero/science/observations.py`
- Create: `src/worldzero/science/partitions.py`
- Create: `tests/science/test_observations.py`
- Create: `tests/science/test_partition_isolation.py`

**Interfaces:**
- Produces: `ObservationMapping`, `EvidencePartition`, `PartitionSet`, `assert_no_holdout_leakage(...)`.

- [ ] **Step 1: Write RED lineage test**

```python
def test_observation_mapping_retains_dataset_and_transform_digest():
    mapping = ObservationMapping(
        model_variable="POPULATION",
        dataset_id="UN_WPP_POP",
        dataset_digest="a" * 64,
        transform_digest="b" * 64,
        observation_class="OBSERVED",
        unit="person",
    )
    assert mapping.dataset_digest == "a" * 64
    assert mapping.transform_digest == "b" * 64
```

- [ ] **Step 2: Write RED holdout leakage test**

```python
import pytest
from worldzero.science.partitions import assert_no_holdout_leakage


def test_calibration_and_temporal_holdout_cannot_overlap():
    with pytest.raises(ValueError, match="overlap"):
        assert_no_holdout_leakage(
            calibration_ids={"obs-1", "obs-2"},
            holdout_ids={"obs-2", "obs-3"},
        )
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_observations.py tests/science/test_partition_isolation.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement explicit observation and partition classes**

Partition classes: `CALIBRATION`, `TEMPORAL_HOLDOUT`, `REGIONAL_HOLDOUT`, `VARIABLE_HOLDOUT`, `SHOCK_HOLDOUT`, `NEGATIVE_CONTROL`.

An observation ID may belong to at most one calibration-or-holdout role within a frozen comparison packet. Metadata-only source rows may be shared, but measured values cannot leak.

- [ ] **Step 5: Run and commit**

```bash
pytest tests/science/test_observations.py tests/science/test_partition_isolation.py -q
ruff check src/worldzero/science tests/science
mypy src/worldzero/science
git add src/worldzero/science/observations.py src/worldzero/science/partitions.py tests/science
git commit -m "feat: separate observation mapping from validation partitions"
```

---

### Task 7: Exact run receipts and solver-independent scientific identity

**Files:**
- Create: `src/worldzero/receipts/__init__.py`
- Create: `src/worldzero/receipts/run_receipt.py`
- Create: `tests/receipts/test_run_receipt.py`
- Create: `specs/RUN_RECEIPT_V1.schema.json`

**Interfaces:**
- Produces: `ScientificSubjectIdentity`, `ExecutionIdentity`, `RunReceipt`, `RunReceipt.digest()`.

- [ ] **Step 1: Write RED subject-versus-execution identity test**

```python
def test_solver_change_preserves_scientific_subject_but_changes_execution_receipt(base_receipt):
    rk = base_receipt.model_copy(deep=True)
    rk.execution.solver = "RK45"
    euler = base_receipt.model_copy(deep=True)
    euler.execution.solver = "EULER"
    assert rk.subject.digest() == euler.subject.digest()
    assert rk.digest() != euler.digest()
```

- [ ] **Step 2: Write RED exact-input replay test**

```python
def test_identical_receipt_payload_has_identical_digest(base_receipt):
    clone = RunReceipt.model_validate(base_receipt.model_dump(mode="json"))
    assert clone.digest() == base_receipt.digest()
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/receipts/test_run_receipt.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement split identities**

`ScientificSubjectIdentity` binds:
- Git tree/commit;
- topology digest;
- family-manifest digest;
- dataset-manifest-set digest;
- parameter digest;
- region-set digest;
- scenario/intervention digest;
- observation-map digest;
- calibration/holdout partition IDs.

`ExecutionIdentity` binds:
- solver name/version;
- timestep/tolerance;
- seed/ensemble ID;
- environment fingerprint.

- [ ] **Step 5: Export schema, run and commit**

```bash
pytest tests/receipts/test_run_receipt.py -q
ruff check src/worldzero/receipts tests/receipts
mypy src/worldzero/receipts
git add src/worldzero/receipts tests/receipts specs/RUN_RECEIPT_V1.schema.json
git commit -m "feat: bind exact scientific and execution run identities"
```

---

### Task 8: Structural comparison and scoped robustness labels

**Files:**
- Create: `src/worldzero/science/comparison.py`
- Create: `tests/science/test_structural_comparison.py`
- Create: `docs/qualification/STRUCTURAL_COMPARISON_V1.md`

**Interfaces:**
- Produces: `FamilyRunResult`, `ClaimComparison`, `compare_families(...) -> ClaimComparison`.

- [ ] **Step 1: Write RED incomplete-family-set test**

```python
import pytest
from worldzero.science.comparison import compare_families


def test_cannot_call_result_robust_when_declared_family_missing():
    with pytest.raises(ValueError, match="missing family F3_NET_ENERGY_MATERIAL"):
        compare_families(
            claim_id="ENERGY_TRANSITION_FEASIBLE",
            declared_families={"F0_WORLD3_CONTROL", "F1_MARKET_ADAPTIVE", "F3_NET_ENERGY_MATERIAL"},
            results={
                "F0_WORLD3_CONTROL": fake_result("PASS"),
                "F1_MARKET_ADAPTIVE": fake_result("PASS"),
            },
        )
```

- [ ] **Step 2: Write RED family-sensitive classification test**

```python
def test_opposing_valid_family_results_are_family_sensitive():
    comparison = compare_families(
        claim_id="ENERGY_TRANSITION_FEASIBLE",
        declared_families={"F1_MARKET_ADAPTIVE", "F3_NET_ENERGY_MATERIAL"},
        results={
            "F1_MARKET_ADAPTIVE": fake_result("SUPPORTED"),
            "F3_NET_ENERGY_MATERIAL": fake_result("NOT_SUPPORTED"),
        },
    )
    assert comparison.label.value == "FAMILY_SENSITIVE"
```

- [ ] **Step 3: Verify RED**

Run: `pytest tests/science/test_structural_comparison.py -q`
Expected: FAIL.

- [ ] **Step 4: Implement conservative label logic**

Rules:
- missing/invalid declared family -> no robustness label; raise validation error;
- valid families materially disagree -> `FAMILY_SENSITIVE`;
- families agree but identifiability gate is unresolved -> `IDENTIFICATION_LIMITED`;
- only one family executed -> `CONTROL_ONLY`;
- all valid declared families agree within preregistered directional/tolerance rule -> `ROBUST_ACROSS_FAMILIES`;
- insufficient evidence -> `UNKNOWN`.

Do not compute an overall model winner.

- [ ] **Step 5: Add qualification example and run suite**

`docs/qualification/STRUCTURAL_COMPARISON_V1.md` must demonstrate one synthetic robust case and one family-sensitive case using clearly fake data, labeled as test fixtures rather than empirical findings.

Run:
```bash
pytest tests/science tests/receipts -q
ruff check src/worldzero/science src/worldzero/receipts tests
mypy src/worldzero/science src/worldzero/receipts
```
Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add src/worldzero/science/comparison.py tests/science/test_structural_comparison.py docs/qualification/STRUCTURAL_COMPARISON_V1.md
git commit -m "feat: compare rival causal families without hiding structural uncertainty"
```

---

## Plan self-review

Coverage check:

- Evidence classes and UNKNOWN preservation: Tasks 1–2.
- Claim lineage/supersession: Task 2.
- Machine-readable causal topology and topology digest: Task 3.
- Mechanism kill tests/F7 admission: Task 4.
- Rival model-family composition: Task 5.
- Observation-model separation and holdout isolation: Task 6.
- Scientific-versus-execution receipt identity: Task 7.
- Family-sensitive/robust/identification-limited outputs: Task 8.
- Dataset admission remains in the original World Zero plan Task 3 and must execute before empirical calibration; this plan deliberately does not duplicate network/data-download work.
- Numerical stock-flow engine remains in the original plan Task 2 and can be developed before or alongside Tasks 1–3, but modern-sector calibration must wait until this spine is green.

No placeholders or unspecified implementation steps remain in this plan. Later sector-family plans should be written separately for F1/F2/F3/F4/F5/F6 rather than expanding this control-plane plan into a monolith.
