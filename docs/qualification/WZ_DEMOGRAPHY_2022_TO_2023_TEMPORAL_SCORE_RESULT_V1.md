# World Zero Demography 2022 → 2023 Temporal Score Result V1

Status: **EXECUTED / CROSS-PLATFORM REPRODUCED / SCORE_ONLY / NO PASS THRESHOLD**

Date: 2026-09-19

## Frozen-before-execution subject

The scoring contract was frozen before any holdout execution at commit:

`e21895a4e96daf75c5b93a087cdf1c58e508a603`

Contract:

`science/scoring/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_CONTRACT_V1.yaml`

The contract fixed:
- the 2022 initialization year and 2023 target year;
- the governed 2022→2023 evidence catalog and partition set;
- all 40 2023 cohort observations as the temporal scoring subject;
- terminal state extraction by `population:{region_id}:{cohort_id}`;
- mean error, MAE, RMSE, MAPE, and global error;
- `allow_refit_on_holdout: false`;
- `acceptance_policy: NONE_SCORE_ONLY`;
- `result_claim: SCORE_ONLY`.

No acceptance threshold was introduced after seeing the result.

## Executed subject

Execution source commit:

`5fc814349d55ba676fe8750b2a41cc229b82f1f1`

Execution source tree:

`d771add596bd88abfc11408f77f74259115aeddf`

The strong runtime path executed from a fresh local clone and bound:
- scenario `WORLD_ZERO_2022_TO_2023_TEMPORAL_SCORE_V1`;
- data bundle `WORLD_ZERO_2022_TEMPORAL_VALIDATION_DATA_V1`;
- parameter set `WORLD_ZERO_2022_TEMPORAL_SCORE_PROVISIONAL_V1`;
- the admitted 2022 total and cohort artifacts and source lineage;
- frozen region/cohort semantics;
- RK4 timestep 0.25.

The exact canonical runtime result SHA-256 is:

`e6d81ab8769ab0e3ada5fa209149b3692bc3967e19af2d1ea56ce27e8afb3851`

## Cross-platform reproduction

GitHub Actions workflow run:

`35462414099`

Linux job `105948527945`:
- CPython 3.12.14;
- Linux x86_64;
- execution SUCCESS;
- score artifact uploaded.

Windows job `105948528046`:
- CPython 3.12.10;
- Windows AMD64;
- execution SUCCESS;
- score artifact uploaded.

Both environments produced:
- the same source commit and tree;
- the same runtime result SHA-256;
- byte-equivalent parsed score content;
- the same aggregate and per-observation scores.

Durable receipts:
- `state/receipts/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_LINUX_V1.json`
- `state/receipts/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_WINDOWS_V1.json`
- `state/receipts/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_CROSS_PLATFORM_V1.json`

Canonical score report:
- `state/results/WZ_DEMOGRAPHY_2022_TO_2023_TEMPORAL_SCORE_V1.json`

## Frozen score

Across all 40 governed 2023 cohort observations:

- mean signed error: **-1,758,193.425 persons per cohort observation**
- mean absolute error: **2,897,964.775 persons**
- RMSE: **4,408,722.530433552 persons**
- MAPE: **1.690737673995113%**
- observed population summed across holdout rows: **8,091,735,125 persons**
- predicted population summed across holdout rows: **8,021,407,388 persons**
- aggregate signed error: **-70,327,737 persons**

The signed aggregate indicates underprediction relative to the frozen 2023 cohort evidence.

## Interpretation boundary

The provisional parameter set deliberately copied the existing execution assumptions without fitting to 2023 evidence. Its demographic birth, mortality, ageing, and migration rates are all zero.

Therefore the terminal 2023 cohort population state remains the governed 2022 cohort initialization state. This run is consequently an exact World Zero runtime reproduction of a **one-year persistence baseline** against a genuinely disjoint 2023 temporal holdout.

That is scientifically useful as a benchmark and as proof that the evidence-use and execution plumbing can perform a real out-of-sample score without holdout leakage. It is not evidence that World Zero's demographic dynamics have been calibrated or learned.

## Claim ceiling

The exact supported result is:

**A governed, disjoint 2022→2023 temporal holdout was executed and descriptively scored under a contract frozen before execution; Linux and Windows reproduced the same runtime result and score.**

It does **not** establish:
- `TEMPORAL_HOLDOUT_PASS` because no pass threshold exists;
- `HISTORICAL_CALIBRATION_PASS`;
- predictive validity;
- forecast skill;
- calibrated parameter quality;
- superiority to a declared benchmark;
- scientific validation of World Zero;
- deployment or production runtime effect.

A successor scientific experiment should preserve this score as the frozen persistence benchmark, derive demographic dynamics using pre-2023 evidence only, predeclare a comparison/acceptance policy, and then evaluate the successor against the still-frozen 2023 holdout without tuning on it.
