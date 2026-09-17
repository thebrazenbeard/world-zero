# World Zero Model Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible, modular World Zero V0 that reproduces a World3-compatible baseline, ingests provenance-bound open data, implements a bounded set of 2026 feedback modules, and supports falsifiable scenario experiments.

**Architecture:** Python 3.12 package-first system-dynamics engine with typed sector interfaces, versioned regional coupling, immutable dataset/scenario manifests, staged calibration/holdouts and deterministic run receipts. Modern modules are added only after the World3 control subject and validation harness are green.

**Tech Stack:** Python 3.12, NumPy, SciPy, pandas or Polars (choose one during Task 1 and pin it), Pydantic v2 for manifests/schemas, Pint for units, pytest, Ruff, mypy, PyYAML, matplotlib only for initial diagnostics.

**Spec:** `docs/superpowers/specs/2026-09-17-world-zero-model-design.md`

## Global Constraints

- No exact-collapse-date claims.
- Sector code never fetches live network data.
- Every dataset, parameter set, scenario and serious run is version/digest bound.
- Variables must declare endogenous/exogenous/intervention-controlled status per scenario.
- Regional dynamics are retained where implemented; global aggregation occurs after dynamics.
- Physical quantities use explicit units and invariant checks.
- Holdout partitions are frozen before late-stage tuning.
- PyWorld3 is a behavioral/reference subject under CeCILL-2.1; do not copy it blindly into World Zero.
- No merge/deployment/public qualification follows automatically from implementation success.

---

### Task 1: Package skeleton, quality gates and typed core IDs

**Files:**
- Create: `pyproject.toml`
- Create: `src/worldzero/__init__.py`
- Create: `src/worldzero/core/interfaces.py`
- Create: `src/worldzero/core/units.py`
- Create: `tests/core/test_interfaces.py`
- Create: `.github/workflows/test.yml`

**Interfaces:**
- Produces: `StockId`, `FlowId`, `SectorId`, `RegionId`, `Quantity` alias/wrapper, `Sector` protocol.

- [ ] **Step 1: Write failing core-interface tests**

```python
from worldzero.core.interfaces import StockId, SectorId


def test_ids_are_nonempty_strings():
    assert str(StockId("population")) == "population"
    assert str(SectorId("demography")) == "demography"
```

- [ ] **Step 2: Run the test before implementation**

Run: `python -m pytest tests/core/test_interfaces.py -v`
Expected: FAIL because package/interfaces do not exist.

- [ ] **Step 3: Add minimal package and pinned tooling**

`pyproject.toml` must require Python `>=3.12,<3.13` initially and define pytest/Ruff/mypy commands. Implement IDs as validated immutable string types; do not add simulation behavior yet.

- [ ] **Step 4: Run quality gates**

Run:
```bash
python -m pytest -q
ruff check .
mypy src/worldzero
```
Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml src tests .github/workflows/test.yml
git commit -m "build: scaffold typed World Zero core"
```

---

### Task 2: Stock-flow engine, clock, units and invariants

**Files:**
- Create: `src/worldzero/core/clock.py`
- Create: `src/worldzero/core/stocks.py`
- Create: `src/worldzero/core/solver.py`
- Create: `src/worldzero/core/invariants.py`
- Create: `tests/core/test_stock_flow_engine.py`
- Create: `tests/core/test_solver_convergence.py`

**Interfaces:**
- Produces: `SimulationClock`, `StockSpec`, `FlowSpec`, `ModelState`, `InvariantResult`, `EulerSolver`, `solve(...)`.

- [ ] **Step 1: Freeze a one-stock conservation test**

```python
def test_closed_stock_conserves_quantity():
    # A transfers to B; total must remain 100 units.
    result = run_two_stock_transfer(initial_a=100.0, initial_b=0.0, rate=0.1, years=10)
    assert abs(result.a[-1] + result.b[-1] - 100.0) < 1e-9
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/core/test_stock_flow_engine.py -v`
Expected: FAIL because engine is absent.

- [ ] **Step 3: Implement minimal deterministic engine**

Support scalar regional/global stocks, explicit units, derivative evaluation, non-finite rejection and invariant hooks. Implement Euler first only to expose semantics.

- [ ] **Step 4: Add a second solver/convergence subject**

Add SciPy `solve_ivp` adapter or a documented RK method and a smooth reference ODE. Require both solvers to converge toward the analytic solution as timestep/tolerance tightens.

- [ ] **Step 5: Run core suite and commit**

```bash
pytest tests/core -q
ruff check .
mypy src/worldzero
git add src/worldzero/core tests/core
git commit -m "feat: add stock-flow engine and numerical invariants"
```

---

### Task 3: Dataset manifests, observations and immutable provenance

**Files:**
- Create: `src/worldzero/data/manifests.py`
- Create: `src/worldzero/data/observations.py`
- Create: `src/worldzero/data/transforms.py`
- Create: `tests/data/test_manifest.py`
- Create: `tests/data/test_observation_lineage.py`
- Create: `data/README.md`

**Interfaces:**
- Produces: `DatasetManifest`, `ObservationSeries`, `ObservationClass` (`DIRECT`, `DERIVED`, `COMPOSITE`, `SCENARIO_INPUT`), digest verification.

- [ ] **Step 1: Write a manifest rejection test**

```python
def test_manifest_requires_digest_and_vintage():
    with pytest.raises(ValidationError):
        DatasetManifest(dataset_id="wpp-population", provider="UN DESA")
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/data -q`
Expected: FAIL.

- [ ] **Step 3: Implement the exact manifest fields from `DATA_SOURCE_REGISTRY_V0.md`**

Include provider/product/release/retrieval/source/license/geography/time/frequency/units/transformations/missing-data/uncertainty/content SHA-256/transform commit.

- [ ] **Step 4: Prove lineage survives transformation**

Test that a normalized per-capita series retains the raw dataset ID/digest and transformation function/version.

- [ ] **Step 5: Run and commit**

```bash
pytest tests/data -q
git add src/worldzero/data tests/data data/README.md
git commit -m "feat: add immutable data provenance and observations"
```

---

### Task 4: Scenario schema and deterministic run receipts

**Files:**
- Create: `src/worldzero/scenarios/schema.py`
- Create: `src/worldzero/scenarios/loader.py`
- Create: `src/worldzero/receipts/run_receipt.py`
- Create: `tests/scenarios/test_scenario_schema.py`
- Create: `tests/receipts/test_run_receipt.py`

**Interfaces:**
- Produces: `VariableControlMode`, `Scenario`, `RunReceipt`.

- [ ] **Step 1: Write failing exogenous/endogenous ambiguity test**

```python
def test_variable_cannot_be_endogenous_and_exogenous():
    with pytest.raises(ValidationError):
        ScenarioVariable(name="fertility", modes=["ENDOGENOUS", "EXOGENOUS_TRAJECTORY"])
```

- [ ] **Step 2: Verify RED**

Run: `pytest tests/scenarios tests/receipts -q`
Expected: FAIL.

- [ ] **Step 3: Implement scenario control modes**

Use exactly `ENDOGENOUS`, `EXOGENOUS_TRAJECTORY`, `INTERVENTION_CONTROLLED`. Require intervention timing/ramp and model-schema compatibility.

- [ ] **Step 4: Implement deterministic receipt identity**

Receipt fields must include model commit/tree, data-manifest digest, parameter digest, scenario ID, solver, timestep, seed, region set, time range and metric artifact ID.

- [ ] **Step 5: Test deterministic replay receipt and commit**

Two identical deterministic inputs must produce the same receipt payload hash.

```bash
pytest tests/scenarios tests/receipts -q
git add src/worldzero/scenarios src/worldzero/receipts tests/scenarios tests/receipts
git commit -m "feat: bind scenarios and reproducible run receipts"
```

---

### Task 5: World3-compatible control subject

**Files:**
- Create: `src/worldzero/baselines/world3_reference.py`
- Create: `tests/baseline/fixtures/world3_standard_run.csv`
- Create: `tests/baseline/test_world3_reference.py`
- Create: `docs/qualification/WORLD3_BASELINE_V1.md`

**Interfaces:**
- Produces: `run_world3_reference(...) -> BaselineTrajectory` with population, resource fraction, food/capita, industrial output/capita and persistent-pollution index.

- [ ] **Step 1: Generate an external reference artifact deliberately**

Use PyWorld3 in a separate environment/reference script to generate the standard-run comparison artifact. Record PyWorld3 version/commit, parameters, timestep and file digest in qualification docs. Do not copy PyWorld3 source into World Zero.

- [ ] **Step 2: Freeze fixture and write RED comparison test**

```python
def test_world3_standard_run_matches_frozen_reference():
    actual = run_world3_reference()
    expected = load_fixture("world3_standard_run.csv")
    assert trajectory_error(actual, expected) < BASELINE_TOLERANCE
```

- [ ] **Step 3: Implement only enough World3-compatible behavior to pass**

Port equations from documented World3 sources or implement a clean-room compatible baseline with source citations. Keep it isolated under `baselines/` so modernization does not silently change it.

- [ ] **Step 4: Add timestep convergence and headline turning-point tests**

Run at `dt=1.0`, `0.5`, `0.25`; document tolerance and convergence behavior.

- [ ] **Step 5: Commit qualification subject**

```bash
pytest tests/baseline -q
git add src/worldzero/baselines tests/baseline docs/qualification/WORLD3_BASELINE_V1.md
git commit -m "feat: freeze World3 compatibility baseline"
```

---

### Task 6: Regional skeleton plus demography, production and distribution

**Files:**
- Create: `src/worldzero/regions/definitions.py`
- Create: `src/worldzero/regions/coupling.py`
- Create: `src/worldzero/sectors/demography.py`
- Create: `src/worldzero/sectors/production.py`
- Create: `src/worldzero/sectors/distribution.py`
- Create: `tests/sectors/test_demography.py`
- Create: `tests/integration/test_regional_aggregation.py`

**Interfaces:**
- Produces: versioned `RegionSet`, age-cohort population flows, productive/service capital, compact distribution state.

- [ ] **Step 1: Freeze region-set manifest and aggregation test**

Create one versioned macroregion set. Test that global population equals the sum of regional population at every timestep.

- [ ] **Step 2: Implement demographic limiting cases**

Tests must cover zero births/deaths, constant fertility/mortality, migration conservation globally, and ageing flow conservation.

- [ ] **Step 3: Add bounded fertility-transition function**

Inputs: education, child survival/health, income/security proxy and desired-family-size parameter. Do not tune to historical observations yet.

- [ ] **Step 4: Add minimal production/distribution coupling**

Labour supply from demography; output/capital from production; labour-share/disposable-income split from distribution. Include invariant that redistribution changes distribution but does not create real output by itself.

- [ ] **Step 5: Run tests and commit**

```bash
pytest tests/sectors/test_demography.py tests/integration/test_regional_aggregation.py -q
git add src/worldzero/regions src/worldzero/sectors tests
git commit -m "feat: add regional demographic and economic skeleton"
```

---

### Task 7: Energy, technology learning and materials/circularity

**Files:**
- Create: `src/worldzero/sectors/energy.py`
- Create: `src/worldzero/sectors/technology.py`
- Create: `src/worldzero/sectors/materials.py`
- Create: `tests/sectors/test_energy_learning.py`
- Create: `tests/sectors/test_material_conservation.py`

**Interfaces:**
- Produces: fossil/low-carbon generation capacity, storage/grid enabling state, electrification/useful-energy demand, cumulative deployment learning, material virgin/in-use/recycled stocks.

- [ ] **Step 1: Write learning-curve RED tests**

Test a known learning rate: each doubling of cumulative capacity reduces cost by the configured fraction, until the configured floor/saturation applies.

- [ ] **Step 2: Write material-conservation RED tests**

Virgin extraction + recycled input must equal material entering in-use stock plus documented losses; retirement moves material to recoverable waste/loss streams.

- [ ] **Step 3: Implement energy/material modules minimally**

No optimization solver yet. Capacity additions follow transparent investment/allocation equations so feedbacks remain auditable.

- [ ] **Step 4: Add hostile constraints**

Tests: zero recycling, high recycling with losses, mineral bottleneck, grid bottleneck, no-learning, high-learning with saturation.

- [ ] **Step 5: Commit**

```bash
pytest tests/sectors/test_energy_learning.py tests/sectors/test_material_conservation.py -q
git add src/worldzero/sectors tests/sectors
git commit -m "feat: model energy learning and material circularity"
```

---

### Task 8: Food-land-water-soil and reduced-form climate coupling

**Files:**
- Create: `src/worldzero/sectors/food_land.py`
- Create: `src/worldzero/sectors/water.py`
- Create: `src/worldzero/sectors/climate.py`
- Create: `tests/sectors/test_food_water_energy.py`
- Create: `tests/sectors/test_climate_damage_interfaces.py`

**Interfaces:**
- Produces: agricultural land/soil condition, water stress/withdrawals, food production/access, reduced-form carbon/temperature and explicit damage multipliers.

- [ ] **Step 1: Write no-free-input tests**

Food output increase from irrigation/fertilizer/mechanization must consume the declared water/nutrient/energy inputs. Bioenergy land allocation must reduce land available to other uses unless expansion is explicitly modeled.

- [ ] **Step 2: Implement climate state and emissions interface**

Keep climate model deliberately reduced form and separately testable. Expose temperature/hazard signals; do not embed food/health damage equations inside climate module.

- [ ] **Step 3: Implement food/water/soil dynamics**

Include degradation/recovery delay and diminishing returns to inputs.

- [ ] **Step 4: Add structural alternatives for damage functions**

Provide at least two pluggable damage-function forms so scenario conclusions are not locked to one curve.

- [ ] **Step 5: Commit**

```bash
pytest tests/sectors/test_food_water_energy.py tests/sectors/test_climate_damage_interfaces.py -q
git add src/worldzero/sectors tests/sectors
git commit -m "feat: couple climate food land water and soil"
```

---

### Task 9: Calibration, holdouts, hostile validation and sensitivity

**Files:**
- Create: `src/worldzero/calibration/parameters.py`
- Create: `src/worldzero/calibration/objective.py`
- Create: `src/worldzero/validation/metrics.py`
- Create: `src/worldzero/validation/holdouts.py`
- Create: `src/worldzero/validation/falsification.py`
- Create: `src/worldzero/validation/sensitivity.py`
- Create: `tests/validation/test_holdout_isolation.py`
- Create: `tests/validation/test_falsification_oracles.py`

**Interfaces:**
- Produces: frozen evidence partitions, metric bundle, calibration runner, falsification suite, sensitivity report.

- [ ] **Step 1: Write holdout-contamination test**

Attempt to pass a holdout observation ID into the calibration objective; require a hard failure.

- [ ] **Step 2: Implement multi-metric results**

Return per-variable/region metrics plus turning-point, conservation and uncertainty coverage; do not collapse into one score by default.

- [ ] **Step 3: Implement the F1-F12 hostile fixtures from the validation strategy**

At minimum F1 aggregate-fit trap, F2 correlated-evidence laundering, F3 identifiability, F5 solver/timestep, F6 technology saturation and F11 trade fragmentation must have executable tests before V0 scenario qualification.

- [ ] **Step 4: Add global sensitivity harness**

Start with Morris screening; add Sobol only when compute/runtime is justified. Freeze seeds and parameter bounds.

- [ ] **Step 5: Commit**

```bash
pytest tests/validation -q
git add src/worldzero/calibration src/worldzero/validation tests/validation
git commit -m "feat: add frozen holdouts falsification and sensitivity"
```

---

### Task 10: Institutions, trade coupling and V0 integrated qualification

**Files:**
- Create: `src/worldzero/sectors/institutions.py`
- Create: `src/worldzero/sectors/trade.py`
- Create: `tests/integration/test_world_zero_v0.py`
- Create: `tests/integration/test_trade_conservation.py`
- Create: `docs/qualification/WORLD_ZERO_V0_QUALIFICATION.md`
- Create: `scenarios/world3_compatibility.yaml`
- Create: `scenarios/2026_baseline.yaml`

**Interfaces:**
- Produces: response-capacity/policy-delay state, conservative physical trade coupling, integrated V0 scenario runner and qualification report.

- [ ] **Step 1: Write trade-conservation and policy-delay tests**

Trade may redistribute food/energy/materials but cannot create them. A policy intervention with a configured delay must not affect state before the delay expires.

- [ ] **Step 2: Integrate active V0 modules**

Use dependency injection/module registry; avoid sector-to-sector imports that create circular ownership.

- [ ] **Step 3: Run frozen historical/holdout suites**

Record exact model/data/parameter/scenario receipts. A failure remains a failure; do not retune holdouts during this task.

- [ ] **Step 4: Run uncertainty/sensitivity and ablations**

Report dominant uncertainty sources and compare V0 against the World3 control subject. Identify extensions that add complexity without measurable qualification value.

- [ ] **Step 5: Write exact qualification report**

The report must list PASS/FAIL/UNKNOWN per qualification ladder state and exact subject commit. It must explicitly state that scenario readiness is not future predictive validation.

- [ ] **Step 6: Final verification and commit**

```bash
pytest -q
ruff check .
mypy src/worldzero
git diff --check
git add src tests scenarios docs/qualification
git commit -m "feat: qualify integrated World Zero V0 scenario system"
```

---

## Plan self-review

- Spec coverage: baseline, modular core, regions, data provenance, scenario semantics, active V0 sectors, validation, uncertainty, receipts and qualification are each mapped to tasks.
- Deferred modules remain deferred; no hidden task implements detailed biodiversity, N/P, conflict, full finance or AI-productivity dynamics.
- No task uses a holdout as calibration data.
- Interface names used across tasks are introduced before they are consumed.
- No merge or deployment step is included.

## Execution recommendation

Use subagent-driven development for Tasks 1-10 with a fresh implementer per task and independent review between tasks. Task 5 (World3 baseline) and Task 9 (validation/falsification) should receive especially hostile review because every later scientific claim depends on them.
