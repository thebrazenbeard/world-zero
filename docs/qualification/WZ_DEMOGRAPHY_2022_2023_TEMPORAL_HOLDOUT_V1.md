# World Zero Demography 2022 → 2023 Temporal Holdout V1

Status: **PRE-EXECUTION TEMPORAL VALIDATION SUBJECT / NO RESULT CLAIM**

Date: 2026-09-19

## Purpose

This subject replaces the contaminated idea of treating 2023 cohort values as holdout evidence for a trajectory initialized from those same 2023 cohort values.

The governed split is now strictly temporal:

- 10 macroregion total-population observations from **2022** are `CALIBRATION`;
- 40 macroregion age-cohort observations from **2022** are `INITIALIZATION`;
- 40 macroregion age-cohort observations from **2023** are `TEMPORAL_HOLDOUT`.

The purpose-built evidence catalog intentionally excludes 2023 regional totals. Those totals are same-year aggregates of the 2023 cohort values and would leak information about the temporal holdout if admitted to calibration.

## Materialization evidence

The 2022 cuts were generated only after the existing acquisition layer verified the exact admitted raw WPP 2024 source lengths and SHA-256 digests.

Materialization receipt:

`state/receipts/WZ_DEMOGRAPHY_2022_2023_TEMPORAL_SPLIT_MATERIALIZATION_RECEIPT_V1.json`

Before emitting 2022 outputs, the same materializer rederived the canonical 2023 cuts from the fetched raw bytes and required byte-for-byte equality with the already admitted repository outputs.

Frozen 2022 outputs:

- `data/derived/wpp2024/WZ_MACROREGION_V0_population_2022.csv`
- `data/derived/wpp2024/WZ_MACROREGION_V0_cohort_population_2022.csv`

Their derived manifests bind source lineage, transform commit, output digest, output length, region/cohort semantics, and validation eligibility.

## Evidence-use firewall

The temporal verifier requires:

1. exactly one `TEMPORAL_HOLDOUT` partition;
2. no alternate final-holdout class mixed into the temporal experiment;
3. complete governed catalog assignment;
4. calibration/final-holdout and initialization/final-holdout disjointness;
5. all calibration and initialization evidence to occur strictly before the earliest temporal-holdout year.

For V1, the latest pre-fit year is 2022 and the earliest holdout year is 2023.

## Covariance and interpretation

Every observation in this packet remains in `UN_WPP_2024_POPULATION_FAMILY`. The 2022 totals, 2022 cohorts, and 2023 cohorts are not independent-source confirmations merely because they occupy different rows or years.

The 2022 total-population calibration terms are same-year aggregates of the initialization population. They are pre-holdout and therefore do not leak 2023 values, but they must not be presented as strong independent dynamic calibration evidence.

## Claim ceiling

This packet can establish only a governed, disjoint, pre-execution temporal-validation subject.

It does **not** yet establish:

- `HISTORICAL_CALIBRATION_PASS`;
- `TEMPORAL_HOLDOUT_PASS`;
- predictive validity;
- forecast skill;
- calibrated parameter quality;
- scientific validation;
- a canonical experiment result;
- deployment or runtime effect.

Those claims require an actual 2022-initialized model execution whose declared initialization use is bound to this packet, followed by scoring against the frozen 2023 temporal holdout without refitting on 2023 evidence.
