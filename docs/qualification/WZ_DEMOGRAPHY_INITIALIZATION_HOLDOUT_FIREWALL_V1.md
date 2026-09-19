# World Zero Initialization / Holdout Firewall V1

Status: **SOURCE CANDIDATE / PRE-FIT FIREWALL / NO HOLDOUT RESULT CLAIM**

Date: 2026-09-19

## Integrated evidence-use state

This successor combines the static initialization semantics developed in PR #24 with the runtime declared-ID overlap guard developed in PR #27.

The governed 2023 evidence catalog remains:

`science/evidence/WZ_DEMOGRAPHY_2023_EVIDENCE_V1.yaml`

The original pre-fit partition:

`science/partitions/WZ_DEMOGRAPHY_2023_VARIABLE_HOLDOUT_V1.yaml`

is retained only as historical provenance. Its interpretation of the 40 cohort observations as a `VARIABLE_HOLDOUT` is superseded for governed use by:

`science/partitions/WZ_DEMOGRAPHY_2023_INITIALIZATION_PARTITION_V2.yaml`

V2 assigns:
- the 10 regional total-population observations to `CALIBRATION`;
- all 40 2023 cohort observations to `INITIALIZATION`;
- no 2023 cohort observation to a final holdout.

## Static evidence-use rule

The partition contract types initialization separately from calibration and final holdout. Population-evidence verification requires every governed catalog observation to be assigned and rejects initialization/final-holdout overlap.

This records the scientific fact that the 2023 cohort values used as `NativeBackboneConfig.initial_population` are initialization evidence, not untouched validation evidence.

## Runtime declared-ID rule

The holdout selector also requires the caller to provide the exact governed observation IDs it declares were consumed while constructing the initial state. Selection fails when any declared initialization ID overlaps the requested holdout IDs.

The declaration must be an exact tuple of unique, non-empty built-in strings.

An empty tuple is only a caller assertion that no governed observation IDs were consumed. It is **not** independent evidence that initialization provenance is complete, and the selector cannot prove that a caller did not omit or relabel consumed evidence.

## Scientific consequence

The static V2 partition closes the known 2023 cohort misclassification. The runtime selector closes the direct declared-ID overlap bypass.

Neither mechanism creates a usable 2023 cohort holdout. A real cohort validation experiment still needs a separately governed disjoint initialization subject, such as a pre-2023 initialization cut followed by a 2023 prediction, or a later cohort year evaluated after an independently initialized trajectory.

## Claim ceiling

This subject may establish only:
- exact governed 2023 evidence loading;
- explicit `CALIBRATION` versus `INITIALIZATION` typing;
- validation-eligibility checks;
- exact holdout identity binding;
- declared initialization-ID validation;
- static and runtime overlap rejection.

It does **not** establish complete initialization provenance, `HISTORICAL_CALIBRATION_PASS`, `VARIABLE_HOLDOUT_PASS`, predictive validity, forecast skill, calibrated parameter quality, scientific validation, canonical experiment results, deployment, or runtime effect.
