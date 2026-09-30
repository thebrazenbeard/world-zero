# World Zero Pre-2023 Demography Dynamics Result V1

Status: **EXECUTED / BETTER_THAN_PERSISTENCE / COMPARISON_ONLY**

Date: 2026-09-19

## What was built

The first named nonzero-demography successor from the frozen comparison contract was implemented and executed as:

- candidate lineage: `WZ_DEMOGRAPHY_PRE2023_DYNAMICS_CANDIDATE_V1`
- scenario: `WORLD_ZERO_2022_TO_2023_PRE2023_DYNAMICS_V1`
- parameter set: `WORLD_ZERO_2022_PRE2023_DYNAMICS_V1`
- score contract: `WZ_DEMOGRAPHY_2022_TO_2023_PRE2023_DYNAMICS_SCORE_CONTRACT_V1`

The fitting path uses only admitted WPP 2024 official-estimate evidence dated 2021-2022.

Regional birth rates are derived from WPP crude-birth-rate population-weighted flows. Regional ageing rates are derived from the population occupying the 10-14, 35-39, and 60-64 boundary groups. A global age-specific mortality shape is inferred from the 2021→2022 broad-cohort continuity equations and then scaled to each macroregion's observed crude death level.

The 2023 cohort holdout is not an input to that derivation. Migration remains zero in this V1 candidate.

Exact derivation receipt:

`state/receipts/WZ_DEMOGRAPHY_PRE2023_DYNAMICS_DERIVATION_V1.json`

Derived parameter-set SHA-256:

`58a10a770b0f5c58ab6ccdcc6170238f83b5499db2b90d55aa06f3f7a1d01bfe`

## Execution

First candidate execution source:

`7913cf89c81e02b58c8e3c364371d5d18899f9a8`

Source tree:

`9510dfdebe9026ea84d18b2c0d835edead38bd62`

GitHub Actions run:

`35464356165`

Linux job:

`105953782375`

The job fetched both admitted WPP source files and verified their exact governed lengths and SHA-256 digests before fitting.

The runtime executed from the strong fresh-local-clone path. Exact runtime result SHA-256:

`f6392ae3d03391df3f64a26f78fa61d5a03d51a076f625a5f735185e933ad05f`

Execution receipt:

`state/receipts/WZ_DEMOGRAPHY_PRE2023_DYNAMICS_EXECUTION_V1.json`

## Measurement

The frozen persistence benchmark was:

- MAE: **2,897,964.775 persons**
- RMSE: **4,408,722.530433552 persons**
- MAPE: **1.690737673995113%**
- absolute global error: **70,327,737 persons**

The first pre-2023 dynamics candidate produced:

- mean signed error: **-136,311.5893688129 persons per cohort observation**
- MAE: **847,326.9504474154 persons**
- RMSE: **1,205,506.4709992579 persons**
- MAPE: **0.6890218118042497%**
- observed population across the 40 holdout rows: **8,091,735,125 persons**
- predicted population: **8,086,282,661.425247 persons**
- signed global error: **-5,452,463.574752808 persons**
- absolute global error: **5,452,463.574752808 persons**

Under the comparison rules frozen before candidate execution, every required gate improved, so the exact bounded result is:

**BETTER_THAN_PERSISTENCE**

Canonical comparison result:

`state/results/WZ_DEMOGRAPHY_2022_TO_2023_PRE2023_DYNAMICS_COMPARISON_V1.json`

## Verification

On the execution head:

- standard CI: **337 tests passed**
- Ruff: **PASS**
- mypy: **PASS**
- offline Linux qualification: **PASS**
- offline Windows qualification: **PASS**
- admitted WPP demographic source fetch: exact digest **PASS**
- admitted WPP age5 source fetch: exact digest **PASS**
- fit → execute → score → compare workflow: **PASS**

## What we learned

The zero-dynamics persistence baseline was not merely missing global population growth. The large improvement came from representing cohort transfer, births, and strongly age-shaped mortality. The candidate reduced MAPE by about 59.25%, MAE by about 70.76%, RMSE by about 72.66%, and absolute global error by about 92.25% relative to persistence.

The residual error is not uniform. Older-adult cohorts remain the weakest part of the candidate in several regions, especially Western/Northern Europe and the Middle East/North Africa. That is a concrete next modeling target rather than a reason to redesign the governance system.

## Claim ceiling

This is a **bounded benchmark comparison** against a 2023 holdout that has already been observed by this development lane. It is not fresh blind validation.

It does not establish:

- `TEMPORAL_HOLDOUT_PASS`
- `HISTORICAL_CALIBRATION_PASS`
- predictive validity or forecast skill
- structurally identified demographic parameters
- scientific validation of World Zero
- deployment or production effect

The correct next scientific move is to preserve this exact V1 result, stop touching this first candidate, and test any next model on a different predeclared historical split or other genuinely independent evidence rather than tuning V1 against the now-spent 2023 benchmark.
