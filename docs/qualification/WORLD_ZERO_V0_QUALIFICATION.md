# World Zero V0 Qualification

Date: 2026-09-18
Status: bounded source/numerical qualification; empirical qualification incomplete

## Exact subject

- Repository: `thebrazenbeard/world-zero`
- Source subject commit: `ad949bc42838759258628342eed3b81e9045363b`
- Source base: `2769401e5f8ebafbfa733c2d34eb287fe937222e`
- PR: #11
- Native 2026 scenario status: `DATA_BINDING_REQUIRED`
- World3 control fixture SHA-256: `31d3f493e942e3f0eadf8828bf51ec968745e19b12399dc382138e89a67a2d68`

This report qualifies only claims directly supported by evidence bound to the exact source subject above.
It does not state or imply that World Zero is historically validated, predictively validated, or a forecast.

## Exact-source execution evidence

Local exact-head gate on Windows:
- pytest: **227/227 PASS**
- Ruff: **PASS**
- mypy: **PASS** across 62 source/tool files
- `uv lock --check`: **PASS**
- Windows offline wheelhouse manifest: **PASS**
- Linux offline wheelhouse manifest: **PASS**
- `git diff --check`: **PASS**

GitHub exact-head evidence:
- ordinary PR CI run `35331955901`: **PASS**, head `ad949bc42838759258628342eed3b81e9045363b`
- offline qualification run `35331955927`: **PASS**
- `qualify-linux`: **PASS**, literal head `ad949bc42838759258628342eed3b81e9045363b`
- `qualify-windows`: **PASS**, literal head `ad949bc42838759258628342eed3b81e9045363b`

## Qualification ladder

| State | Result | Exact evidence / boundary |
| --- | --- | --- |
| `SOURCE_REPRODUCIBLE` | **PASS** | Exact source passes local, ordinary CI, and index-disabled Linux/Windows reconstruction gates. |
| `NUMERICAL_BASELINE_PASS` | **PASS** | Core solver/conservation tests, integrated native trajectory tests, and frozen World3 control-artifact regression mechanics pass. This does **not** mean native V0 reproduces World3 or historical reality. |
| `HISTORICAL_CALIBRATION_PASS` | **UNKNOWN** | No frozen admitted historical dataset + parameter-set execution exists for this subject. |
| `TEMPORAL_HOLDOUT_PASS` | **UNKNOWN** | Holdout firewall exists; no frozen temporal-holdout execution exists. |
| `REGIONAL_HOLDOUT_PASS` | **UNKNOWN** | Regional mechanics exist; no frozen regional-holdout execution exists. |
| `VARIABLE_HOLDOUT_PASS` | **UNKNOWN** | Multi-metric tooling exists; no frozen variable-holdout execution exists. |
| `STRUCTURAL_FALSIFICATION_PASS` | **UNKNOWN** | F1/F2/F3/F5/F6/F11 oracles are executable and tested, but have not all been run against this integrated subject with frozen empirical bindings. |
| `UNCERTAINTY_CHARACTERIZED` | **UNKNOWN** | Deterministic Morris screening exists; no frozen V0 parameter ensemble/screen has been executed. |
| `SCENARIO_EXPERIMENT_READY` | **FAIL** | `scenarios/2026_baseline.yaml` intentionally remains `DATA_BINDING_REQUIRED`; executable status requires frozen data and parameter-set bindings. |

No ladder state implies the next one.

## What the exact source subject does establish

The source contains a runnable regional stock-flow backbone with:
- cohort demography and migration;
- productive/service capital and income allocation;
- dynamic fossil, low-carbon, grid and storage capacity;
- material extraction, use, waste, recycling and explicit losses;
- energy/material constraints on output;
- carbon/temperature feedback into output and food;
- soil degradation/recovery and water stress;
- conservative physical food trade;
- bounded institutional response and explicit policy delay;
- frozen calibration/holdout/falsification/sensitivity control surfaces.

The integrated V0 runner can execute synthetic/mechanical scenarios whose parameter and initial-condition inputs are explicitly supplied.
That capability is software/scenario machinery, not evidence that any supplied synthetic scenario represents 2026 reality.

## World3 control boundary

The World3 artifact remains an **external control subject**.
The repository freezes its trajectory identity and verifies the adapter's exact-source binding behavior.
World Zero does not inherit World3 causal validity from similarity to, or compatibility with, that control.
The native V0 source is not claimed here to reproduce the World3 standard run.

## Structural-test boundary

Executable hostile controls currently cover at least:
- F1 aggregate-fit trap;
- F2 correlated-evidence laundering;
- F3 parameter-swap / identifiability;
- F5 solver/timestep convergence oracle;
- F6 technology-learning saturation;
- F11 physical trade fragmentation/conservation;
- explicit policy-delay behavior;
- mass/stock conservation and missing-sector fail-closed cases.

Passing the oracle unit tests proves the falsification machinery behaves as specified.
It does not convert those oracle tests into a subject-level `STRUCTURAL_FALSIFICATION_PASS`.
That rung requires a frozen execution packet against the exact model/data/parameter/scenario subject.

## Required next evidence

To advance empirical/scenario qualification:
1. admit and freeze source datasets with provenance, revision/vintage, units and transforms;
2. freeze the calibration/temporal/regional/variable/shock partition set before fitting;
3. freeze bounded parameter definitions and an initial parameter-set subject;
4. execute calibration only against calibration IDs;
5. execute untouched holdouts and the structural suite;
6. run Morris screening on the frozen parameter bounds and report dominant uncertainty;
7. issue immutable run receipts binding source commit, data, parameters, scenario, solver and timestep;
8. only then promote the 2026 scenario manifest to `EXECUTABLE` if its data/parameter contracts are satisfied.

## Claim language

Supported:
> Commit `ad949bc42838759258628342eed3b81e9045363b` is source-reproducible and passes its bounded numerical/software baseline gates on qualified Windows and Linux reconstruction paths.

Not supported:
> World Zero V0 is historically validated, predictively validated, calibrated to 2026, or known to forecast future global outcomes accurately.

Scenario readiness is not future predictive validation.
