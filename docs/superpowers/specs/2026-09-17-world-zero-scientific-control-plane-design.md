# World Zero Scientific Comparison Spine Design

Date: 2026-09-17
Status: approved continuation design; implementation not yet started

## Purpose

World Zero must be able to test competing causal explanations without letting the simulation code itself become the uninspectable source of scientific meaning.

The scientific comparison spine is a solver-independent control plane for:

- evidence and claim classes;
- dataset admission/currentness;
- causal topology;
- rival model-family composition;
- mechanism admission and kill tests;
- exact run identity;
- holdout isolation;
- structural comparison and qualification labels.

The sector equations remain important, but they are consumers of this scientific state rather than the sole place where assumptions live.

## Design objective

A reviewer should be able to answer, without reverse-engineering Python equations:

1. What causal structure did this model run?
2. Which relations were observed, inferred, disputed or hypothetical?
3. Which mechanisms were absent, endogenous, exogenous or intervention-controlled?
4. Which exact data and parameter cuts were used?
5. Which rival structures were tested?
6. What would have falsified an admitted mechanism?
7. Which result is robust across families and which is family-sensitive?
8. Can the same scientific subject be replayed with another numerical solver?

If those questions cannot be answered from durable machine-readable artifacts and receipts, the run is not qualification-grade.

## Architectural boundary

The spine owns **scientific identity and comparison semantics**.

It does not own:

- numerical integration internals;
- sector-specific equations;
- data downloading/network clients;
- plotting/UI;
- normative policy optimization;
- a universal ranking of rival models.

Sector code may implement equations, but it must bind to declared topology/manifest objects. A solver may integrate the model, but it does not define what causal claim the model represents.

## Component 1 — evidence and claim registry

Canonical evidence classes:

- `OBSERVED`
- `DERIVED`
- `INFERRED`
- `HYPOTHESIS`
- `DISPUTED`
- `UNKNOWN`
- `SUPERSEDED`

Each claim record includes:

- stable claim ID;
- proposition;
- evidence class;
- source references;
- scope;
- rival interpretations;
- model obligation;
- downgrade/kill condition;
- supersedes/superseded-by links.

The registry is append-oriented. Updating a claim produces a new revision/event; old state remains reproducible.

## Component 2 — dataset admission registry

Dataset lifecycle:

`CANDIDATE -> SOURCE_VERIFIED -> RIGHTS_TERMS_CHECKED -> SCHEMA_MAPPED -> QUALITY_CHECKED -> ADMITTED`

Dataset manifests bind:

- provider/product/release;
- retrieval date;
- source locator;
- license/terms state;
- geography;
- time coverage/frequency;
- units/definitions;
- uncertainty;
- missing-data treatment;
- content digest;
- transformation code digest;
- supersession/currentness status.

Sector code never fetches network data. Runs consume admitted immutable data cuts.

## Component 3 — causal topology registry

`specs/CAUSAL_TOPOLOGY_V1.schema.json` is the normative V1 shape.

The topology registry represents:

- stocks;
- flows;
- auxiliary variables;
- observations;
- prices;
- policy states;
- shocks;
- threshold states;
- network states;
- technology states;
- causal/constraint/substitution/damage/transmission relations;
- polarity;
- lag model;
- spatial scope;
- control mode;
- evidence class;
- uncertainty;
- source and claim references;
- rival relation IDs;
- kill-test IDs.

A topology receives a deterministic digest after canonical serialization. Run receipts bind that digest.

## Component 4 — model-family manifest

The first family registry contains:

- `F0_WORLD3_CONTROL`
- `F1_MARKET_ADAPTIVE`
- `F2_ENDOGENOUS_INNOVATION`
- `F3_NET_ENERGY_MATERIAL`
- `F4_INSTITUTIONAL_FRAGILITY`
- `F5_RESILIENT_REGIONAL`
- `F6_COMPOUND_RISK`
- `F7_MINIMAL_ADAPTIVE_SYNTHESIS`

A family manifest defines:

- topology ID/digest;
- enabled sector implementations;
- required/forbidden mechanisms;
- parameter schema version;
- observation compatibility;
- region-set compatibility;
- required hostile controls;
- qualification status.

Families share infrastructure but not necessarily causal structure.

## Component 5 — mechanism admission registry

Each mechanism has a durable packet implementing `MECHANISM_ADMISSION_AND_ABLATION_V1.md`.

Required state includes:

- semantic/boundary definition;
- evidence class;
- source/claim bindings;
- identifiability class;
- null/rival mechanism;
- motivating residual;
- preregistered kill test;
- holdout target;
- ablation expectation;
- complexity budget;
- disposition.

The runtime must be able to refuse F7 composition if an included mechanism lacks the required admission state.

## Component 6 — observation model

Model state and empirical observation are separate.

An observation mapping declares:

- latent/source model variable;
- empirical series ID;
- transformation/aggregation;
- unit conversion;
- spatial mapping;
- temporal alignment;
- measurement uncertainty;
- observation class.

A directly measured population series and an inferred ecosystem-function index are therefore not treated as equivalent evidence merely because both appear in a loss function.

## Component 7 — scenario and intervention contract

Control modes:

- `ENDOGENOUS`
- `EXOGENOUS_TRAJECTORY`
- `INTERVENTION_CONTROLLED`
- `ABSENT`

A variable or relation cannot silently change mode within a comparison. Scenario manifests must bind intervention timing, ramp, target, value/function and family compatibility.

## Component 8 — exact run receipt

A serious run receipt binds at minimum:

- Git commit/tree;
- topology digest;
- family manifest digest;
- dataset-manifest set digest;
- parameter-set digest;
- region-set digest;
- scenario/intervention digest;
- observation-map digest;
- solver/solver version;
- timestep/tolerances;
- random seed/ensemble ID;
- time range;
- calibration partition ID;
- validation/holdout partition ID;
- produced metric/artifact digests.

The receipt identifies the subject. It is not itself evidence that the subject passed qualification.

## Component 9 — validation and structural comparison

Comparison is multi-dimensional. No universal scalar ranking is required.

Required metric families include:

- temporal holdout error;
- regional holdout error;
- variable holdout error;
- direction-of-change;
- turning-point timing;
- conservation/invariant violations;
- residual structure/autocorrelation;
- uncertainty coverage;
- shock/recovery behavior;
- numerical convergence;
- sensitivity concentration;
- identifiability diagnostics.

Structural result labels:

- `ROBUST_ACROSS_FAMILIES`
- `FAMILY_SENSITIVE`
- `IDENTIFICATION_LIMITED`
- `CONTROL_ONLY`
- `UNKNOWN`

These labels attach to an exact claim, metric bundle, family set and evidence cut.

## Data flow

```text
source material
   -> source/claim ledger
   -> dataset candidate/admission
   -> observation mappings
   -> causal topology
   -> rival family manifests
   -> parameter/scenario manifests
   -> sector implementations
   -> solver
   -> exact run receipt
   -> metrics/holdouts/kill tests
   -> structural comparison
   -> scoped qualification label
```

No arrow may skip provenance by turning a retrieved source directly into an unquestioned equation constant.

## Failure behavior

Fail closed when:

- topology references a missing node/claim/kill test;
- units are incompatible;
- an admitted run uses a non-admitted dataset cut;
- a family includes a forbidden mechanism;
- F7 includes a mechanism without required admission gates;
- holdout observations leak into calibration;
- run receipt cannot bind exact inputs;
- topology digest does not match the compiled model subject;
- the same variable is simultaneously endogenous and externally prescribed;
- conservation identities fail beyond declared tolerance;
- non-finite state appears;
- a comparison attempts to label family robustness without actually executing the declared rival set.

Unknown scientific state is not a runtime error by itself. It must remain `UNKNOWN` or `IDENTIFICATION_LIMITED` rather than being filled with a default value.

## Repository structure

Implementation should add focused modules rather than one large governance file:

```text
src/worldzero/science/
  evidence.py
  claims.py
  topology.py
  families.py
  mechanisms.py
  observations.py
  comparison.py

src/worldzero/data/
  manifests.py
  admission.py

src/worldzero/scenarios/
  schema.py

src/worldzero/receipts/
  run_receipt.py

specs/
  CAUSAL_TOPOLOGY_V1.schema.json
  MODEL_FAMILY_V1.schema.json
  MECHANISM_ADMISSION_V1.schema.json
  RUN_RECEIPT_V1.schema.json

tests/science/
  test_claim_registry.py
  test_topology.py
  test_family_manifest.py
  test_mechanism_admission.py
  test_structural_comparison.py
```

## Testing strategy

Tests begin with invalid scientific states, not happy-path simulation output.

High-value negative tests:

- dangling topology edge;
- unknown evidence-class value;
- `UNKNOWN` parameter silently coerced to zero;
- topology digest changes when causal relation changes;
- topology digest does not change for irrelevant formatting/order after canonicalization;
- family manifest enables a forbidden relation;
- F7 admits a mechanism with no kill test;
- holdout ID appears in calibration partition;
- identical run inputs generate identical receipt identity;
- solver change creates a new execution receipt but preserves topology identity;
- rival-family result incorrectly labeled robust when one declared family was not run;
- a globally conserved quantity changes through regional trade/migration;
- observation transformation loses source lineage.

## Relationship to the original implementation plan

The original `2026-09-17-world-zero-model.md` sector plan remains useful but is no longer the first implementation frontier.

The scientific comparison spine must be implemented before modern sector calibration. Specifically:

1. typed core/numerical primitives may proceed;
2. scientific spine and provenance contracts come next;
3. World3-compatible F0 control is frozen;
4. regional/sector primitives are implemented;
5. F1–F6 mechanisms are added as separable rival structures;
6. only evidence-surviving mechanisms may compose F7.

This ordering prevents late governance from being bolted onto an already tuned model.

## Non-goals for V1

- no full Bayesian causal-discovery engine;
- no automatic truth inference from source counts;
- no automatic model-family winner;
- no unrestricted self-modifying topology;
- no optimizer that silently rewrites causal structure;
- no requirement for a full global supply-chain graph in V0;
- no claim that every causal relation is statistically identifiable.

## Success criterion

The scientific comparison spine V1 succeeds when two materially different causal families can be built from explicit manifests, run against the same admitted evidence cut, replayed from receipts, and compared without losing structural uncertainty or confusing fit with causal validation.
