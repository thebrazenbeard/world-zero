# World Zero Scientific Comparison Spine Design V2

Date: 2026-09-17
Status: current design candidate; supersedes `2026-09-17-world-zero-scientific-control-plane-design.md`

## Why V2 exists

The first scientific-spine design correctly separated evidence, topology, families and execution, but a second hostile review exposed four material weaknesses:

1. pairwise causal edges can misrepresent genuinely higher-order relations;
2. causal-family-only comparison can privilege the system-dynamics worldview;
3. declared topology can drift from executable code;
4. structural-robustness labels can be gamed if metrics/tolerances are chosen after results are seen.

V2 corrects those weaknesses before implementation.

## Core objective

World Zero must be able to compare competing causal explanations **and** cheaper non-causal predictive benchmarks while preserving exact evidence, topology, implementation and execution identity.

A qualification-grade result must make it possible to answer:

- what was observed versus inferred;
- what causal structure was declared;
- what code implemented each declared relation;
- what data/partitions were used;
- what rival causal families and predictive benchmarks were preregistered;
- what metric/tolerance rules were frozen before execution;
- what mechanism kill tests and ablations were run;
- whether a result is robust, family-sensitive, benchmark-inferior or identification-limited.

## Architectural layers

### 1. Evidence / claim layer

Maintains append-oriented claims with evidence classes:

`OBSERVED`, `DERIVED`, `INFERRED`, `HYPOTHESIS`, `DISPUTED`, `UNKNOWN`, `SUPERSEDED`.

Claim revisions never silently overwrite prior historical state.

### 2. Dataset / observation layer

Maintains admitted immutable data cuts and observation mappings.

Observation records additionally carry `upstream_lineage_id` when multiple derived datasets share a common source. This allows validation to distinguish genuinely independent evidence from correlated transformations of one upstream series.

Where materially important, observation mappings may carry covariance-group metadata rather than assuming independent measurement error.

### 3. Causal topology layer

Current schema: `specs/CAUSAL_TOPOLOGY_V2.schema.json`.

V2 relations are hyperedge-compatible:

`inputs[] -> relation -> outputs[]`

A pairwise edge is the one-input/one-output special case.

Each relation declares:

- relation type;
- functional-form class;
- polarity/sign behavior;
- lag/delay model;
- spatial scope;
- evidence class;
- uncertainty class;
- source/claim bindings;
- kill-test IDs;
- rival relation IDs;
- optional implementation binding.

Topology content does **not** contain the Git commit that contains itself. Exact source binding is external through family/coverage/run receipts.

### 4. Implementation-coverage layer

Current schema: `specs/IMPLEMENTATION_COVERAGE_V1.schema.json`.

A declared topology is not considered executable merely because code exists.

Compilation/runtime registration produces an implementation coverage artifact that maps each active node/relation to:

- module;
- symbol;
- behavioral contract ID where applicable;
- micro-test IDs;
- binding status.

Qualification-grade coverage requires no undeclared runtime relations and no missing declared active relations.

This does not mathematically prove source code semantics, so relation-level limiting-case/micro-tests are still required.

### 5. Causal model-family layer

Causal families remain:

- F0 World3-compatible control;
- F1 market-adaptive;
- F2 endogenous innovation;
- F3 net-energy/material bottleneck;
- F4 institutional fragility;
- F5 resilient regional network;
- F6 compound-risk cascade;
- F7 minimal adaptive synthesis.

F7 remains downstream: it is composed only from mechanisms that survive admission/ablation gates.

### 6. Predictive benchmark layer

Current design: `docs/research/PREDICTIVE_BENCHMARKS_V1.md`.

Benchmarks are deliberately outside the causal namespace:

- `B0_PERSISTENCE_TREND`;
- `B1_REDUCED_FORM_EMPIRICAL`.

They receive no causal interpretation.

Their purpose is to answer a hostile question: does the expensive causal machinery actually improve out-of-sample prediction or intervention validity over something cheaper?

### 7. Mechanism-admission layer

Current design: `docs/research/MECHANISM_ADMISSION_AND_ABLATION_V1.md`.

A mechanism can live in a rival family without earning F7 admission.

F7 admission requires:

- semantic/boundary clarity;
- at least weak identifiability unless needed for a hard invariant;
- preregistered kill test;
- holdout or invariant value;
- ablation value;
- structural-rival analysis;
- proportionate complexity;
- numerical integrity;
- no unresolved negative transfer.

### 8. Comparison-preregistration layer

Current schema: `specs/COMPARISON_PROTOCOL_V1.schema.json`.

A comparison protocol is frozen before qualification-grade execution and binds:

- claim ID;
- causal families/benchmarks;
- calibration partition;
- holdout partitions;
- metrics;
- direction/tolerance rules;
- benchmark margins where used;
- missing-subject policy;
- identifiability gate;
- whether the comparison is confirmatory or exploratory.

A post-hoc comparison can still be useful, but remains explicitly exploratory.

### 9. Scientific subject identity

A scientific subject binds:

- Git tree/commit;
- topology digest;
- model-family or benchmark manifest digest;
- implementation-coverage digest for causal subjects;
- dataset-manifest-set digest;
- parameter/hyperparameter digest;
- region-set digest;
- scenario/intervention digest;
- observation-map digest;
- calibration/holdout partition IDs;
- comparison-protocol digest where the run participates in a frozen comparison.

### 10. Execution identity

Execution identity remains separate:

- solver name/version;
- timestep/tolerances;
- random seed/ensemble member;
- numerical environment fingerprint.

Changing solver changes execution identity, not causal topology identity.

## Accounting firewalls exposed by hostile review

### Energy accounting

F3 must define one reconciliation identity so energy-sector own-use/transition energy is counted exactly once.

At minimum distinguish:

- gross energy produced;
- conversion/distribution losses;
- energy-sector own use;
- final energy;
- useful energy;
- energy investment embodied in new energy infrastructure.

Embodied/transition energy cannot also appear as an untracked second subtraction through industrial demand.

### Regional trade accounting

F5 must choose and declare production versus consumption accounting for each output metric.

Every physical trade flow has:

- one origin debit;
- one destination credit;
- one transport-loss term where applicable.

Global conservation must survive arbitrary rerouting.

Embodied water/energy/material footprint metrics are diagnostics derived from trade, not additional physical stocks.

## Benchmark fairness

B0/B1 use the same admitted observations and frozen partitions as causal families for ordinary historical prediction.

They are exempt only from tests that inherently require causal/physical intervention semantics.

A causal family does not receive a pass merely because a benchmark cannot answer a novel intervention question. It must still demonstrate invariant-valid counterfactual behavior and/or better predictive performance in its claimed domain.

## Complexity handling

V2 still avoids one universal model score.

Instead each comparison reports:

- predictive metrics;
- number of dynamic states;
- calibrated parameter count;
- latent-variable count;
- external scenario-input count;
- runtime/ensemble cost;
- identifiability class;
- mechanism count.

Reviewers compare models on a Pareto/claim-specific basis. Statistical submodels may additionally report AIC/BIC or other suitable complexity metrics where mathematically meaningful, but those are not imposed on the whole system-dynamics model.

## Structural result vocabulary

Causal-family result labels:

- `ROBUST_ACROSS_FAMILIES`
- `FAMILY_SENSITIVE`
- `IDENTIFICATION_LIMITED`
- `CONTROL_ONLY`
- `UNKNOWN`

Benchmark comparison labels:

- `OUTPERFORMS_B0_ON_DECLARED_HOLDOUT`
- `OUTPERFORMS_B1_ON_DECLARED_HOLDOUT`
- `NO_PREDICTIVE_GAIN_OVER_BENCHMARK`
- `BENCHMARK_SUPERIOR_ON_HISTORICAL_HOLDOUT`
- `INTERVENTION_COMPARISON_NOT_APPLICABLE_TO_BENCHMARK`

No label implies universal predictive truth.

## Fail-closed conditions

Reject qualification-grade execution when:

- a V1 pairwise topology is used where V2 is required;
- topology inputs/outputs reference missing nodes;
- implementation coverage has missing or undeclared active relations;
- comparison protocol was not frozen before confirmatory execution;
- metric/tolerance was changed after inspecting holdout results;
- a claimed independent evidence source shares upstream lineage that the comparison failed to disclose;
- calibration/holdout partitions overlap;
- F7 contains a mechanism without required admission state;
- energy or regional trade conservation cannot reconcile;
- benchmark hyperparameters were selected using final holdout data;
- structural robustness is declared without running the entire frozen subject set.

## Updated repository targets

```text
src/worldzero/science/
  types.py
  canonical.py
  claims.py
  topology.py
  implementation_coverage.py
  mechanisms.py
  families.py
  benchmarks.py
  observations.py
  partitions.py
  comparison_protocol.py
  comparison.py

src/worldzero/accounting/
  energy.py
  trade.py

src/worldzero/receipts/
  run_receipt.py

specs/
  CAUSAL_TOPOLOGY_V2.schema.json
  COMPARISON_PROTOCOL_V1.schema.json
  IMPLEMENTATION_COVERAGE_V1.schema.json
  CLAIM_RECORD_V1.schema.json
  MECHANISM_ADMISSION_V1.schema.json
  MODEL_FAMILY_V1.schema.json
  RUN_RECEIPT_V1.schema.json
```

## Updated implementation ordering

1. typed scientific vocabulary and canonical digest primitives;
2. claim/data lineage primitives;
3. topology V2 + implementation coverage;
4. mechanism admission;
5. causal-family + benchmark manifests;
6. observation/partition leakage guards;
7. frozen comparison protocol;
8. exact subject/execution receipts;
9. structural comparison;
10. energy/trade accounting firewalls;
11. World3 F0 control;
12. F1/F3 first rivals;
13. remaining rivals only as evidence/kill tests justify them;
14. F7 only after mechanism admission evidence exists.

## V2 success criterion

Before modern sector calibration begins, World Zero must demonstrate on synthetic fixtures that:

1. a higher-order causal relation can be represented without false pairwise decomposition;
2. declared topology and executable bindings reconcile exactly;
3. B0/B1 and at least two causal families can share a frozen comparison protocol;
4. holdout leakage and post-hoc tolerance changes are rejected;
5. structural disagreement is labeled family-sensitive rather than averaged away;
6. an intentionally overcomplex causal family can lose to a simple benchmark without the framework treating that as an error;
7. changing numerical solver changes execution identity while preserving scientific topology identity.
