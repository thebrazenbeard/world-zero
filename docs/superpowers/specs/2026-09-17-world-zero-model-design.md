# World Zero Model Design

Date: 2026-09-17
Status: architecture specification for research implementation

## 1. Purpose

World Zero is a transparent, falsifiable, modular world-systems dynamics model inspired by World3 but modernized for 2026 evidence and feedbacks.

It is designed to answer conditional questions such as:

- Under what combinations of demographic, technological, ecological, economic and institutional assumptions do global/regional systems stabilize, overshoot or decline?
- Which constraints dominate different scenarios and periods?
- Which apparent limits are physical, ecological, infrastructural, economic, distributional or institutional?
- How do adaptation, substitution, recycling and technological learning change trajectories?
- How sensitive are conclusions to uncertain structure and parameters?

It is not designed to produce an oracle-like single prediction of civilization's future.

## 2. Architectural approach

Use a coupled stock-flow architecture with explicit delays and typed inter-module exchanges. Each module owns its internal state and exports a small set of observables/flows. Regional modules operate on a versioned macroregion set. Truly global physical states, such as the reduced-form atmospheric climate state, are shared explicitly.

The observation/calibration layer is separate from the simulation layer. Model state is not assumed directly measurable.

### 2.1 Proposed Python package structure

```text
src/worldzero/
  __init__.py
  core/
    clock.py
    units.py
    stocks.py
    delays.py
    solver.py
    interfaces.py
    invariants.py
  regions/
    definitions.py
    coupling.py
  sectors/
    demography.py
    production.py
    distribution.py
    energy.py
    materials.py
    food_land.py
    water.py
    climate.py
    biosphere.py
    technology.py
    institutions.py
    trade.py
  data/
    manifests.py
    observations.py
    transforms.py
    registry.py
  scenarios/
    schema.py
    loader.py
  calibration/
    objective.py
    parameters.py
  validation/
    metrics.py
    holdouts.py
    falsification.py
    sensitivity.py
  receipts/
    run_receipt.py
  cli.py

tests/
  baseline/
  core/
  sectors/
  integration/
  validation/
```

V0 does not need every sector file to contain a full model. Interfaces are established early; modules are activated in stages.

## 3. Core simulation contract

### 3.1 Time

- Historical reference start: 1900 where source data/model initialization permit.
- Default scenario horizon: 2100.
- Internal default timestep target: 0.25 year, subject to convergence testing.
- Solver must be replaceable; numerical conclusions may not depend on an undocumented solver choice.

### 3.2 Stocks and flows

A stock has:

- stable ID;
- owner module;
- units;
- region/global scope;
- non-negativity or other domain constraints;
- initialization source/rule;
- incoming/outgoing flows;
- conservation semantics where applicable.

A flow has:

- stable ID;
- source/target stocks where physical accounting applies;
- units per time;
- equation/function ID;
- declared dependencies;
- sign convention;
- delay if any.

### 3.3 Module interface

Conceptual interface:

```python
class Sector(Protocol):
    sector_id: str

    def initialize(self, context: InitContext) -> SectorState: ...
    def exports(self, state: SectorState) -> Mapping[str, Quantity]: ...
    def derivatives(self, state: SectorState, inputs: SectorInputs, t: float) -> FlowSet: ...
    def invariants(self, state: SectorState, inputs: SectorInputs) -> Sequence[InvariantResult]: ...
```

Exact code can evolve during implementation, but responsibilities must remain separated.

## 4. Region model

Start with 8-12 macroregions chosen by data availability and structural differences. Region definitions are data-controlled and versioned; model code must not scatter hard-coded region names.

Regional state includes population, production/capital, food/land/water, energy mix, material demand, income/distribution and institutional proxies.

Global state includes at least reduced-form atmospheric carbon/climate variables and any globally mixed pollutant selected for V0.

Trade/coupling moves physical commodities/services between regions and must conserve physical quantities subject to documented losses.

## 5. V0 active modules

### 5.1 World3 compatibility baseline

Before modernization, implement or wrap a clean-room/reference World3-compatible behavioral subject and freeze trajectory fixtures for headline variables. PyWorld3 may be used as an external behavioral reference under its CeCILL-2.1 license; copying code is not required and should not occur casually.

### 5.2 Demography

V0 state:

- age cohorts by region;
- births/deaths;
- fertility/desired fertility proxy;
- life expectancy/health proxy;
- net migration between regions.

Inputs/feedbacks: food access, pollution/climate health burden, income/public services, education proxy, urbanization/dependency.

### 5.3 Production/capital

V0 state:

- productive capital;
- service/public capital;
- infrastructure quality/depreciation.

Output uses capital, labour, energy services and material inputs. Environmental damages can raise depreciation/lower productivity. No unconstrained Cobb-Douglas assumption is required; alternative production structures belong to structural uncertainty tests.

### 5.4 Distribution

V0 should use a compact representation rather than a full microsimulation:

- labour income share or worker/owner income split;
- disposable income per broad group;
- access/public-service proxy.

Distribution feeds consumption composition, food/energy access, health/fertility and institutional response capacity.

### 5.5 Energy

V0 distinguishes:

- fossil-fuel energy;
- low-carbon electricity capacity;
- storage/grid enabling capacity;
- final useful energy demand;
- electrification fraction.

Technology learning applies to selected clean technologies using cumulative deployment, with configurable learning-rate saturation and supply/integration constraints.

### 5.6 Materials

V0 uses a compact critical-material basket plus fossil resources, not dozens of minerals.

Required mechanisms:

- virgin extraction;
- depletion/extraction intensity;
- processing capacity;
- in-use stock;
- recycling/secondary supply;
- substitution/efficiency response;
- concentration/trade disruption parameter.

Later versions can split the basket if holdouts or policy questions require material-specific behavior.

### 5.7 Food/land/water/soil

V0 state:

- productive agricultural land;
- soil/productivity condition;
- irrigation/water availability or stress;
- nutrient/fertilizer input;
- food production and food-access outcome.

Food production depends on land, soil, water, nutrients, energy, capital/technology and climate. Food access additionally depends on income/prices/trade.

### 5.8 Climate

Use a reduced-form climate/carbon module suitable for century-scale scenario coupling, not a general circulation model.

Minimum:

- emissions;
- atmospheric carbon/forcing proxy;
- temperature anomaly;
- damage/hazard interfaces to agriculture, health, productivity, water and capital depreciation.

Alternative damage formulations are structural-uncertainty subjects.

### 5.9 Institutions

V0 institutional state should be deliberately small:

- response capacity;
- policy implementation delay;
- social tension/trust proxy if evidence supports calibration.

This module modulates deployment/adaptation/policy implementation. It must not decide which policies are morally correct or deterministically infer conflict.

## 6. Deferred modules after V0

Unless required by failed holdouts, defer detailed:

- explicit nitrogen/phosphorus cycles;
- multi-index biodiversity dynamics;
- ocean acidification/fisheries detail;
- detailed novel-entity chemistry/plastics;
- full monetary/financial sector;
- endogenous armed-conflict model;
- AI-driven productivity model;
- high-resolution national/within-country distributions.

Interfaces should allow later addition without contaminating V0 scope.

## 7. Scenario semantics

A scenario is a versioned declaration of interventions and exogenous assumptions. It may override or constrain designated variables but cannot silently change equation definitions.

Scenario schema should identify:

- scenario ID/version;
- model commit compatibility;
- exogenous trajectories;
- policy interventions;
- parameter overrides;
- intervention start/end and ramp/delay;
- stochastic assumptions/seed policy.

Key requirement: variables such as fertility, technology cost, carbon price, redistribution or policy capacity must be marked `ENDOGENOUS`, `EXOGENOUS_TRAJECTORY`, or `INTERVENTION_CONTROLLED` for each scenario.

## 8. Data and observation architecture

Data ingestion produces immutable raw artifacts and normalized observations with manifests. Sector code never reaches out to live APIs.

Observation mapping converts latent model variables to comparable measured variables. Example: a latent soil-condition stock may map to multiple observed proxies; the mapping and uncertainty are explicit.

Calibration operates against observation IDs, not arbitrary dataframe columns.

## 9. Calibration

Do not calibrate the entire model simultaneously at first.

Order:

1. reproduce baseline;
2. calibrate/qualify modules individually against relevant history;
3. couple two/three modules and test interface behavior;
4. conduct staged joint calibration with parameter bounds/prior information;
5. preserve holdouts throughout.

Use parameter constraints derived from physical units/literature/data. If radically different parameter sets fit equally well, report non-identifiability.

## 10. Validation and falsification

The authoritative validation strategy is `docs/research/VALIDATION_AND_FALSIFICATION_STRATEGY.md`.

The implementation must support:

- temporal/regional/variable holdouts;
- solver/timestep convergence;
- stock-flow conservation;
- aggregate-vs-regional checks;
- parameter/structural sensitivity;
- stochastic shock ensembles;
- module ablations;
- World3 baseline comparison.

## 11. Reproducibility

Each simulation run emits a `WORLD_ZERO_RUN_RECEIPT_V1` containing exact source, data-manifest, parameter, scenario, region-set, solver/timestep and seed identities plus result/metric artifact references.

No chart is evidence without a receipt.

## 12. Error handling

Fail closed on:

- missing dataset manifests;
- unit mismatch;
- duplicate stock IDs;
- physically impossible negative stocks unless the variable explicitly permits negatives;
- non-finite derivatives/states;
- unbound scenario parameters;
- incompatible model/data/scenario schema versions;
- violated conservation/invariant checks above configured tolerance.

Warnings rather than hard failure may be appropriate for empirical coverage gaps, but they must propagate to receipts/qualification outputs.

## 13. Testing

Three layers:

1. **Unit:** equations, delays, units, transformations, manifest validation.
2. **Sector:** conservation, known limiting cases, monotonicity/sign tests, historical bounded calibration.
3. **Integrated:** baseline reproduction, coupling invariants, holdouts, shocks, sensitivity, scenario receipts.

Tests should include intentionally wrong models/data to prove the validation harness can fail.

## 14. Success criteria for V0

V0 is `SCENARIO_EXPERIMENT_READY` only when:

- World3 compatibility fixtures are reproducible;
- active World Zero modules have typed stock/flow definitions and invariant tests;
- at least one reproducible open-data historical bundle is frozen;
- calibration and at least temporal + variable/regional holdouts are runnable;
- numerical convergence and conservation tests pass;
- sensitivity identifies dominant uncertainty;
- run receipts reproduce identical deterministic runs;
- known hostile fixtures fail for the intended reasons;
- documentation distinguishes observed, calibrated, inferred and scenario-controlled quantities.

This does not mean V0 predicts the future correctly. It means the model is technically coherent enough to support transparent scenario experiments.

## 15. Non-goals

V0 will not:

- forecast exact collapse dates;
- claim political inevitability;
- replace specialized climate, demographic, biodiversity or macroeconomic models;
- optimize a single ideological welfare function;
- infer causal truth solely from curve matching;
- hide uncertainty behind one composite score;
- implement every 2026 metric simply because data exist.
