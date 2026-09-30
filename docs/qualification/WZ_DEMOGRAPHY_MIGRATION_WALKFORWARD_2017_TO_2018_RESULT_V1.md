# World Zero Demography Migration Walk-Forward Result V1

Status: **EXECUTED / CROSS-PLATFORM REPRODUCED / BETTER_WITH_MIGRATION / HISTORICAL_WALKFORWARD_COMPARISON_ONLY**

Date: 2026-09-19

## Frozen-before-execution design

The experiment contract was frozen before this lane extracted or inspected the 2018 target:

`science/scoring/WZ_DEMOGRAPHY_MIGRATION_WALKFORWARD_2017_TO_2018_V1.yaml`

Freeze commit:

`5ceaa1426d168a8b1d3fca3ed12428d524e5e030`

The contract fixed:

- fitting years: 2016-2017;
- initialization year: 2017;
- target year: 2018;
- the no-migration baseline lineage;
- the migration candidate lineage;
- first-evaluation-only holdout use;
- strict improvement requirements for MAE, RMSE, MAPE, and older-adult MAPE;
- absolute global error may not worsen;
- claim ceiling: `HISTORICAL_WALKFORWARD_COMPARISON_ONLY`.

## Causal difference

Both arms use the same:

- admitted WPP 2024 source bytes;
- 2016-2017 birth-rate derivation;
- cohort-boundary ageing derivation;
- global age-shaped mortality derivation;
- regional crude-death scaling;
- 2017 initial population;
- native RK4 backbone and timestep 0.25.

The candidate differs only by explicit interregional migration.

Regional average net migration is derived from 2016-2017 WPP CNMR. Negative-net regions supply a deterministic conservative flow matrix to positive-net regions. The balanced flow is **4,628,323.741048 persons/year** across **24 links**. Raw aggregate inflow and outflow differ by only about 179 persons/year; the conservative matrix uses the smaller total and therefore creates no population from migration.

## First clean execution

Exact source commit:

`63a8cc50fbcffb677b3060a544fd7c6e93a5160d`

Exact source tree:

`d62c958ccf4d606ddabf1db76ed7d68d44f36830`

Baseline parameter SHA-256:

`015ac15262dfa5315c586922ca392c3905f1905dea68eefc71ab6eadde64cb44`

Migration-candidate parameter SHA-256:

`938c395fe1986cc9b3bf967d63c42ec6db9e525007ab5af50aa1486e5c23125f`

The 2018 holdout was extracted only after both arms had already executed.

## Measurement

Across the same 40 region/cohort observations:

| Metric | No migration | With migration | Change |
| --- | ---: | ---: | ---: |
| MAE | 806,689.400 | **620,416.459** | **23.09% lower** |
| RMSE | 1,084,341.239 | **896,770.081** | **17.30% lower** |
| MAPE | 0.707138% | **0.546169%** | **22.76% lower** |
| Older-adult MAPE | 1.588530% | **1.478027%** | **6.96% lower** |
| Absolute global error | 1,588,302.506 | **1,568,497.440** | **1.25% lower** |

Per-cohort MAPE moved:

- child: 0.360520% → **0.169342%**
- young adult: 0.444695% → **0.213139%**
- mature adult: 0.434809% → **0.324169%**
- older adult: 1.588530% → **1.478027%**

Every predeclared gate passed.

Formal result:

**BETTER_WITH_MIGRATION**

Baseline terminal-state digest:

`9026e009beae127ec4c6e9cf746ef61d91524092eec91da56f848df336e557d8`

Migration terminal-state digest:

`fd13c31f1cd88476a189e52991b1bb2872ccbc75e041560a30c011e282ff673c`

## Cross-platform reproduction

GitHub Actions run:

`35467162073`

Linux job:

`105961511238`

Windows job:

`105961511115`

Both independently fetched and verified the admitted WPP source bytes and executed the frozen experiment.

Linux artifact ID: `10591208271`  
Linux artifact ZIP SHA-256: `61c2208b558ce3128032d67c8ef46690329a77269904f8c38ecf720a99edb711`

Windows artifact ID: `10591123400`  
Windows artifact ZIP SHA-256: `5d86dd5c74a587dada22a632d85b931d9ad1703dbf5d09bdd06bff5f15e40f37`

ZIP container digests differ, but every scientific payload file is byte-identical across Linux and Windows:

- baseline terminal: `75671c9ba552d7d696e918c3a4049c79d2cd759e17d3bbfe8b8538aa20e98638`
- migration terminal: `cd3f88af94453c07943e48615592645ce22d3196cbb3e097a17acb2902f52a5e`
- comparison report: `9344e9998fce7e6cde70282e7c67eaa7c7b0ae59cb385a957ce28bac5171012f`
- derivation receipt: `40a4336e6e15ad8800e861aac0e6ed97bf4ed1e37e85fe987257ea870ed3f4cd`
- execution receipt: `1191daecf9d1c2dc43e6ffb6a30d6ad7553daeccd6427848ef75fdb015fc2c4e`

## Verification

On the clean execution head:

- pytest: **340 passed**
- Ruff: **PASS**
- mypy: **PASS**
- offline Linux qualification: **PASS**
- offline Windows qualification: **PASS**
- scientific Linux execution: **PASS**
- scientific Windows execution: **PASS**
- admitted WPP source digest verification: **PASS**
- Linux/Windows scientific payload identity: **PASS**

## What we learned

Explicit migration is not decorative complexity here. On a target year that was frozen before inspection, adding conservative regional migration improved every required aggregate metric and every cohort-level MAPE.

The gain is largest for child and young-adult cohorts. Older-adult error also improves, but only modestly and remains the largest cohort residual by a wide margin. That narrows the next scientific question: migration belongs in the model, while older-adult dynamics still need an additional mechanism or better age-specific mortality representation.

## Claim ceiling

This result supports only a bounded historical walk-forward comparison on 2017→2018.

It does **not** establish:

- general predictive validity;
- future forecast skill;
- structural identification of migration or mortality;
- `HISTORICAL_CALIBRATION_PASS`;
- `TEMPORAL_HOLDOUT_PASS` for the spent 2023 benchmark;
- scientific validation of World Zero as a whole;
- deployment or production effect.

The next model should preserve this migration result and test the older-adult residual on another predeclared historical target rather than tune against 2018 or 2023.
