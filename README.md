# World Zero

World Zero is a research and modeling project to build a modern, transparent successor to the World3 system-dynamics model used in *The Limits to Growth*.

The goal is **not** to reproduce a predetermined collapse narrative, nor to assume that markets or technology automatically dissolve physical limits. The goal is to build a falsifiable world-systems comparison platform that can test competing explanations of overshoot, adaptation, substitution, technological learning, demographic transition, inequality, environmental degradation, institutional response, network fragility, regional heterogeneity and resilience with explicit evidence and uncertainty.

## Current status

`RESEARCH_AND_ARCHITECTURE_V2` — no executable World Zero model is claimed yet.

Current research branch: `work/world-zero-research-architecture-v1`

The architecture now requires a scientific comparison spine **before** modern-sector calibration. The first implementation frontier is therefore:

1. typed evidence/claim/provenance contracts;
2. hyperedge-capable causal topology;
3. topology-to-code implementation coverage;
4. mechanism admission/ablation gates;
5. rival causal families plus cheap predictive benchmarks;
6. frozen comparison protocols and holdout isolation;
7. exact scientific/execution receipts;
8. energy/trade accounting firewalls;
9. then a reproducible World3-compatible F0 control and the first modern rivals.

## Core principles

- Scenarios are conditional model trajectories, not prophecies.
- Historical fit does not uniquely prove causal structure.
- World Zero compares rival causal structures instead of privileging one architecture and tuning its parameters.
- Cheap non-causal predictive benchmarks are allowed to beat causal models; interpretability does not excuse poor holdout performance.
- Stocks, flows, delays, higher-order interactions and feedback loops remain first-class.
- Global aggregates are outputs of regional dynamics where practical, not substitutes for them.
- Physical, ecological, economic, demographic, distributional and institutional feedbacks are modeled separately before coupling.
- Technology, policy, fertility, prices and inequality must be explicitly endogenous, exogenous, intervention-controlled or absent; never silently more than one.
- Every empirical series carries source/provenance, upstream lineage where material, definition, units, geography, time coverage, revision vintage and uncertainty.
- Dataset admission is explicit; candidate data do not become model evidence merely because they were downloaded.
- Identifiability is checked before calibration credit is granted.
- Every new mechanism must have a serious kill test, holdout/invariant target and ablation expectation; complexity must earn its place.
- Declared causal topology and executable behavior must reconcile through implementation coverage and relation-level micro-tests.
- Confirmatory metrics, tolerances and subject sets are frozen before holdout execution.
- Every serious run is reproducible from exact source, topology, implementation coverage, data, parameter, region, scenario, partition, comparison protocol, solver and seed/environment receipts.
- Validation is claim-specific. No model receives an unqualified label of "validated."
- Missing evidence remains `UNKNOWN`; required fields never justify fabricated precision.
- Superseded hypotheses, schemas and failed model structures remain reproducible historical subjects with explicit disposition.
- Energy and regional physical trade are governed by reconciliation identities so resources are never created, destroyed or double-counted by accounting conventions.

## Research package

- `docs/research/LIMITS_TO_GROWTH_AND_WORLD3_BASELINE.md` — what the original work actually claimed, what World3 models, and what later comparisons do and do not establish.
- `docs/research/WORLD3_AND_WORLD_ZERO_HOSTILE_CHALLENGE_V1.md` — direct attack on World3 assumptions and the first World Zero architecture.
- `docs/research/RIVAL_MODEL_FAMILIES_V1.md` — F0–F7 causal-family contract.
- `docs/research/PREDICTIVE_BENCHMARKS_V1.md` — B0/B1 non-causal benchmark contract.
- `docs/research/WORLD_ZERO_2026_EXTENSION_MATRIX.md` — modern systems, adaptive mechanisms and hostile alternatives.
- `docs/research/CLAIM_AND_ASSUMPTION_LEDGER_V0.md` — seeded ledger separating observation, inference, dispute, hypothesis and unknowns.
- `docs/research/MECHANISM_ADMISSION_AND_ABLATION_V1.md` — gates a mechanism must survive before entering the minimal synthesis.
- `docs/research/ADVERSARIAL_EVIDENCE_UPDATE_2026-09-17.md` — evidence update on net energy, rebound, infrastructure queues, mineral constraints, networks, lock-in and compound risk.
- `docs/research/DATA_SOURCE_REGISTRY_V0.md` — candidate 2026 data sources and observables.
- `docs/research/VALIDATION_AND_FALSIFICATION_STRATEGY.md` — calibration, holdouts, sensitivity, shocks and hostile tests.
- `docs/research/CROSS_PROJECT_ENGINEERING_PATTERNS_2026-09-17.md` — generalized engineering patterns transferred after reviewing the owner’s repository portfolio, with private-project details deliberately excluded from this public repository.
- `docs/coordination/THIRTEEN_LANE_SYNTHESIS_2026-09-17.md` — first thirteen-role synthesis.
- `docs/coordination/THIRTEEN_LANE_HOSTILE_REVIEW_V2_2026-09-17.md` — second local thirteen-lens hostile review plus explicit boundary that it is not thirteen independent executions.

## Current architecture / plans

- `docs/superpowers/specs/2026-09-17-world-zero-model-design.md` — broad model architecture foundation.
- `docs/superpowers/specs/2026-09-17-world-zero-scientific-control-plane-design-v2.md` — current hostile-reviewed scientific comparison spine; supersedes its V1 predecessor.
- `docs/superpowers/plans/2026-09-17-world-zero-scientific-control-plane-v2.md` — current implementation predecessor plan; complete this spine before modern-sector calibration.
- `docs/superpowers/plans/2026-09-17-world-zero-model.md` — downstream broader sector/model plan; still useful after the scientific spine and F0 control are green.

## Machine-readable contracts

- `specs/CAUSAL_TOPOLOGY_V2.schema.json` — current higher-order causal topology contract.
- `specs/COMPARISON_PROTOCOL_V1.schema.json` — preregistered claim/subject/metric/decision-rule contract.
- `specs/IMPLEMENTATION_COVERAGE_V1.schema.json` — declared-topology to executable-binding coverage contract.
- `specs/SCHEMA_STATUS.md` — current/superseded schema status.

## Reference implementation boundary

[`cvanwynsberghe/pyworld3`](https://github.com/cvanwynsberghe/pyworld3) is a useful behavioral/reference implementation of World3. It is licensed under CeCILL 2.1. World Zero should initially use it as a reference subject and comparison target rather than blindly copying source code.

## Governance

Research and planning on this branch do not authorize merge, publication claims, deployment, or claims of behavioral/predictive qualification. Those are separate gates.
