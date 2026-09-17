# World Zero Validation and Falsification Strategy

Date: 2026-09-17
Status: proposed qualification framework

World Zero should be difficult to impress. A visually plausible curve is not validation.

## 1. Claim-scoped qualification

Never state `WORLD_ZERO_VALIDATED` without a qualifier. A defensible result is of the form:

`<exact model commit> reproduces <specified variables> over <specified regions/years> against <dataset manifest> within <declared metrics/tolerances>.`

Source correctness, numerical correctness, historical fit, structural plausibility, scenario usefulness and future predictive skill are separate claims.

## 2. Frozen evidence partitions

Before serious calibration, partition evidence into:

1. **Calibration set** — data permitted to estimate parameters.
2. **Temporal holdout** — later/earlier time windows not used in parameter fitting.
3. **Regional holdout** — selected regions withheld from some calibration stages.
4. **Variable holdout** — observed variables not directly optimized.
5. **Structural/adversarial set** — synthetic and historical cases designed to expose wrong mechanisms.
6. **Shock set** — events/regimes outside smooth trend behavior.

Do not move failed holdouts into calibration and continue calling them holdouts.

## 3. World3 control subject

Phase 0 creates a World3-compatible control subject. Store exact reference trajectories for headline variables and sector-level invariants.

Purpose:

- prove the simulator can reproduce a known system-dynamics model;
- establish numerical regression tests;
- measure whether extensions actually improve explanatory/holdout behavior;
- retain the original overshoot mechanism as a comparand rather than rewriting history.

## 4. Metrics — never one magic score

Report metrics by variable/region plus summaries. Candidate metrics:

- normalized RMSE / MAE for trajectory levels;
- growth-rate/direction error;
- turning-point timing error;
- rank/order agreement across regions;
- stock-flow conservation residuals;
- calibration residual autocorrelation;
- uncertainty-interval coverage;
- shock recovery shape/timing;
- scenario discrimination (do materially different assumptions produce distinguishable outcomes?);
- qualitative behavior class where relevant (monotonic growth, S-curve, overshoot/decline, oscillation, stabilization).

A model may pass level fit while failing turning points or conservation; that should remain visible.

## 5. Structural falsification tests

### F1 — Aggregate-fit trap

Construct/identify two regional trajectories that offset to the same global aggregate. A model fitting only the aggregate must not receive regional qualification.

### F2 — Correlated-indicator laundering

Remove or cluster correlated evidence families (GDP/energy/materials/emissions). Qualification should not collapse merely because five correlated metrics were counted as five independent confirmations.

### F3 — Parameter swap / identifiability

Search for distinct parameter sets that produce near-identical observed trajectories. If many exist, report the parameter/structure as non-identifiable rather than presenting one calibrated value as truth.

### F4 — Delay perturbation

Vary major information/physical delays within plausible ranges. Overshoot conclusions that depend on a narrow unverified delay need explicit sensitivity warnings.

### F5 — Timestep/solver dependence

Run with multiple timesteps and at least two compatible numerical methods. Behavior class and key metrics should converge within declared tolerance.

### F6 — Technology learning saturation

Stress learning rates, deployment limits, grid integration and material constraints. Prevent endless exponential cost reduction from becoming an accidental infinite-resource mechanism.

### F7 — Resource substitution extremes

Test zero substitution, plausible substitution and unrealistically frictionless substitution. The model should make the consequence of each assumption legible rather than bury it.

### F8 — Climate damage nonlinearity

Stress alternative damage/impact functions and threshold behavior. Avoid letting one chosen damage curve predetermine collapse/stability.

### F9 — Demographic transition

Test whether education/health/fertility feedback reproduces observed regional transitions without directly forcing fertility to its observed path.

### F10 — Distribution feedback ablation

Hold aggregate output constant while varying distribution. If modeled consumption, health, fertility or policy response are claimed to depend on inequality, ablation should demonstrate that pathway.

### F11 — Trade fragmentation

Shock regional food/energy/mineral trade links. Check whether physical shortages, prices and substitution propagate consistently without creating/losing matter.

### F12 — Policy delay and reversal

Introduce delayed policy response, implementation friction and reversal. The system should not assume instantaneous perfect optimization after a threshold is crossed.

## 6. Historical shock suite

Candidate events for bounded replay tests:

- 1973/1979 oil shocks;
- post-1990 regional economic transitions;
- 2007-2008 food/energy/financial shock period;
- 2008-2009 global financial crisis;
- 2010s renewable-cost acceleration;
- COVID-19 pandemic shock and rebound;
- 2021-2023 energy/commodity/supply-chain disruptions;
- major drought/heat/crop-failure years;
- rapid EV/solar/storage deployment periods.

The purpose is not to fit every event perfectly. It is to test whether module interfaces and feedback directions behave sensibly under known stress.

## 7. Uncertainty decomposition

Report at least three uncertainty classes separately:

1. **Parameter uncertainty** — uncertain numerical values inside a chosen structure.
2. **Structural uncertainty** — alternative plausible equations/module choices.
3. **Scenario uncertainty** — future policy, technology, conflict and social choices not inferable from physics alone.

Monte Carlo over parameters does not cover structural or scenario uncertainty.

## 8. Sensitivity

Use local sensitivity for debugging and global sensitivity for substantive claims. Candidate methods include Morris screening and Sobol/variance-based analysis once computational cost allows.

Every headline result should identify which parameters/modules dominate variance and whether that dominance is stable across scenarios.

## 9. Reproducible run receipt

Every serious run should emit a machine-readable receipt similar to:

```json
{
  "schema_id": "WORLD_ZERO_RUN_RECEIPT_V1",
  "model_commit": "<git sha>",
  "model_tree": "<git tree sha>",
  "data_manifest_digest": "<sha256>",
  "parameter_set_digest": "<sha256>",
  "scenario_id": "<id>",
  "solver": "<solver/version>",
  "timestep": 0.25,
  "random_seed": 12345,
  "region_set": "<versioned set>",
  "start_year": 1900,
  "end_year": 2100,
  "metrics_artifact": "<path/digest>"
}
```

## 10. Qualification ladder

Use narrow states:

- `SOURCE_REPRODUCIBLE`
- `NUMERICAL_BASELINE_PASS`
- `HISTORICAL_CALIBRATION_PASS`
- `TEMPORAL_HOLDOUT_PASS`
- `REGIONAL_HOLDOUT_PASS`
- `VARIABLE_HOLDOUT_PASS`
- `STRUCTURAL_FALSIFICATION_PASS`
- `UNCERTAINTY_CHARACTERIZED`
- `SCENARIO_EXPERIMENT_READY`

No state implies the next.

## 11. Stop conditions

Pause model expansion if:

- calibration requires implausible parameter values;
- a new module improves its target but materially degrades unrelated holdouts;
- solver/timestep changes alter qualitative conclusions;
- results are dominated by an unmeasured latent parameter;
- the model becomes too complex to identify from available data;
- a claimed mechanism cannot be distinguished from a simpler alternative.

World Zero should prefer a smaller model with exposed uncertainty over an enormous model that can fit anything.
