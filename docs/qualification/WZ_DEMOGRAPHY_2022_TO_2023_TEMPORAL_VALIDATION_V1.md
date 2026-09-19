# World Zero Demography 2022 -> 2023 Temporal Validation V1

Status: **SOURCE MATERIALIZATION REQUIRED / PRE-EXECUTION / NO VALIDATION RESULT**

Date: 2026-09-19

## Objective

Create a genuinely temporal cohort validation subject in which World Zero starts from governed 2022 cohort population evidence and the governed 2023 cohort population cut is reserved for post-initialization comparison.

This removes the contamination that invalidated the earlier 2023-as-both-initialization-and-holdout interpretation.

## Frozen source family

The existing admitted raw source is:

`data/manifests/UN_WPP_2024_POPULATION_AGE5_SEX_MEDIUM_V1.yaml`

Expected raw artifact:
- dataset: `un-wpp-2024-population-age5-sex-medium-v1`
- content length: `29948947` bytes
- SHA-256: `a04d7d1486a5eb2832cc812d599448f0a71e8ac9e1e7e6fa4066673d6a2487cd`
- source observation class for 2022 and 2023: `OFFICIAL_ESTIMATE`
- admitted transform: `WPP2024_AGE5_TO_WZ_MACROREGION_COHORT_V0`

The raw gzip itself remains outside Git. Any official or mirror download is acceptable only if the exact admitted byte length and SHA-256 match. A same-named file without exact-byte verification is not sufficient.

## Required successor artifacts

Before this experiment can become executable, freeze and admit:

1. a 2022 macroregion cohort-population derived artifact using the already-governed region and cohort mappings;
2. a compatible governed 2022 total-population artifact so the normal baseline loader can reconcile the 2022 initial state;
3. a 2022 population evidence catalog containing the complete governed cohort cut;
4. a frozen temporal validation subject that binds the complete 2022 cohort cut as initialization and the complete governed 2023 cohort cut as temporal holdout;
5. a 2022-start scenario/data bundle whose runtime start year equals the 2022 data-bundle year.

The candidate scenario is:

`scenarios/validation/2022_to_2023_demography_temporal_holdout.yaml`

It deliberately remains `DATA_BINDING_REQUIRED`.

## Mechanical firewall

`TemporalPopulationValidationSubject` requires:
- holdout year strictly after initialization year;
- exact initialization and holdout catalog identities;
- matching frozen region/cohort semantics;
- complete cohort cuts for both bound years;
- unique IDs within each side;
- no observation-ID overlap between initialization and holdout.

The existing runtime loader separately requires `scenario.start == data_bundle.year`, preventing a 2022-start executable subject from silently loading a 2023 initial-state bundle.

## Current transport frontier

A public GitHub repository was found containing a file at the expected WPP filename, but the available GitHub connector rejects the gzip payload because it exposes repository file content through a UTF-8 text path. That candidate has therefore **not** been admitted or treated as equivalent.

No 2022 derived values, digest, manifest, evidence catalog, or validation result are claimed in this lane yet.

## Claim ceiling

This lane may currently establish only:
- the exact temporal evidence-use contract;
- the intended 2022 -> 2023 year separation;
- the source-byte acceptance requirement;
- fail-closed catalog/year/completeness/overlap checks;
- a non-executable scenario awaiting exact 2022 data binding.

It does **not** establish:
- a verified 2022 raw-source retrieval;
- an admitted 2022 derived artifact;
- a runnable 2022 baseline;
- `HISTORICAL_CALIBRATION_PASS`;
- `TEMPORAL_HOLDOUT_PASS`;
- predictive validity;
- forecast skill;
- scientific validation;
- deployment or runtime effect.
